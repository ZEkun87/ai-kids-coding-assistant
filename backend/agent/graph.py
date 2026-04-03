from langgraph.graph import StateGraph
from agent.state import AgentState

from agent.nodes.analyze import analyze_node
from agent.nodes.retrieve import retrieve_node
from agent.nodes.generate import generate_node
from agent.nodes.validate import validate_node
from agent.nodes.explain import explain_node


def build_graph():
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("generate", generate_node)
    workflow.add_node("validate", validate_node)
    workflow.add_node("explain", explain_node)

    # 设置入口
    workflow.set_entry_point("analyze")

    # 定义流程
    workflow.add_edge("analyze", "retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", "validate")

    # 条件控制
    def check_valid(state):
        return "explain" if state.get("validated") else "generate"

    workflow.add_conditional_edges("validate", check_valid)

    workflow.add_edge("explain", "__end__")

    return workflow.compile()
