from typing import TypedDict, List, Optional


class AgentState(TypedDict):
    question: str
    intent: Optional[str]
    documents: Optional[List[str]]
    answer: Optional[str]
    validated: Optional[bool]
    final_answer: Optional[str]
    generation_count: Optional[int]
