---
name: alice-google-sheet
description: Read, write, append, update, delete, search, or manage Google Sheets data via Alice
scope: data
triggers:
  - "google sheet"
  - "google sheets"
  - "spreadsheet"
  - "sheet"
  - "đọc sheet"
  - "ghi sheet"
  - "cập nhật sheet"
  - "thêm vào sheet"
  - "xóa sheet"
  - "xóa dòng"
  - "tìm trong sheet"
  - "tìm dòng"
  - "đọc google sheet"
  - "ghi vào google sheet"
  - "tạo sheet mới"
  - "thêm sheet"
  - "xóa sheet tab"
  - "mở sheet"
  - "open sheet"
  - "mở google sheet"
---

# Google Sheets CRUD Skill

Thao tác đầy đủ CRUD với Google Sheets qua Python script, dùng credentials của Alice.

## Credentials

| Item | Path |
|---|---|
| Token | `{ALICE_ROOT}/credentials/google_token.json` |
| Scopes | `gmail.modify` + `calendar` + `spreadsheets` + `drive.readonly` |

Nếu token chưa có hoặc hết hạn → chạy: `{ALICE_ROOT}/.venv/bin/python {ALICE_ROOT}/setup/google_auth_setup.py`

---

## Routing — Hỏi trước khi thực thi

Với mọi thao tác CRUD, **luôn hỏi user chọn mode** trước khi chạy:

> **"Bạn muốn thao tác qua terminal (xem/sửa dữ liệu trực tiếp) hay mở trên Google Sheets (trình duyệt)?"**

| Option | Khi nào dùng | Hành động |
|---|---|---|
| **1 — Terminal (CLI)** | Đọc dữ liệu, sửa, xóa, tìm kiếm, batch | Chạy Python script, in kết quả ra terminal |
| **2 — Google Sheets (browser)** | Xem visual, chỉnh tay, chia sẻ | Mở URL trên trình duyệt bằng `subprocess.run(["open", url])` |

> Ngoại lệ: nếu user đã rõ ràng ("mở trên Google", "in ra terminal") → không cần hỏi lại.

---

## Boilerplate — init cho CLI

```python
import warnings
warnings.filterwarnings("ignore")

from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

ALICE_ROOT = Path("{ALICE_ROOT}")
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

creds = Credentials.from_authorized_user_file(
    str(ALICE_ROOT / "credentials/google_token.json"), SCOPES
)
service = build("sheets", "v4", credentials=creds)
sheet = service.spreadsheets()
```

---

## LIST — Liệt kê tất cả spreadsheets

Khi user hỏi "list sheet", "danh sách sheet", "các sheet của tôi":

```python
import warnings
warnings.filterwarnings("ignore")

from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

ALICE_ROOT = Path("{ALICE_ROOT}")
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

creds = Credentials.from_authorized_user_file(
    str(ALICE_ROOT / "credentials/google_token.json"), SCOPES
)
drive = build("drive", "v3", credentials=creds)

results = drive.files().list(
    q="mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
    fields="files(id, name, modifiedTime)",
    orderBy="modifiedTime desc",
    pageSize=50
).execute()

files = results.get("files", [])
print(f"Google Sheets của bạn ({len(files)} files):\n")
print(f"{'#':<4} {'Tên':<35} {'Cập nhật':<12} {'ID'}")
print("-" * 85)
for i, f in enumerate(files, 1):
    print(f"{i:<4} {f['name']:<35} {f['modifiedTime'][:10]:<12} {f['id']}")
```

**Format output chuẩn:**
```
Google Sheets của bạn (5 files):

#    Tên                                 Cập nhật     ID
-------------------------------------------------------------------------------------
1    permission-report                   2026-04-15   1sRYpkvx...
2    Soundwise - Bug Report              2026-04-10   1bnf_ESQ...
```

> Sau khi list xong, nếu user muốn thao tác tiếp → hỏi số thứ tự của sheet.

---

## READ

### Option 1 — CLI: In dữ liệu ra terminal

**Đọc một vùng cụ thể:**
```python
result = sheet.values().get(
    spreadsheetId=SPREADSHEET_ID,
    range="Sheet1!A1:Z100"
).execute()
rows = result.get("values", [])
for row in rows:
    print(row)
```

