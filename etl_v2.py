from typing import Iterator
from pathlib import Path
from contextlib import closing
import csv
import sqlite3
import logging

#python -X dev etl_v2.py to check if all connections were closed properly

#============================ LOGGING CONFIG ===================================#

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
fh = logging.FileHandler('events.log')
fh.setLevel(level=logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(level=logging.WARNING)
logger.addHandler(fh)
#logger.addHandler(ch) # uncomment to show logs in terminal

#============================= INITIAL PATHS ===================================#

path_db = Path('offers.db')
path_file = Path('arizona_data.csv')

#=============================      EXTRACT     ================================#

# instead of holding a whole file in memory, 
# iterator returns row by row preventing resources' overloading

def iter_raw_file(path: Path) -> Iterator[dict]:
    """Read CSV file and yield each valid row as a dict, skipping rows with empty fields."""
    skipped_records = 0
    try:
        # using utf-8-sig, sig -> to eliminate BOM sign at the beginning, in case a file was edited on Windows for example using excel
        with path.open(encoding='utf-8-sig') as f:
            # DictReader allows access by column name, making the code more readable at a negligible performance cost
            contents = csv.DictReader(f)
            for num, row in enumerate(contents, start=2):
                # skip rows where any field is empty, whitespace-only, or missing (None from mismatched columns)
                if '' in row.values() or ' ' in row.values() or None in row.values():
                    logger.warning("Entry from line %i was skipped - empty fields detected.", num)
                    skipped_records +=1
                    continue
                yield row
        logger.info("Skipped %i rows in function 'iter_raw_file()'.", skipped_records)                 
    except (IsADirectoryError, FileNotFoundError) as e:
        logger.error("File %s does not exist: %s", path.name, e)
        raise
    except Exception as e:
        logger.error("Unknown error: %s", e)
        raise


#==========================    TRANSFORM    =============================#


def data_cleaner(raw_data: Iterator[dict]) -> Iterator[dict]:
    """Cast fields to proper numeric types and skip rows with invalid values."""
    skipped_records = 0
    for i, entry in enumerate(raw_data, 2):
        try:
            entry['zip'] = int(float(entry['zip']))
            entry['year_built'] = int(float(entry['year_built']))
            entry['listPrice'] = float(entry['listPrice'])
            entry['lastSoldPrice'] = float(entry['lastSoldPrice'])
            entry['list_to_sold_ratio'] = float(entry['list_to_sold_ratio'])
            entry['sqft'] = float(entry['sqft'])
            entry['price_per_sqft'] = float(entry['price_per_sqft'])
            entry['stories'] = int(float(entry['stories']))
            entry['beds'] = int(float(entry['beds']))
            entry['baths'] = int(float(entry['baths']))
            entry['baths_full'] = int(float(entry['baths_full']))
            entry['baths_full_calc'] = int(float(entry['baths_full_calc']))
            entry['garage'] = int(float(entry['garage']))
            yield entry
        # If the value doesn't match the type - skip row
        except ValueError as e:
            logger.warning('Wrong value in line %i; entry skipped: %s', i, e)
            skipped_records += 1
            continue
        except Exception as e:
            logger.warning('Unknown error in line %i: %s', i, e)
            skipped_records += 1
            continue
    logger.info("Skipped %i rows in function 'data_cleaner()'.", skipped_records)

#============================== LOADER ================================#

def db_create_table(path: Path = path_db):
    """Create the 'offers' table in the SQLite database if it doesn't exist."""
    try:
        # closing() ensures the connection is closed on exit;
        # conn as context manager handles commit on success / rollback on exception
        with (
            closing(sqlite3.connect(path)) as conn,
            conn
        ):
            conn.execute('''
                CREATE TABLE IF NOT EXISTS offers
                    (
                        zip INTEGER,
                        type TEXT,
                        year_built INTEGER,
                        listPrice REAL,
                        lastSoldPrice REAL,
                        list_to_sold_ratio REAL,
                        sqft REAL,
                        price_per_sqft REAL,
                        stories INTEGER,
                        beds INTEGER,
                        baths INTEGER,
                        baths_full INTEGER,
                        baths_full_calc INTEGER,
                        garage INTEGER,
                        sanitized_text TEXT
                    ) STRICT 
            ''')
            
        logger.info("Table %s was successfully created.", path.name)
    
    except sqlite3.Error as e:
        logger.error("SQlite3 Error: %s", e)
        raise
    except (FileNotFoundError, IsADirectoryError) as e:
        logger.error("File %s does not exist: %s", path.name, e)
        raise
    except Exception as e:
        logger.error("Unknown error: %s", e)
        raise


def db_add_data(clean_data: Iterator[dict], path: Path = path_db):
    """Insert cleaned data rows into the 'offers' table."""
    entries_total = 0
    try:
        with(
            closing(sqlite3.connect(path)) as conn,
            conn
        ):
            for entry in clean_data:
                vals = tuple(entry.values())
                conn.execute("INSERT INTO offers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", vals)          
                entries_total += 1

            logger.info("Loaded %i rows to 'offers' table.", entries_total)

    except sqlite3.Error as e:
        logger.error("SQlite3 Error: %s", e)
        raise
    except (IsADirectoryError, FileNotFoundError) as e:
        logger.error("File %s does not exist: %s", path.name, e)
        raise
    except Exception as e:
        logger.error("Unknown error: %s", e)
        raise


def db_get_data(path: Path = path_db) -> list:
     conn = sqlite3.connect(path)
     cur = conn.cursor()
     query = cur.execute("SELECT Count(*) FROM offers")
     result = query.fetchall()
     conn.close()
     return result


def delete_files():
    """Remove the database and log files. Used for clean re-runs."""
    Path("events.log").unlink(missing_ok=True)
    path_db.unlink(missing_ok=True)


def main():
    """Run the full ETL pipeline: extract from CSV, transform types, load into SQLite."""
    db_create_table()
    logger.info("Starting ETL process.")
    extractor = iter_raw_file(path_file)
    logger.info("Extractor has been initialized.")
    transformer = data_cleaner(extractor)
    logger.info("Transformer has been initialized.")
    db_add_data(transformer)
    logger.info("Data has been loaded to the database.")
    #delete_files()  # disabled: keep DB and logs after run for inspection


main()


