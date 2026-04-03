def code_analyze_node(state: dict):
    from llm.dashscope_client import call_dashscope

    question = state["question"]
    prompt = f"""
你是少儿编程老师，请分析这段描述中的代码问题并给出讲解：{question}

要求：
1. 先指出主要错误或风险点；
2. 给出可执行的修改建议；
3. 用小学生/初中生能理解的语言解释原因；
4. 给一个简短示例帮助理解。
"""
    answer = call_dashscope(prompt, temperature=0.5)
    return {**state, "answer": answer, "validated": True}
