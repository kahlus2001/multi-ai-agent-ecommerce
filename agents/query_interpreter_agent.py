import os
import re
import json
import pandas as pd
import sqlite3
import webcolors
from dotenv import load_dotenv
from rapidfuzz import fuzz

from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic.v1 import BaseModel, Field

load_dotenv()
USE_LLM = os.getenv("USE_LLM", "false").lower() == "true"

class QueryFilters(BaseModel):
    product_type: str | None = Field(default=None)
    color: str | None = Field(default=None)
    brand: str | None = Field(default=None)
    price_min: int | None = Field(default=None)
    price_max: int | None = Field(default=None)
    gender: str | None = Field(default=None)
    attributes: list[str] = Field(default_factory=list)

parser = JsonOutputParser(pydantic_object=QueryFilters)
instructions = parser.get_format_instructions().replace("{", "{{").replace("}", "}}")

prompt = ChatPromptTemplate.from_messages([
    ("system", 
    """You are a product search assistant. Your job is to extract structured filters from natural language product queries.

Only return a JSON object with **these keys**: 
- product_type (from category, sub_category, or title fields)
- color (as a CSS3 color name, like "red", "black", not hex codes)
- brand (match against known brand names)
- price_min (in USD, optional)
- price_max (in USD, optional)
- gender (Men, Women, Unisex, etc.)
- attributes (list of descriptive words from product_details, e.g. waterproof, comfortable, breathable)

Rules:
- DO NOT include any explanations or comments.
- DO NOT invent new keys.
- Use null if a field is not found.
- Keep attributes as a list of strings.
- 'cheap' implies price_max is low, 'expensive' implies high price_min, but do not assign specific numbers.
- Examples of valid gender values: "men", "women", "unisex", "boys", "girls"
- Always format your output as strict JSON matching the required keys.
"""
    ),
    ("human", 
     "Query: {input}\n\nReturn ONLY valid JSON matching the above format.")
])



llm = ChatOllama(model="mistral")

class QueryInterpreterAgent:
    def __init__(self, db_path="db/products.db"):
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT brand, category, sub_category, title, product_details FROM products", conn)
        conn.close()

        self.colors = list(webcolors.CSS3_NAMES_TO_HEX.keys())

        raw_types = pd.Series(
            df['category'].dropna().tolist() +
            df['sub_category'].dropna().tolist() +
            df['title'].dropna().tolist()
        ).str.lower().str.strip().unique().tolist()
        self.types = [t for t in raw_types if len(t) > 2]

        self.brands = [b for b in df['brand'].dropna().str.lower().str.strip().unique().tolist() if len(b) > 2]

        details_text = df['product_details'].dropna().astype(str).str.lower().str.cat(sep=" ")
        self.attributes = pd.Series(re.findall(r'\b[a-zA-Z\-]{4,}\b', details_text)).value_counts().head(30).index.tolist()

        self.gender_terms = ['men', 'man', 'women', 'woman', 'male', 'female', 'boy', 'girl', 'boys', 'girls', 'unisex']

        print(f"✅ Loaded {len(self.types)} product types, {len(self.brands)} brands.")
        print("🎯 Top attributes:", self.attributes[:10])

    def run(self, state: dict) -> dict:
        user_input = state.get("user_input", "").lower()
        print(f"\n🔍 User input: {user_input}")

        query_params = {
            "product_type": None,
            "color": None,
            "brand": None,
            "price_min": None,
            "price_max": None,
            "gender": None,
            "attributes": []
        }

        if USE_LLM:
            try:
                chain = prompt | llm | parser
                llm_result = chain.invoke({"input": user_input})
                query_params = llm_result.dict() if hasattr(llm_result, 'dict') else llm_result
                print("🤖 LLM matched filters:", query_params)
                state["query_params"] = query_params
                return state
            except Exception as e:
                print("⚠️ LLM parsing failed, falling back to rule-based:", str(e))

        print("🧠 Using rule-based interpreter...")

        for color in self.colors:
            if re.search(rf"\\b{re.escape(color)}\\b", user_input):
                query_params["color"] = color
                break

        best_type, best_score = None, 0
        for p_type in self.types:
            if p_type in self.gender_terms:
                continue
            score = fuzz.partial_ratio(p_type, user_input)
            if score > best_score:
                best_type, best_score = p_type, score
        if best_score > 80:
            query_params["product_type"] = best_type

        best_brand, best_score = None, 0
        for brand in self.brands:
            if not brand.strip():
                continue
            score = fuzz.partial_ratio(brand, user_input)
            if score > best_score:
                best_brand, best_score = brand, score
        if best_score > 80:
            query_params["brand"] = best_brand

        under = re.search(r'under \$?(\d+)', user_input)
        over = re.search(r'(?:over|above|more than) \$?(\d+)', user_input)
        between = re.search(r'between \$?(\d+)\s*(?:and|to)\s*\$?(\d+)', user_input)
        if under:
            query_params["price_max"] = int(under.group(1))
        elif over:
            query_params["price_min"] = int(over.group(1))
        elif between:
            query_params["price_min"] = int(between.group(1))
            query_params["price_max"] = int(between.group(2))

        if any(term in user_input for term in ['men', 'male', 'man', 'boys', 'boy']):
            query_params["gender"] = "Men"
        elif any(term in user_input for term in ['women', 'female', 'woman', 'girls', 'girl']):
            query_params["gender"] = "Women"
        elif 'unisex' in user_input:
            query_params["gender"] = "Unisex"

        for attr in self.attributes + ['cheap', 'expensive']:
            if attr in user_input:
                query_params["attributes"].append(attr)

        print("✅ Rule-based filters:", query_params)
        state["query_params"] = query_params
        return state
