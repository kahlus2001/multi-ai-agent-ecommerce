import pandas as pd
import sqlite3
import re
import webcolors
from fuzzywuzzy import fuzz  # Swap with rapidfuzz if needed


class QueryInterpreterAgent:
    def __init__(self, db_path="db/products.db"):
        # Load product data
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(
            "SELECT brand, category, sub_category, title FROM products", conn)
        conn.close()

        # Colors
        self.colors = list(webcolors.CSS3_NAMES_TO_HEX.keys())

        # Product types (from title, category, subcategory)
        raw_types = pd.Series(
            df['category'].dropna().tolist() +
            df['sub_category'].dropna().tolist() +
            df['title'].dropna().tolist()
        ).str.lower().str.strip().unique().tolist()
        self.types = [t for t in raw_types if len(t) > 2]

        # Brands (cleaned)
        self.brands = [b for b in df['brand'].dropna().str.lower(
        ).str.strip().unique().tolist() if len(b) > 2]

        # Attributes
        self.attributes = ['comfortable', 'discount', 'best rated', 'cheap']

        # Gender-related words to filter from product types
        self.gender_terms = [
            'men', 'man', 'women', 'woman', 'male', 'female',
            'boy', 'girl', 'boys', 'girls', 'unisex'
        ]

        # Debug
        print(
            f"✅ Loaded {len(self.types)} product types, {len(self.brands)} brands.")
        print("📦 Example product types:", self.types[:10])
        print("🏷️ Example brands:", self.brands[:10])

    def run(self, state: dict) -> dict:
        user_input = state.get("user_input", "").lower()
        print(f"\n🔍 Checking user input: {user_input}")

        query_params = {
            "product_type": None,
            "color": None,
            "brand": None,
            "price_min": None,
            "price_max": None,
            "gender": None,
            "attributes": []
        }

        # Match color
        for color in self.colors:
            if re.search(rf"\b{re.escape(color)}\b", user_input):
                print(f"🎨 Matched color: {color}")
                query_params["color"] = color
                break

        # Fuzzy match product type
        print("🎯 Fuzzy matching against product types...")
        best_type = None
        best_type_score = 0
        for p_type in self.types:
            if p_type in self.gender_terms:
                continue
            score = fuzz.partial_ratio(p_type, user_input)
            if score > best_type_score:
                best_type = p_type
                best_type_score = score

        if best_type_score > 80:
            query_params["product_type"] = best_type
            print(
                f"✅ Fuzzy matched product type: {best_type} (score: {best_type_score})")
        else:
            print("❌ No suitable product type match found.")

        # Fuzzy match brand
        print("🎯 Fuzzy matching against brands...")
        best_brand = None
        best_brand_score = 0
        for brand in self.brands:
            if not brand.strip():
                continue
            score = fuzz.partial_ratio(brand, user_input)
            if score > best_brand_score:
                best_brand = brand
                best_brand_score = score

        if best_brand_score > 80:
            query_params["brand"] = best_brand
            print(
                f"✅ Fuzzy matched brand: {best_brand} (score: {best_brand_score})")
        else:
            print("❌ No suitable brand match found.")

        # Match price
        under = re.search(r'under \$?(\d+)', user_input)
        between = re.search(
            r'between \$?(\d+)\s*(?:and|to)\s*\$?(\d+)', user_input)
        if under:
            query_params["price_max"] = int(under.group(1))
        elif between:
            query_params["price_min"] = int(between.group(1))
            query_params["price_max"] = int(between.group(2))

        # Match gender
        if any(term in user_input for term in ['men', 'male', 'man', 'boys', 'boy']):
            query_params["gender"] = "Men"
        elif any(term in user_input for term in ['women', 'female', 'woman', 'girls', 'girl']):
            query_params["gender"] = "Women"
        elif 'unisex' in user_input:
            query_params["gender"] = "Unisex"

        # Match attributes
        for attr in self.attributes:
            if attr in user_input:
                print(f"✨ Matched attribute: {attr}")
                query_params["attributes"].append(attr)

        state["query_params"] = query_params
        return state


if __name__ == "__main__":
    agent = QueryInterpreterAgent()

    test_inputs = [
        "Show me red dresses from Adidas Originals under $50",
        "Looking for a black t-shirt between $20 and $40 for men",
        "I want comfortable jeans from Puma",
        "Best rated blue pants for women",
        "I'm looking for a grey hoodie from Levis for boys",
        "Show me a white tshirt from HM for girls",
        "Find a unisex jacket under $100"
    ]

    for query in test_inputs:
        state = {"user_input": query}
        result = agent.run(state)
        print(f"\n📝 Input: {query}")
        print(f"📦 Parsed: {result['query_params']}")