**Đọc toàn bộ sheet (table format):**
```python
result = sheet.values().get(
    spreadsheetId=SPREADSHEET_ID, range="Sheet1"
).execute()
rows = result.get("values", [])
if rows:
    headers = rows[0]
    col_w = [max(len(str(r[i])) if i < len(r) else 0 for r in rows) for i in range(len(headers))]
    fmt = "  ".join(f"{{:<{w}}}" for w in col_w)
    print(fmt.format(*headers))
    print("-" * (sum(col_w) + 2 * len(col_w)))
    for row in rows[1:]:
        padded = row + [""] * (len(headers) - len(row))
        print(fmt.format(*padded))
```

**Batch read nhiều vùng:**
```python
result = sheet.values().batchGet(
    spreadsheetId=SPREADSHEET_ID,
    ranges=["Sheet1!A1:C10", "Sheet2!A1:B5"]
).execute()
for vr in result.get("valueRanges", []):
    print(vr["range"], vr.get("values", []))
```

### Option 2 — Browser: Mở trên Google Sheets

```python
import subprocess
url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit"
subprocess.run(["open", url])
```

---

## CREATE

### Option 1 — CLI

**Tạo Spreadsheet mới:**
```python
body = {
    "properties": {"title": "Tên spreadsheet"},
    "sheets": [{"properties": {"title": "Sheet1"}}]
}
result = service.spreadsheets().create(body=body).execute()
new_id = result["spreadsheetId"]
print(f"Created: {new_id}")
print(f"URL: https://docs.google.com/spreadsheets/d/{new_id}/edit")
```

**Thêm sheet tab mới:**
```python
body = {"requests": [{"addSheet": {"properties": {"title": "Sheet mới"}}}]}
service.spreadsheets().batchUpdate(
    spreadsheetId=SPREADSHEET_ID, body=body
).execute()
print("Tab created.")
```

**Append dòng mới (thêm vào cuối):**
```python
sheet.values().append(
    spreadsheetId=SPREADSHEET_ID,
    range="Sheet1",
    valueInputOption="USER_ENTERED",
    insertDataOption="INSERT_ROWS",
    body={"values": [["val1", "val2", "val3"]]}
).execute()
print("Row appended.")
```

### Option 2 — Browser: Mở sheet sau khi tạo

```python
import subprocess
subprocess.run(["open", f"https://docs.google.com/spreadsheets/d/{new_id}/edit"])
```

---

## UPDATE

### Option 1 — CLI

**Ghi đè vùng cụ thể:**
```python
sheet.values().update(
    spreadsheetId=SPREADSHEET_ID,
    range="Sheet1!A2",
    valueInputOption="USER_ENTERED",
    body={"values": [["new_val1", "new_val2"]]}
).execute()
print("Updated.")
```

**Batch update nhiều vùng:**
```python
body = {
    "valueInputOption": "USER_ENTERED",
    "data": [
        {"range": "Sheet1!A1", "values": [["Header1", "Header2"]]},
        {"range": "Sheet1!A2", "values": [["row1_val1", "row1_val2"]]},
    ]
}
sheet.values().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
print("Batch updated.")
```

**Tìm dòng theo giá trị rồi update:**
```python
result = sheet.values().get(
    spreadsheetId=SPREADSHEET_ID, range="Sheet1!A:A"
).execute()
rows = result.get("values", [])
for i, row in enumerate(rows):
    if row and row[0] == "target_value":
        row_number = i + 1
        sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"Sheet1!B{row_number}",
            valueInputOption="USER_ENTERED",
            body={"values": [["updated_value"]]}
        ).execute()
        print(f"Updated row {row_number}")
        break
```

**Đổi tên sheet tab:**
```python
meta = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
sheet_id = next(
    s["properties"]["sheetId"]
    for s in meta["sheets"]
    if s["properties"]["title"] == "Sheet1"
)
body = {"requests": [{"updateSheetProperties": {
    "properties": {"sheetId": sheet_id, "title": "Tên mới"},
    "fields": "title"
}}]}
service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
print("Renamed.")
```

### Option 2 — Browser: Mở để sửa tay

```python
import subprocess
subprocess.run(["open", f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit"])
```

---

## DELETE

### Option 1 — CLI

**Xóa nội dung vùng (giữ format):**
```python
sheet.values().clear(
    spreadsheetId=SPREADSHEET_ID,
    range="Sheet1!A2:Z100"
).execute()
print("Cleared.")
```

