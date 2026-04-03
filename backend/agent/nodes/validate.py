def validate_node(state: dict):
    answer = state.get("answer", "")
    generation_count = state.get("generation_count", 0)

    # 回答足够完整即通过；最多重试两次后放行，避免图流程卡死。
    validated = len(answer.strip()) >= 30 or generation_count >= 2

    return {**state, "validated": validated}
