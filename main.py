from graph.graph_builder import build_graph
import kagglehub
from db.provision import provision_database_from_json
import os

def main():
    # Download and prepare dataset
    path = kagglehub.dataset_download("aaditshukla/flipkart-fasion-products-dataset")
    json_path = os.path.join(path, "flipkart_fashion_products_dataset.json")
    db_path = "./db/products.db"

    # Create the SQLite DB from JSON
    provision_database_from_json(json_path, db_path)

    # Build the graph
    graph = build_graph(db_path)

    # Run CLI loop

    while True:
        user_input = input("Enter your query: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        response = graph.invoke({"user_input": user_input})

        print("\n🛍️ Smart Shopping Assistant Says:")
        print(response.get("final_response", "⚠️ No response generated."))

if __name__ == "__main__":
    main()
