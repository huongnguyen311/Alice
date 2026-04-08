import csv
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

BASE_DIR = Path(__file__).parent
SCRIPTS_DIR = BASE_DIR / "auto-scripts"
DATA_DIR = BASE_DIR / "data"
MEMORY_DIR = BASE_DIR / "memory"
LOGS_CSV = DATA_DIR / "logs.csv"

app = FastAPI(title="Alice", description="Local AI assistant automation server")
scheduler = BackgroundScheduler()
scheduler.start()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.now().isoformat()}


# ---------------------------------------------------------------------------
# Library — list available scripts
# ---------------------------------------------------------------------------

@app.get("/library")
def library():
    scripts = [f.stem for f in SCRIPTS_DIR.glob("*.py")] if SCRIPTS_DIR.exists() else []
    return {"scripts": sorted(scripts)}


# ---------------------------------------------------------------------------
# Run — execute a script by name
# ---------------------------------------------------------------------------

@app.post("/run/{script_name}")
def run_script(script_name: str):
    script_path = SCRIPTS_DIR / f"{script_name}.py"
    if not script_path.exists():
        raise HTTPException(status_code=404, detail=f"Script '{script_name}' not found in auto-scripts/")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
    )

    status = "success" if result.returncode == 0 else "error"
    summary = (result.stdout or result.stderr or "").strip().splitlines()[-1] if (result.stdout or result.stderr) else ""
    _append_log(script_name, status, summary)

    return {
        "script": script_name,
        "status": status,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


# ---------------------------------------------------------------------------
# Schedule — add a recurring job
# ---------------------------------------------------------------------------

class ScheduleRequest(BaseModel):
    script: str
    cron: str  # e.g. "0 9 * * 1"


@app.post("/schedule")
def schedule_script(req: ScheduleRequest):
    script_path = SCRIPTS_DIR / f"{req.script}.py"
    if not script_path.exists():
        raise HTTPException(status_code=404, detail=f"Script '{req.script}' not found in auto-scripts/")

    parts = req.cron.split()
    if len(parts) != 5:
        raise HTTPException(status_code=400, detail="Cron must have 5 fields: minute hour day month day_of_week")

    minute, hour, day, month, day_of_week = parts

    scheduler.add_job(
        func=lambda: subprocess.run([sys.executable, str(script_path)]),
        trigger="cron",
        minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week,
        id=req.script,
        replace_existing=True,
    )

    return {"scheduled": req.script, "cron": req.cron}


# ---------------------------------------------------------------------------
# Memory — read and write Markdown memory files
# ---------------------------------------------------------------------------

@app.get("/memory")
def list_memory():
    files = [f.name for f in MEMORY_DIR.glob("*.md")] if MEMORY_DIR.exists() else []
    return {"files": sorted(files)}


@app.get("/memory/{filename}")
def read_memory(filename: str):
    path = MEMORY_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Memory file '{filename}' not found")
    return {"filename": filename, "content": path.read_text(encoding="utf-8")}


class MemoryWriteRequest(BaseModel):
    filename: str
    content: str


@app.post("/memory")
def write_memory(req: MemoryWriteRequest):
    MEMORY_DIR.mkdir(exist_ok=True)
    path = MEMORY_DIR / req.filename
    path.write_text(req.content, encoding="utf-8")
    return {"written": req.filename}


# ---------------------------------------------------------------------------
# Data — read a CSV file
# ---------------------------------------------------------------------------

@app.get("/data/{filename}")
def read_data(filename: str):
    path = DATA_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Data file '{filename}' not found")
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {"filename": filename, "rows": rows}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _append_log(script: str, status: str, summary: str):
    DATA_DIR.mkdir(exist_ok=True)
    file_exists = LOGS_CSV.exists()
    with open(LOGS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "script", "status", "summary"])
        writer.writerow([datetime.now().isoformat(), script, status, summary])
