def validate_node(state: dict):
    answer = state.get("answer", "")

    # 简单校验逻辑
    if len(answer) < 10:
        validated = False
    else:
        validated = True

    return {**state, "validated": validated}
