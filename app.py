from load_catalog import load_and_clean_catalog
from search.structured_search import StructuredSearchEngine
from search.multimodal_search import MultimodalSearchEngine

def main():
    catalog = load_and_clean_catalog("data/catalog.csv")

    print("\nChoose mode:")
    print("1) Text search")
    print("2) Image + optional text search")

    mode = input("Enter 1 or 2: ").strip()

    if mode == "1":
        engine = StructuredSearchEngine(catalog)
        while True:
            query = input("\nEnter rug search query (or 'exit'): ")
            if query.lower() == "exit":
                break

            results = engine.search(query, top_k=5)
            print("\nTop results:")
            print(results[["Title", "price", "score"]])

    elif mode == "2":
        engine = MultimodalSearchEngine(catalog)

        room_image = input("Enter path to room image (e.g., data/room1.jpeg): ").strip()
        text_query = input("Enter optional text query (or press Enter to skip): ").strip()
        if text_query == "":
            text_query = None

        results = engine.search(room_image, text_query=text_query, top_k=5)

        print("\nTop results:")
        print(results[["Title", "price", "score"]])

    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()