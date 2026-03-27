def analyze_node(state: dict):
    question = state["question"]

    # 简化版意图识别（可替换为LLM）
    if "错误" in question or "代码" in question:
        intent = "code_analysis"
    else:
        intent = "qa"

    return {**state, "intent": intent}
