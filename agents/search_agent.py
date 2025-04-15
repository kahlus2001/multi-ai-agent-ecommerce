import sqlite3
from langchain.agents import Tool, initialize_agent
from langchain_core.runnables import Runnable
from langchain_core.language_models import BaseLanguageModel
from langchain_openai import ChatOpenAI


# tool
def make_execute_db_query_tool(db_path: str):
    def execute(query: str):
        try:
            # Force limit if not present
            if "limit" not in query.lower():
                query += " LIMIT 10"

            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

        except Exception as e:
            return f"⚠️ Query failed: {e}"
    return execute


class SearchAgent(Runnable):
    def __init__(self, db_path: str, llm: BaseLanguageModel = None):
        self.llm = llm or ChatOpenAI(temperature=0)
        self.db_path = db_path

        self.valid_columns = [
            "id", "title", "description", "brand", "category", "sub_category",
            "actual_price", "selling_price", "average_rating", "discount",
            "seller", "out_of_stock", "url"
        ]

        # Tool for executing SQL
        execute_tool = make_execute_db_query_tool(db_path)

        self.tools = [
            Tool(
                name="execute_db_query",
                func=execute_tool,
                description=(
                    "Use this tool to query the products SQLite database.\n"
                    "✅ Available columns:\n"
                    "- id (TEXT)\n"
                    "- title (TEXT)\n"
                    "- description (TEXT)\n"
                    "- brand (TEXT)\n"
                    "- category (TEXT)\n"
                    "- sub_category (TEXT)\n"
                    "- actual_price (REAL)\n"
                    "- selling_price (REAL)\n"
                    "- average_rating (REAL)\n"
                    "- discount (TEXT)\n"
                    "- seller (TEXT)\n"
                    "- out_of_stock (INTEGER: 0 = in stock, 1 = out of stock)\n"
                    "- url (TEXT)\n\n"
                    "❗Only use fields from `query_params` in the WHERE clause.\n"
                    "🚫 Do NOT infer or guess fields if not explicitly provided.\n"
                    "🚫 Do NOT wrap the SQL query in backticks or triple backticks.\n"
                    "Example:\n"
                    "SELECT * FROM products WHERE LOWER(brand) LIKE '%york%' AND selling_price < 1000 LIMIT 5"
                )
            )
        ]

        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent="zero-shot-react-description",
            verbose=True
        )

    def invoke(self, state: dict) -> dict:
        query_params = state.get("query_params")
        
        if query_params:
            prompt = (
                "You are querying an SQLite database with a `products` table.\n"
                f"The user provided the following filters as key-value pairs: {query_params}\n\n"
                "✅ Available columns:\n"
                "- id, title, description, brand, category, sub_category\n"
                "- actual_price, selling_price, average_rating, discount\n"
                "- seller, out_of_stock, url\n\n"
                "❗ Only use these fields in the WHERE clause.\n"
                "For text fields, use LOWER(...) with LIKE for fuzzy matching.\n"
                "Do not use columns that aren't listed.\n"
                "Do NOT return the SQL query.\n\n"
                "Instead, use the `execute_db_query` tool to run the SQL query.\n"
                "After the tool is called, return only the **first matching product** (as a dictionary)."
            )
        else:
            prompt = (
                "User did not provide structured filters. "
                "Try to infer user intent and query the SQLite `products` table accordingly.\n"
                "Use only these columns: id, title, description, brand, category, sub_category, actual_price, "
                "selling_price, average_rating, discount, seller, out_of_stock, url.\n"
                "Use LOWER(...) with LIKE for fuzzy matching on text fields.\n"
                "Call the `execute_db_query` tool with the generated SQL query.\n"
                "Then return only the **first matching product** as a dictionary."
            )

        response = self.agent.run(prompt)

        state["search_results"] = (
            response if isinstance(response, list) else [response]
        )
        return state

