import sqlite3
from langchain.agents import Tool, initialize_agent
from langchain_core.runnables import Runnable
from langchain_core.language_models import BaseLanguageModel
from langchain_openai import ChatOpenAI


# Tool to execute a SQL query
def make_execute_db_query_tool(db_path: str):
    def execute(query: str):
        try:
            if "limit" not in query.lower():
                query += " LIMIT 5"
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            return f"⚠️ Query failed: {e}"
    return execute


# Optional helper to get known values from DB
def get_distinct_values(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    result = {
        "brands": [row[0] for row in cursor.execute("SELECT DISTINCT brand FROM products WHERE brand IS NOT NULL")],
        "categories": [row[0] for row in cursor.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL")],
        "sub_categories": [row[0] for row in cursor.execute("SELECT DISTINCT sub_category FROM products WHERE sub_category IS NOT NULL")]
    }
    conn.close()
    return result


# SearchAgent
class SearchAgent(Runnable):
    def __init__(self, db_path: str, llm: BaseLanguageModel = None):
        self.llm = llm or ChatOpenAI(temperature=0)
        self.db_path = db_path
        self.execute_tool = make_execute_db_query_tool(db_path)

        self.tools = [
            Tool(
                name="execute_db_query",
                func=self.execute_tool,
                description=(
                    "Use this tool to query the SQLite products database.\n"
                    "Allowed filters:\n"
                    "- `selling_price` (REAL) using >= or <=\n"
                    "- Match words from query in `title` using LOWER(title) LIKE '%word%'\n"
                    "Do NOT use other columns.\n"
                    "Use LIMIT 5.\n"
                    "Example:\n"
                    "SELECT * FROM products WHERE LOWER(title) LIKE '%jacket%' AND selling_price <= 1000 LIMIT 10"
                )
            )
        ]

        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent="zero-shot-react-description",
            verbose=True
        )

    def run_prompt(self, query_params):
        prompt = (
            "You are querying a `products` SQLite table.\n"
            f"The user provided query params: {query_params}\n\n"
            "Build a SQL query using ONLY these rules:\n"
            "- Match text values from `product_type`, `color`, `brand`, `attributes` in the `title` "
            "using LOWER(title) LIKE '%value%'\n"
            "- Use `selling_price >= price_min` if provided\n"
            "- Use `selling_price <= price_max` if provided\n"
            "Only use `title` and `selling_price` in the WHERE clause.\n"
            "Run the query using the `execute_db_query` tool. Use LIMIT 5.\n"
            "If query returns something, return the results in JSON format.\n"
            "If no results are found, change the query to something more generic.\n"
            "Return the results in JSON format.\n\n"
        )
        return self.agent.run(prompt)

    def invoke(self, state: dict) -> dict:
        query_params = state.get("query_params")

        if query_params:
            response = self.run_prompt(query_params)
        else:
            # Fallback when structured query not available
            response = self.agent.run(
                "No structured filters provided. "
                "Infer keywords from the user input and query the `products` table. "
                "Search these keywords in the `title` column using LOWER(title) LIKE '%keyword%'. "
                "Return up to 5 results using the `execute_db_query` tool."
            )

        state["search_results"] = response if isinstance(response, list) else [response]
        return state
