import csv
import sqlite3
from pathlib import Path

DATA_PATH = Path("cell-count.csv") #Path(__file__).parent / "cell-count.csv" 
DB_PATH = Path("loblaw-database.db") #Path(__file__).parent / "loblaw-database.db"

POPULATIONS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]

#Initialize Database 
SCHEMA = """
    CREATE TABLE subjects (
        subject_id TEXT PRIMARY KEY, 
        project TEXT NOT NULL, 
        condition TEXT NOT NULL, 
        age INTEGER NOT NULL, 
        sex TEXT NOT NULL CHECK (sex IN ('M', 'F')), 
        treatment TEXT NOT NULL,
        response TEXT NOT NULL CHECK (response IN ('yes', 'no', '')));
        
    CREATE TABLE samples (
        sample_id TEXT PRIMARY KEY, 
        subject_id TEXT NOT NULL, 
        sample_type TEXT NOT NULL, 
        time_from_treatment_start INTEGER NOT NULL,

        FOREIGN KEY (subject_id) REFERENCES Subjects(subject_id));

    CREATE TABLE cell_counts (
        sample_id TEXT NOT NULL, 
        population TEXT NOT NULL, 
        count INTEGER NOT NULL,

        PRIMARY KEY (sample_id, population), 
        FOREIGN KEY (sample_id) REFERENCES Samples(sample_id));
"""

def create_tables(connection):
    connection.executescript(SCHEMA)

#Load all rows form cell-count.csv
def load_data(connection):
    with DATA_PATH.open(newline="") as file: 
        data = csv.DictReader(file)
        for row in data: 
            connection.execute(
                """INSERT OR IGNORE INTO subjects 
                (subject_id, project, condition, age, sex, treatment, response)
                VALUES (?, ?, ?, ?, ?, ?, ?)""", (
                    row["subject"],
                    row["project"], 
                    row["condition"], 
                    int(row["age"]), 
                    row["sex"],
                    row["treatment"], 
                    row["response"]
                )
            )
            connection.execute(
                """INSERT INTO samples
                (sample_id, subject_id, sample_type, time_from_treatment_start)
                VALUES (?, ?, ?, ?)""", (
                    row["sample"], 
                    row["subject"], 
                    row["sample_type"],
                    int(row["time_from_treatment_start"])
                )
            )
            for population in POPULATIONS:
                connection.execute(
                    """INSERT INTO cell_counts
                    (sample_id, population, count)
                    VALUES (?, ?, ?)""", (
                        row["sample"], 
                        population, 
                        int(row[population])
                    )
                )

def main(): 
    if not DATA_PATH.exists(): 
        raise FileNotFoundError(f"Input file not found: {DATA_PATH}")
    #Delete database if already exists  
    if DB_PATH.exists():
        DB_PATH.unlink()
    with sqlite3.connect(DB_PATH) as connection: 
        connection.execute("PRAGMA foreign_keys = ON")
        create_tables(connection)
        load_data(connection)
    print(f"Database created: {DB_PATH}")

if __name__ == "__main__":
    main()

