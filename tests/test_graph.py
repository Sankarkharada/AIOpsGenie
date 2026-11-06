from app.agents.graph import graph


def main():

    print("\n===================================")
    print("       AIOPSGENIE AI ASSISTANT")
    print("===================================")

    query = input("\nUser: ")

    result = graph.invoke({
        "user_query": query
    })

    print("\n===================================")
    print("DETECTED INTENT")
    print("===================================")

    print(result.get("intent"))

    print("\n===================================")
    print("AI RESPONSE")
    print("===================================")

    print(result.get("response"))

    print("\n===================================")
    print("KNOWLEDGE SOURCES")
    print("===================================")

    print(result.get("sources", "Not applicable"))


if __name__ == "__main__":
    main()