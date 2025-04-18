from langchain_core.runnables import Runnable
from langchain_core.language_models import BaseLanguageModel
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

class DetailsAgent(Runnable):
    def __init__(self, llm: BaseLanguageModel = None):
        self.llm = llm or ChatOpenAI(temperature=0.7)

        self.prompt = ChatPromptTemplate.from_template(
            """You are a helpful shopping assistant. Based on the user's query and the following product search results, generate a friendly and informative response. Highlight key features like price, discount, brand, and rating. If no products were found, say so kindly.

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
 
