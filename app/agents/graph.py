import re

from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END

from app.agents.state import AgentState
from app.rag.retriever import search_knowledge

from app.tools.ticket_tool import (
    create_ticket,
    get_ticket_status
)

from app.tools.system_tool import check_service_status


llm = ChatOllama(
    model="llama3.2:3b",
    temperature=0.1
)


# NODE 1: CLASSIFY QUERY
def classify_query(state: AgentState):

    query = state["user_query"]
    query_lower = query.lower()

    # Explicit ticket creation
    if re.search(r"\b(create|raise|open|submit)\b.*\bticket\b", query_lower):

        intent = "TICKET"

    # Explicit ticket lookup
    elif re.search(r"\b(check|show|get|find)\b.*\bticket\b", query_lower):

        intent = "TICKET"

    # Service monitoring requests
    elif (
        re.search(
            r"\b(status|operational|health|running|availability|outage)\b",
            query_lower
        )
        and re.search(
            r"\b(vpn|email|database|firewall|web)\b",
            query_lower
        )
    ):

        intent = "SYSTEM"

    else:

        prompt = f"""
Classify the request into exactly one category:

SUPPORT
KNOWLEDGE
GENERAL

User request:
{query}

Return only the category name.
"""

        result = llm.invoke(prompt)

        intent = result.content.strip().upper()

        if intent not in {"SUPPORT", "KNOWLEDGE", "GENERAL"}:
            intent = "GENERAL"

    print(f"\n[AGENT] Detected intent: {intent}")

    return {"intent": intent}


# NODE 2: KNOWLEDGE RETRIEVAL
def retrieve_knowledge(state: AgentState):

    query = state["user_query"]

    print("\n[RAG] Searching knowledge base...")

    documents = search_knowledge(query, k=3)

    context = "\n\n".join(
        document.page_content
        for document in documents
    )

    sources = list({
        document.metadata.get("source", "Unknown")
        for document in documents
    })

    print(f"[RAG] Retrieved {len(documents)} documents")

    return {
        "context": context,
        "sources": ", ".join(sources)
    }


# NODE 3: TICKET MANAGEMENT
def execute_ticket_tool(state: AgentState):

    query = state["user_query"]
    query_lower = query.lower()

    print("\n[TOOL] Executing ticket management tool...")

    match = re.search(
        r"\b(?:check|show|get|find)\s+(?:the\s+)?ticket"
        r"(?:\s+status)?\s*#?\s*(\d+)\b",
        query_lower
    )

    if not match:
        match = re.search(
            r"\bticket\s*#?(\d+)\s+status\b",
            query_lower
        )

    if match:

        ticket_id = int(match.group(1))

        ticket = get_ticket_status(ticket_id)

        if "error" in ticket:

            response = f"Ticket #{ticket_id} was not found."

        else:

            response = (
                f"Ticket ID: {ticket['id']}\n"
                f"Title: {ticket['title']}\n"
                f"Priority: {ticket['priority']}\n"
                f"Status: {ticket['status']}\n"
                f"Created: {ticket['created_at']}"
            )

        print("[TOOL] Ticket status retrieved.")

        return {
            "response": response,
            "tool_result": str(ticket)
        }

    if re.search(r"\b(create|raise|open|submit)\b", query_lower):

        if "critical" in query_lower:
            priority = "CRITICAL"
        elif "high" in query_lower:
            priority = "HIGH"
        elif "low" in query_lower:
            priority = "LOW"
        else:
            priority = "MEDIUM"

        ticket = create_ticket(
            title=f"Support Request: {query[:70]}",
            description=query,
            priority=priority
        )

        response = (
            "Support ticket created successfully!\n\n"
            f"Ticket ID: {ticket['ticket_id']}\n"
            f"Priority: {ticket['priority']}\n"
            f"Status: {ticket['status']}"
        )

        print("[TOOL] New ticket created.")

        return {
            "response": response,
            "tool_result": str(ticket)
        }

    return {
        "response": "Please specify whether you want to create or check a ticket."
    }


# NODE 4: SYSTEM MONITORING
def execute_system_tool(state: AgentState):

    query = state["user_query"].lower()

    print("\n[TOOL] Checking system service status...")

    services = [
        "vpn",
        "email",
        "database",
        "firewall",
        "web"
    ]

    selected_service = next(
        (service for service in services if service in query),
        None
    )

    if not selected_service:

        return {
            "response": "Please specify a supported service: VPN, email, database, firewall or web."
        }

    result = check_service_status(selected_service)

    response = (
        f"Service: {result['service'].upper()}\n"
        f"Status: {result['status']}\n"
        f"Details: {result['message']}"
    )

    print("[TOOL] Service status retrieved.")

    return {
        "response": response,
        "tool_result": str(result)
    }


# NODE 5: LLM RESPONSE
def generate_response(state: AgentState):

    query = state["user_query"]

    intent = state.get("intent", "GENERAL")

    context = state.get("context", "")

    if intent in {"SUPPORT", "KNOWLEDGE"}:

        if not context.strip():

            return {
                "response": "No relevant information was found in the knowledge base."
            }

        prompt = f"""
You are AIOpsGenie, an enterprise IT support assistant.

User question:
{query}

Retrieved knowledge:
{context}

Rules:
- Answer using only the retrieved knowledge.
- Do not invent technical information.
- Give clear troubleshooting steps.
- Never request passwords or MFA codes.
- Explain when information is unavailable.

Generate a professional response.
"""

    else:

        prompt = f"""
You are AIOpsGenie, an enterprise AI assistant.

User request:
{query}

Give a concise and professional response.
"""

    result = llm.invoke(prompt)

    return {"response": result.content}


# ROUTING
def route_after_classification(state: AgentState):

    intent = state.get("intent", "GENERAL")

    if intent == "TICKET":
        return "ticket"

    if intent == "SYSTEM":
        return "system"

    if intent in {"SUPPORT", "KNOWLEDGE"}:
        return "knowledge"

    return "general"


# BUILD GRAPH
builder = StateGraph(AgentState)

builder.add_node("classify_query", classify_query)
builder.add_node("retrieve_knowledge", retrieve_knowledge)
builder.add_node("execute_ticket_tool", execute_ticket_tool)
builder.add_node("execute_system_tool", execute_system_tool)
builder.add_node("generate_response", generate_response)

builder.add_edge(START, "classify_query")

builder.add_conditional_edges(
    "classify_query",
    route_after_classification,
    {
        "ticket": "execute_ticket_tool",
        "system": "execute_system_tool",
        "knowledge": "retrieve_knowledge",
        "general": "generate_response"
    }
)

builder.add_edge("retrieve_knowledge", "generate_response")

builder.add_edge("execute_ticket_tool", END)

builder.add_edge("execute_system_tool", END)

builder.add_edge("generate_response", END)

graph = builder.compile()