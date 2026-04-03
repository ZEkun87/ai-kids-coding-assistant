from langgraph.graph import StateGraph
from agent.state import AgentState

from agent.nodes.analyze import analyze_node
from agent.nodes.code_analyze import code_analyze_node
from agent.nodes.retrieve import retrieve_node
from agent.nodes.generate import generate_node
from agent.nodes.validate import validate_node
from agent.nodes.explain import explain_node


def build_graph():
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("code_analyze", code_analyze_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("generate", generate_node)
    workflow.add_node("validate", validate_node)
    workflow.add_node("explain", explain_node)

    # 设置入口
    workflow.set_entry_point("analyze")

    # analyze 后按意图分流
    def route_by_intent(state):
        return "code_analyze" if state.get("intent") == "code_analysis" else "retrieve"

    workflow.add_conditional_edges("analyze", route_by_intent)

    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", "validate")
    workflow.add_edge("code_analyze", "explain")

    # 条件控制
    def check_valid(state):
        return "explain" if state.get("validated") else "generate"

    workflow.add_conditional_edges("validate", check_valid)

    workflow.add_edge("explain", "__end__")

    return workflow.compile()
