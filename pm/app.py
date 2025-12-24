CONNECTION_STRING = "Server=prod.home.arpa;Database=pm;User Id=pmuser;Password=StrongP@ssw0rd!;"

import random
import sys
import os
import atexit
import time
from pathlib import Path
from contextlib import closing
from typing import Callable

import pymssql
from sample_data import CSV_HEADERS, SAMPLE_CSV_PATH, load_csv_rows

try:
    import readline  # type: ignore
except ImportError:
    readline = None


def _connection_params() -> dict[str, str]:
    params: dict[str, str] = {}
    for part in CONNECTION_STRING.split(";"):
        if not part.strip():
            continue
        if "=" in part:
            key, value = part.split("=", 1)
            params[key.strip()] = value.strip()
    return params


def _connect() -> pymssql.Connection:
    params = _connection_params()
    return pymssql.connect(
        server=params.get("Server"),
        database=params.get("Database"),
        user=params.get("User Id") or params.get("Uid"),
        password=params.get("Password"),
        port=int(params.get("Port", "1433")),
        timeout=5,
        login_timeout=5,
        as_dict=False,
    )


def test_connection() -> None:
    try:
        with _connect() as conn:
            with closing(conn.cursor()) as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        print("Connection succeeded.")
    except pymssql.Error as exc:
        print(f"Connection failed: {exc}")


def list_tables() -> None:
    try:
        with _connect() as conn:
            with closing(conn.cursor()) as cur:
                cur.execute(
                    """
                    SELECT s.name AS schema_name, t.name AS table_name
                    FROM sys.tables t
                    JOIN sys.schemas s ON t.schema_id = s.schema_id
                    ORDER BY s.name, t.name;
                    """
                )
                tables = cur.fetchall()
                if not tables:
                    print("No tables found.")
                    return
                for schema, name in tables:
                    cur.execute(f"SELECT COUNT(*) FROM [{schema}].[{name}]")
                    row_count = cur.fetchone()[0]
                    print(f"{schema}.{name} (rows: {row_count})")
    except pymssql.Error as exc:
        print(f"Could not list tables: {exc}")


