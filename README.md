# pyPII-TDM - PM
This is a small, simple project to generate a bank party master PM using synthetic data. I use it for development and performance testing of masking algorithms.

Test run - Inserted 10000000 party rows in 3927.80s = 1:05h

## Running the console app
The `pm` console script provides a simple menu to test the database connection and list tables.

```bash
cd pm
uv sync          # install dependencies (pymssql / FreeTDS bundled)
uv run pm        # start the menu
```

Menu options:
- `1` Test connection
- `2` List tables
- `3` Generate sample party data
- `4` List last 5 rows (id, name)
- `5` Show a party by id
- `q` Quit

Notes:
- Uses `pymssql` (FreeTDS) so no system ODBC driver is needed. Just run `uv sync` to install dependencies.
- Option 3 randomly samples from `pm/sample_data.csv` (1000 unique rows) and inserts the requested count into `dbo.Party`.
