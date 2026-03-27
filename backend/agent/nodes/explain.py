def explain_node(state: dict):
    answer = state.get("answer", "")

    # 模拟“少儿友好表达”
    final_answer = f"小朋友你好～😊\n\n{answer}"

    return {**state, "final_answer": final_answer}
