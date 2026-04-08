---
name: read-csv
description: Read, filter, and summarise data from a CSV file. Use when the user asks to look at data, get a summary, find specific records, or analyse a spreadsheet.
scope: data
triggers:
  - "analyse"
  - "csv"
  - "log"
  - "data file"
  - "show me the data"
  - "summarise the data"
  - "filter"
  - "find records"
  - "spreadsheet"
  - "report on"
---

# Skill: Read CSV

## When to Use
- User asks to "look at", "check", "summarise", or "analyse" a file
- User wants to find specific rows or filter data
- User asks for counts, totals, or averages from a dataset

## How to Read a CSV

### Option 1 — Quick read (small files)
Read the file directly and summarise in plain English. No script needed.

### Option 2 — Write a script (large files or reusable logic)
Use the `build-script` skill to create a script that processes the CSV and writes output to `/data/output.csv`.

## Summary Format

When summarising CSV data, always include:
- **Row count** — how many records
- **Columns** — what fields are present
- **Key findings** — the most useful insight from the data
- **Anomalies** — anything that looks wrong or missing

Keep the summary concise. Use bullet points unless the user has asked for a different format (check `memories/user_profile.md`).

## Example Response

> **contacts.csv** — 142 rows
> - Fields: name, email, company, last_contacted
> - 18 records have no email address
> - Most recent contact: 2026-03-20 | Oldest: 2024-11-03
> - 34 contacts from "Acme Corp"

## Filtering

If the user wants to filter:
- Ask which column and what value if not specified
- Show matching rows in a simple table
- Offer to save the filtered result to `/data/filtered_output.csv`
