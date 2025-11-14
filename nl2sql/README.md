# SQL Agent with Azure OpenAI

This Python script (`sql_agent.py`) demonstrates how to build a **SQL agent** that interacts with a SQL database using an **Azure OpenAI Chat model** and **LangChain**. The agent can generate SQL queries based on user questions, execute them against a database, and return results in a readable format.


---

## Prerequisites

1. **Python 3.10+** installed
2. **SQL database** (example uses `Chinook.db`)
3. **Azure OpenAI account** with a deployed model

---

## How-To-Run

1. Install packages `pip install -r requirements.txt`
2. Create a .env file in the project root:
```
AZURE_OPENAI_ENDPOINT=https://<your-azure-endpoint>.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=<your-deployment-name>
AZURE_OPENAI_API_KEY=<your-api-key>
OPENAI_API_VERSION=2023-07-01-preview
SQL_DB_URI=sqlite:///Chinook.db
```
3. Run code `python sql_agent.py`