def generate_data() -> None:
    start_time = time.perf_counter()
    raw = input("How many rows to generate? [default 1000] ").strip()
    if readline and readline.get_current_history_length() > 0:
        try:
            readline.remove_history_item(readline.get_current_history_length() - 1)
        except Exception:
            pass
    if raw == "":
        count = 1000
    elif raw.isdigit() and int(raw) > 0:
        count = int(raw)
    else:
        print("Please enter a positive integer.")
        return
    try:
        all_rows = load_csv_rows(SAMPLE_CSV_PATH)
        if not all_rows:
            print(f"No rows found in CSV at {SAMPLE_CSV_PATH}")
            return
        pools: dict[str, list[str]] = {h: [] for h in CSV_HEADERS}
        for row in all_rows:
            for header, value in zip(CSV_HEADERS, row):
                pools[header].append(value)

        inserted = 0
        batch: list[tuple[str, ...]] = []
        batch_size = 500
        with _connect() as conn:
            with closing(conn.cursor()) as cur:
                cur.execute("SET DEADLOCK_PRIORITY LOW; SET LOCK_TIMEOUT 5000;")
                insert_sql = """
                    INSERT INTO dbo.Party
                        (FirstName, LastName, Address1, Address2, Zip, City, Country, [Type])
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                for seq in range(1, count + 1):
                    name1 = random.choice(pools["name1"])
                    name2 = random.choice(pools["name2"])
                    surname1 = random.choice(pools["surname1"])
                    surname2 = random.choice(pools["surname2"])
                    street = random.choice(pools["street"])
                    postal = random.choice(pools["postal_code"])
                    city = random.choice(pools["city"])
                    country = random.choice(pools["country"])
                    first_name = f"{name1} {name2}".strip()
                    last_name = f"{surname1} {surname2}".strip()
                    party_type = random.choice(["Person", "Company"])
                    batch.append(
                        (
                            first_name,
                            last_name,
                            street,
                            "",
                            postal,
                            city,
                            country,
                            party_type,
                        )
                    )
                    if len(batch) >= batch_size:
                        cur.executemany(insert_sql, batch)
                        conn.commit()
                        inserted += len(batch)
                        batch.clear()
                        print(f"Inserted {inserted}/{count}", end="\r", flush=True)
                if batch:
                    cur.executemany(insert_sql, batch)
                    conn.commit()
                    inserted += len(batch)
                    print(f"Inserted {inserted}/{count}", end="\r", flush=True)
        duration = time.perf_counter() - start_time
        print(f"\nInserted {inserted} party rows in {duration:.2f}s.")
    except pymssql.Error as exc:
        print(f"Failed to generate data: {exc}")


def list_recent_rows() -> None:
    try:
        with _connect() as conn:
            with closing(conn.cursor()) as cur:
                cur.execute(
                    """
                    SELECT TOP 5
                        Id,
                        CONCAT_WS(' ', FirstName, LastName) AS FullName
                    FROM dbo.Party
                    ORDER BY Id DESC;
                    """
                )
                rows = cur.fetchall()
                if not rows:
                    print("No rows in dbo.Party.")
                    return
                for pid, name in rows:
                    print(f"{pid} | {name.strip()}")
    except pymssql.Error as exc:
        print(f"Could not list recent rows: {exc}")


def _print_table(headers: list[str], rows: list[tuple]) -> None:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len("" if val is None else str(val)))

    def fmt_row(row_vals):
        return " | ".join(str(val if val is not None else "").ljust(widths[i]) for i, val in enumerate(row_vals))

    divider = "-+-".join("-" * w for w in widths)
    print(fmt_row(headers))
    print(divider)
    for row in rows:
        print(fmt_row(row))


def show_party_by_id() -> None:
    raw = input("Enter Id: ").strip()
    if not raw.isdigit():
        print("Please enter a numeric id.")
        return
    pid = int(raw)
    try:
        with _connect() as conn:
            with closing(conn.cursor()) as cur:
                cur.execute(
                    """
                    SELECT
                        Id, FirstName, LastName,
                        Address1, Address2, Zip,
                        City, Country, [Type]
                    FROM dbo.Party
                    WHERE Id = %s
                    """,
                    (pid,),
                )
                row = cur.fetchone()
                if not row:
                    print(f"No Party found with id {pid}.")
                    return
                headers = [
                    "Id",
                    "FirstName",
                    "LastName",
                    "Address1",
                    "Address2",
                    "Zip",
                    "City",
                    "Country",
                    "Type",
                ]
                _print_table(headers, [row])
    except pymssql.Error as exc:
        print(f"Could not fetch party: {exc}")


def _clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def _setup_history() -> None:
    if not readline:
        return
    histfile = Path(__file__).with_name(".pm_history")
    try:
        readline.read_history_file(histfile)
    except FileNotFoundError:
        pass
    readline.set_history_length(200)

    def save_history() -> None:
        try:
            readline.write_history_file(histfile)
        except Exception:
            pass

    atexit.register(save_history)


def main() -> None:
    _setup_history()
    options: dict[str, tuple[str, Callable[[], None]]] = {
        "1": ("Test connection", test_connection),
        "2": ("List tables", list_tables),
        "3": ("Generate sample party data", generate_data),
        "4": ("List last 5 rows (id, name)", list_recent_rows),
        "5": ("Show a party by id", show_party_by_id),
        "q": ("Quit", lambda: sys.exit(0)),
    }
    while True:
        _clear_screen()
        print("\nChoose an option:")
        for key, (label, _) in options.items():
            print(f"{key}. {label}")
        choice = input("Enter choice: ").strip().lower()
        if choice in options:
            _, action = options[choice]
            action()
        else:
            print("Invalid choice. Try again.")
        input("\nPress Enter to return to the menu...")


if __name__ == "__main__":
    main()