**Xóa dòng cụ thể (shift dòng bên dưới lên):**
```python
# row_index: 0-indexed (dòng 2 → index 1)
row_index = 1
body = {"requests": [{"deleteDimension": {"range": {
    "sheetId": SHEET_ID,
    "dimension": "ROWS",
    "startIndex": row_index,
    "endIndex": row_index + 1
}}}]}
service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
print(f"Deleted row {row_index + 1}.")
```

**Xóa nhiều dòng liên tiếp:**
```python
body = {"requests": [{"deleteDimension": {"range": {
    "sheetId": SHEET_ID,
    "dimension": "ROWS",
    "startIndex": start_row,  # 0-indexed, inclusive
    "endIndex": end_row       # 0-indexed, exclusive
}}}]}
service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
```

**Xóa sheet tab:**
```python
meta = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
sheet_id = next(
    s["properties"]["sheetId"]
    for s in meta["sheets"]
    if s["properties"]["title"] == "Sheet cần xóa"
)
body = {"requests": [{"deleteSheet": {"sheetId": sheet_id}}]}
service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
print("Sheet tab deleted.")
```

### Option 2 — Browser: Xóa tay trên Google Sheets

```python
import subprocess
subprocess.run(["open", f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit"])
```

---

## SEARCH

### Option 1 — CLI: In kết quả ra terminal

**Tìm dòng theo keyword:**
```python
result = sheet.values().get(
    spreadsheetId=SPREADSHEET_ID, range="Sheet1"
).execute()
rows = result.get("values", [])

keyword = "cần tìm"
matches = [
    (i + 1, row)
    for i, row in enumerate(rows)
    if any(keyword.lower() in str(cell).lower() for cell in row)
]
print(f"Tìm thấy {len(matches)} dòng:\n")
for row_num, row in matches:
    print(f"  Row {row_num}: {row}")
```

**Lấy sheet ID theo tên tab:**
```python
meta = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
sheet_map = {
    s["properties"]["title"]: s["properties"]["sheetId"]
    for s in meta["sheets"]
}
print(sheet_map)
```

### Option 2 — Browser: Dùng Ctrl+F trên Google Sheets

```python
import subprocess
subprocess.run(["open", f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit"])
```

---

## META — Thông tin sheet

**Liệt kê tất cả tabs (table format):**
```python
meta = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
print(f"{'Tab':<30} {'sheetId':<10} {'Rows'}")
print("-" * 55)
for s in meta["sheets"]:
    p = s["properties"]
    print(f"{p['title']:<30} {p['sheetId']:<10} {p['gridProperties']['rowCount']}")
```

**Đếm số dòng có dữ liệu:**
```python
result = sheet.values().get(
    spreadsheetId=SPREADSHEET_ID, range="Sheet1!A:A"
).execute()
count = len(result.get("values", []))
print(f"Rows with data: {count}")
```

---

## Spreadsheet IDs đã biết

| # | Tên | Spreadsheet ID |
|---|---|---|
| 1 | permission-report | `1sRYpkvxomMN7XdTZH5z93Lv2S2wUsA0tNqzyq2qMQy0` |
| 2 | Soundwise - Bug Report | `1bnf_ESQX49KLH50MgIF1xxg48YQ08QQkhd5nk9TVQ1g` |
| 3 | Quản lý Thiết bị & Tài sản | `1aOE1U4gSdYUHMIcvo5pUEbS-Oq_jlPAsHsE3vTtLkeM` |
| 4 | Quản lý Hạ tầng & Chi phí | `10MJYDPFivGaG2a6aNStpJTmbJO0zDQXgs1nnBB71ebc` |
| 5 | Quản lý Nhân sự & Tài khoản | `1ZxKpGywH8oligvl1GnQRuOHGoiAoRo225MxpuRMsj44` |

---

## Lưu ý quan trọng

| Vấn đề | Giải thích |
|---|---|
| `SPREADSHEET_ID` | ID trong URL: `docs.google.com/spreadsheets/d/**ID**/edit` |
| `SHEET_ID` (tab) | Lấy từ `meta["sheets"][n]["properties"]["sheetId"]` — khác `SPREADSHEET_ID` |
| `sheetId` của Sheet1 đầu tiên | Thường là `0` |
| Row index | API dùng 0-indexed cho `deleteDimension`; range dùng 1-indexed (`A1`, `A2`...) |
| `valueInputOption` | `USER_ENTERED`: parse công thức/date. `RAW`: lưu nguyên chuỗi |

## Venv & Dependencies

```bash
{ALICE_ROOT}/.venv/bin/pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```
