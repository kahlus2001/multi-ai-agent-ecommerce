from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict):
    user_input: str
    query_params: Dict[str, Any]
    search_results: List[Dict[str, Any]]
    ranked_results: List[Dict[str, Any]]
    final_response: List[Dict[str, Any]]
