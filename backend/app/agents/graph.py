from langgraph.graph import END, START, StateGraph

from app.agents.educator import educator_node
from app.agents.quant import quant_node
from app.agents.research import research_node
from app.agents.state import AgentState
from app.agents.strategist import strategist_node


def build_agent_graph():
    builder = StateGraph(AgentState)
    builder.add_node("research", research_node)
    builder.add_node("quant", quant_node)
    builder.add_node("strategist", strategist_node)
    builder.add_node("educator", educator_node)

    builder.add_edge(START, "research")
    builder.add_edge("research", "quant")
    builder.add_edge("quant", "strategist")
    builder.add_edge("strategist", "educator")
    builder.add_edge("educator", END)
    return builder.compile()


agent_graph = build_agent_graph()