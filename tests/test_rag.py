from app.rag.retriever import search_knowledge


def main():

    query = input("\nKnowledge Query: ")

    results = search_knowledge(query)

    print("\n--- RETRIEVED KNOWLEDGE ---")

    for index, document in enumerate(results, start=1):

        print(f"\n[{index}]")
        print("Source:", document.metadata.get("source"))
        print(document.page_content[:1000])


if __name__ == "__main__":
    main()