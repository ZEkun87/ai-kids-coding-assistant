def explain_node(state: dict):
    intent = state.get("intent", "qa")
    answer = state.get("answer", "")

    if intent == "code_analysis":
        final_answer = f"我们一起来找代码里的小问题吧～\n\n{answer}"
    else:
        final_answer = f"小朋友你好～\n\n{answer}"

    return {**state, "final_answer": final_answer}
