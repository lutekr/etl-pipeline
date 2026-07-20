# ETL Pipeline — Arizona Property Offers

## DESCRIPTION

A simple ETL pipeline in pure Python using SQLite.
It reads a csv file of Arizona property offers, validates
and cleans the rows and converts each field to the right type,
and loads clean data into a SQLite database. The program logs what it does and skips bad rows instead of crashing.

Out of about 9,950 data rows in the source file, roughly 7,400 pass the checks and are loaded; the rest are skipped and counted (empty fields, or values that do not match the expected type).

## What it does

- **Extract** — reads the CSV row by row as a stream (a generator), so the whole file is never held in memory at once. It opens the file with `utf-8-sig` to remove the BOM that Excel on Windows adds to the first column name. Rows with empty or missing fields are skipped, logged, and counted.
- **Transform** — casts each field to its proper type (integers and floats). If a value cannot be converted — for example text in a numeric column — that row is skipped, logged, and counted. A single bad row never stops the pipeline.
- **Load** — inserts the clean rows into an `offers` table in SQLite. The table uses `STRICT` mode, so column types are enforced by the database. Inserts run inside one transaction using context managers, so the connection is always closed and the write is committed only if everything succeeds — otherwise it rolls back.

## Why version 2 (rebuilt from scratch)

This is the second version of the project, rewritten from a blank file. The first version seemed to work, but it had bugs I only really understood after it broke:

- **It was losing about two thirds of the data.** The loader called the cleaning function three times per loop iteration, and each call pulled a fresh row from the same generator — so two out of every three cleaned rows were consumed and thrown away. In v2 the stream is built once and consumed once.
- **The "generator" was not actually a generator.** It used `return` instead of `yield`, so it returned only the first row per call. v2 uses a real generator.
- **Errors were handled in the wrong place.** v2 separates the two kinds of errors: a structural problem (missing file, bad connection) is raised and stops the run, while a bad data row is skipped, logged, and counted.

Rebuilding it from scratch, instead of patching the old code, was the whole point — it forced me to understand every line instead of guessing.

## Technologies

- **Python 3.11** (it uses parenthesized context managers, which need 3.10+, and `STRICT` tables, which need a recent SQLite)
- **SQLite** (through the standard-library `sqlite3` module)
- **No external dependencies — standard library only** (`csv`, `sqlite3`, `logging`, `pathlib`, `contextlib`, `typing`)

## Project structure

```
project/
├── etl_v2.py          # the whole pipeline: extract, transform, load, main
├── arizona_data.csv   # source data
└── events.log         # created on each run: log of skipped/loaded rows and errors
```

## How to run

```bash
python etl_v2.py
```

This creates `offers.db`, runs the pipeline, and writes `events.log`. To start from a clean state, delete `offers.db` first (or call `delete_files()`), because re-running the pipeline appends rows to the existing table.

## Note

Run it with `python -X dev etl_v2.py` to get warnings if any database connection or file is accidentally left open.
