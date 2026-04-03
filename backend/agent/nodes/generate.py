def generate_node(state: dict):
    from llm.dashscope_client import call_dashscope

    question = state["question"]
    docs = state.get("documents", [])
    context = "\n".join(docs) if docs else "无参考文档"
    prompt = f"""
你是少儿编程辅导老师，用简单语言回答以下问题：{question}
参考文档：
{context}

要求：1. 适合小学生/初中生理解；2. 语气友好；3. 引导思考而非直接给答案。
"""
    answer = call_dashscope(prompt, temperature=0.7)
    generation_count = state.get("generation_count", 0) + 1
    return {**state, "answer": answer, "generation_count": generation_count}
