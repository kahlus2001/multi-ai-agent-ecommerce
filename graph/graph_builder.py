from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from graph.state import AgentState
from agents.query_interpreter_agent import QueryInterpreterAgent
from agents.search_agent import SearchAgent
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(temperature=0)

def build_graph(db_path: str) -> StateGraph:
    query_interpreter = QueryInterpreterAgent()
    search_agent = SearchAgent(db_path=db_path)

    builder = StateGraph(AgentState)
    builder.add_node("QueryInterpreter", query_interpreter.run)
    builder.add_node("Search", search_agent.invoke)
    builder.add_edge(START, "QueryInterpreter")
    builder.add_edge("QueryInterpreter", "Search")
    builder.add_edge("Search", END)

    return builder.compile()
