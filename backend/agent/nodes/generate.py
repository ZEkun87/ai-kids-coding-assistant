def generate_node(state: dict):
    question = state["question"]
    docs = state.get("documents", [])

    context = "\n".join(docs)

    # 简化版（实际替换为LLM调用）
    answer = f"基于知识库：{context}\n\n回答：{question} 的解决方案是..."

    return {**state, "answer": answer}
