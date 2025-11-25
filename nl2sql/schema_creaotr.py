import pandas as pd

# 1) Load files
tables = pd.read_csv("Tables.csv", sep=";")
fields = pd.read_csv("All_Fielddescriptions.csv", sep=";")
relations = pd.read_csv("Relation_Keys.csv", sep=";")

# Normalize column names if needed
tables.columns = [c.lower() for c in tables.columns]
fields.columns = [c.lower() for c in fields.columns]
relations.columns = [c.lower() for c in relations.columns]


# 2) Helper: SQL type mapping from your CSV type → SQL Server type
TYPE_MAP = {
    "int": "INT",
    "bigint": "BIGINT",
    "smallint": "SMALLINT",
    "tinyint": "TINYINT",
    "float": "FLOAT",
    "decimal": "DECIMAL(18,4)",
    "varchar": "VARCHAR(255)",
    "nvarchar": "NVARCHAR(255)",
    "text": "TEXT",
    "date": "DATE",
    "datetime": "DATETIME",
    "bit": "BIT",
}


def map_type(t):
    t = str(t).lower()
    for k, v in TYPE_MAP.items():
        if t.startswith(k):
            return v
    return "NVARCHAR(255)"   # fallback


# 3) Build CREATE TABLE statements
schema_sql = []

for _, trow in tables.iterrows():
    table_name = trow["tablename"]

    # Get all columns for this table
    fset = fields[fields["tablename"] == table_name]

    columns_sql = []
    primary_keys = []

    for _, f in fset.iterrows():
        colname = f["fieldname"]
        coltype = map_type(f["datatype"])
        nullable = "NOT NULL" if f.get("isnull", "YES") in ["NO", 0, "0"] else "NULL"

        columns_sql.append(f"    [{colname}] {coltype} {nullable}")

        if str(f.get("isprimary", "")).lower() in ["yes", "true", "1"]:
            primary_keys.append(colname)

    # Build primary key constraint
    pk_sql = ""
    if primary_keys:
        cols = ", ".join(f"[{c}]" for c in primary_keys)
        pk_sql = f",\n    CONSTRAINT [PK_{table_name}] PRIMARY KEY ({cols})"

    create_sql = f"CREATE TABLE [{table_name}] (\n" + ",\n".join(columns_sql) + pk_sql + "\n);\n"
    schema_sql.append(create_sql)


# 4) Foreign Keys
fk_sql_statements = []

for _, r in relations.iterrows():
    child = r["child_table"]
    child_col = r["child_column"]
    parent = r["parent_table"]
    parent_col = r["parent_column"]

    fk_name = f"FK_{child}_{child_col}_{parent}"

    fk_sql = (
        f"ALTER TABLE [{child}] "
        f"ADD CONSTRAINT [{fk_name}] FOREIGN KEY ([{child_col}]) "
        f"REFERENCES [{parent}] ([{parent_col}]);"
    )
    fk_sql_statements.append(fk_sql)

# 5) Final SQL script
FULL_SCHEMA = "\n\n".join(schema_sql + fk_sql_statements)

# Print or save to a file
print(FULL_SCHEMA)

with open("generated_schema.sql", "w", encoding="utf-8") as f:
    f.write(FULL_SCHEMA)

print("Schema generated → generated_schema.sql")
