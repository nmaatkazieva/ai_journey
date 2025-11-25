import os
import pandas as pd
from langchain_openai import AzureChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import create_agent

# -----------------------------
# Read and trim CSV files
# -----------------------------
def read_csv_trimmed(file_name, keep_columns):
    df = pd.read_csv(file_name, sep=";", encoding="utf-8")
    df = df[keep_columns]
    return df.to_dict(orient="records")  # compact JSON-like

tables = read_csv_trimmed("tables.csv", ["USERLEVEL_NAME", "LOGICAL_NAME"])
columns = read_csv_trimmed("columns.csv", ["TABLE_ID", "USERLEVEL_NAME", "LOGICAL_NAME", "PK_FIELD_ID"])
relations = read_csv_trimmed("relation_keys.csv", ["ParentTable", "ParentColumn", "ReferencedTable", "ReferencedColumn"])

# Convert to string for prompt embedding
import json
tables_json = json.dumps(tables, ensure_ascii=False)
columns_json = json.dumps(columns, ensure_ascii=False)
relations_json = json.dumps(relations, ensure_ascii=False)

# Save to a file
with open("tables.json", "w") as f:
    json.dump(tables_json, f, indent=4)  # indent=4 makes it pretty-printed
    # Save to a file
with open("columns.json", "w") as f:
    json.dump(columns_json, f, indent=4)  # indent=4 makes it pretty-printed
    # Save to a file
with open("relations.json", "w") as f:
    json.dump(relations_json, f, indent=4)  # indent=4 makes it pretty-printed

# -----------------------------
# System prompt
# -----------------------------
system_prompt = f"""
You are an intelligent SQL analysis agent for the Hoffmann & Co Assekuradeur transport-insurance database.
Your task is to translate user questions into high-quality SQL queries for Microsoft SQL Server
and interpret results clearly.

Database Schema (embedded, only essential info):
------------------------------------------------
NOTE: The CSV metadata is in German (USERLEVEL_NAME columns). Translate English ↔ German internally.

Tables (names):
{tables_json}

Columns:
{columns_json}

Relationships (foreign keys):
{relations_json}

Agent Rules:
-------------
1. Always use the embedded schema to resolve table and column names.
2. Never use SELECT *; always pick relevant fields.
3. Limit results to {{top_k}} rows unless the user requests otherwise.
4. Never run DML statements (INSERT, UPDATE, DELETE, DROP).
5. Respect foreign key relationships to join tables correctly.
6. Translate user queries from English ↔ German internally if needed.
7. Summarize results clearly after execution, mentioning tables and columns used.
8. For counts, distributions, or top N queries, always aggregate and limit accordingly.
"""

# -----------------------------
# Initialize LLM
# -----------------------------
llm = AzureChatOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    deployment_name=os.environ["AZURE_OPENAI_DEPLOYMENT"],
    openai_api_key=os.environ["AZURE_OPENAI_API_KEY"],
    openai_api_version=os.environ["OPENAI_API_VERSION"],
    temperature=0  # deterministic outputs for SQL
)

# -----------------------------
# SQL Database setup
# -----------------------------
SQL_DB_URI = (
    "mssql+pyodbc://@localhost/VMH?"
    "driver=ODBC+Driver+18+for+SQL+Server"
    "&trusted_connection=yes"
    "&TrustServerCertificate=yes"
)
db = SQLDatabase.from_uri(SQL_DB_URI)
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
tools = toolkit.get_tools()

# -----------------------------
# Create agent
# -----------------------------
agent = create_agent(
    llm,
    tools,
    system_prompt=system_prompt,
)

# -----------------------------
# Example query execution with retry
# -----------------------------
question = "which broker has the most contracts in 2023"


for step in agent.stream(
    {"messages": [{"role": "user", "content": question}]},
    stream_mode="values",
):
    message = step["messages"][-1]
    message.pretty_print()