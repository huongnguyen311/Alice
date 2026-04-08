---
name: alice-read-csv
description: Read, filter, and summarise a CSV file stored in Alice's data directory. Use when analysing Alice's data or logs.
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

# Skill: Read CSV (Global Wrapper)

This skill delegates to Alice's full implementation.

Read and follow: `{ALICE_ROOT}/skills/read-csv.md`

**Context for delegated skill:**
- Alice root is `{ALICE_ROOT}`
- Default data directory: `{ALICE_ROOT}/data/`
- Treat all relative paths in the delegated skill as relative to `{ALICE_ROOT}`
