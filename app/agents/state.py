from typing import TypedDict


class AgentState(TypedDict, total=False):

    user_query: str

    intent: str

    context: str

    sources: str

    response: str

    tool_result: str