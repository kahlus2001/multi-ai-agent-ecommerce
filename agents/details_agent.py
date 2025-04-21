from langchain_core.runnables import Runnable
from langchain_core.language_models import BaseLanguageModel
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
load_dotenv()


class DetailsAgent(Runnable):
    def __init__(self, llm: BaseLanguageModel = None):
        self.llm = llm or ChatOpenAI(temperature=0.7)

        self.prompt = ChatPromptTemplate.from_template(
            """You are a smart and friendly shopping assistant helping a user choose the best product from the search results below.

        Your task is to:
        - Analyze the products deeply based on price, discount, brand reputation, average rating, seller credibility, availability, and any other relevant info.
        - Recommend **up to 3 of the best options** — but write your response like you're chatting with a friend.
        - DO NOT list the products or number them.
        - DO NOT use bullet points.
        - Instead, write a smooth, natural paragraph that compares the options informally and clearly ranks them by highlighting the best first.
        - Mention things like “great deal,” “worth considering,” “solid backup option,” or “if you're on a tighter budget,” to make your advice feel personal and practical.
        - Include purchase links **inline** in the sentence where the product is mentioned.
        - If no products are available, say so politely and briefly.

        Keep your tone helpful, conversational, and engaging — like a real human giving thoughtful shopping advice.

        Search results (in JSON-like format):
        {products}

        Your response:"""
        )


    def invoke(self, state: dict) -> dict:
        products = state.get("search_results", [])

        # Convert product dictionaries to a readable string for the LLM
        product_text = "\n".join([str(p) for p in products]) if products else "[]"

        chain = self.prompt | self.llm
        response = chain.invoke({"products": product_text})

        # Save the response back into the state for display
        state["final_response"] = response.content
        return state
    
if __name__ == "__main__":
    # Sample search result (as would come from SearchAgent)
    test_state = {
        "search_results": [
            {
                "title": "Nike Revolution 5 Running Shoes",
                "brand": "Nike",
                "selling_price": 2999,
                "actual_price": 4999,
                "discount": "40%",
                "average_rating": 4.4,
                "category": "Footwear",
                "sub_category": "Running Shoes",
                "seller": "Nike Official Store",
                "out_of_stock": 0,
                "url": "https://example.com/nike-revolution-5"
            },
            {
                "title": "Adidas Lite Racer",
                "brand": "Adidas",
                "selling_price": 2799,
                "actual_price": 3999,
                "discount": "30%",
                "average_rating": 4.1,
                "category": "Footwear",
                "sub_category": "Casual Shoes",
                "seller": "Adidas Authorized",
                "out_of_stock": 0,
                "url": "https://example.com/adidas-lite-racer"
            }
        ]
    }

    # Run the DetailsAgent with test data
    agent = DetailsAgent()
    result_state = agent.invoke(test_state)

    # Print out the generated response
    print("\n🧪 Test Output:")
    print(result_state["final_response"])
 
