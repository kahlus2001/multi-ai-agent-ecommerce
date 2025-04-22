from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from graph.state import AgentState
from agents.query_interpreter_agent import QueryInterpreterAgent
from agents.search_agent import SearchAgent
from agents.details_agent import DetailsAgent
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(temperature=0)

def build_graph(db_path: str) -> StateGraph:
    # Initialize all agents
    query_interpreter = QueryInterpreterAgent()
    search_agent = SearchAgent(db_path=db_path, llm=llm)
    details_agent = DetailsAgent(llm=llm)

    # Create the state graph
    builder = StateGraph(AgentState)
    builder.add_node("QueryInterpreter", query_interpreter.run)
    builder.add_node("Search", search_agent.invoke)
    builder.add_node("Details", details_agent.invoke)

    # Connect nodes
    builder.add_edge(START, "QueryInterpreter")
    builder.add_edge("QueryInterpreter", "Search")
    builder.add_edge("Search", "Details")
    builder.add_edge("Details", END)

    return builder.compile()
