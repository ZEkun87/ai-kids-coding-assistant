from functools import lru_cache


@lru_cache(maxsize=256)
def _classify_intent_with_llm(question: str) -> str:
    from llm.dashscope_client import call_dashscope

    classify_prompt = f"""
请判断下面用户问题更适合哪种处理类型，只返回一个标签：
- qa：知识问答、概念解释、学习建议、练习思路
- code_analysis：代码报错、调试、语法错误、代码优化

用户问题：{question}

只输出 qa 或 code_analysis，不要输出其他内容。
"""
    result = (
        call_dashscope(classify_prompt, temperature=0.0, max_tokens=10).strip().lower()
    )
    return "code_analysis" if "code_analysis" in result else "qa"


def analyze_node(state: dict):
    question = state["question"]
    normalized = question.lower()

    # 先用关键词规则做快速判断，减少一次 LLM 调用。
    # 注意：普通问题中出现“代码”不一定是调试需求。
    code_keywords = ["错误", "报错", "bug", "debug", "异常", "traceback", "语法"]
    if any(keyword in normalized for keyword in code_keywords) or "def " in normalized:
        return {**state, "intent": "code_analysis"}

    try:
        intent = _classify_intent_with_llm(question)
    except Exception:
        # 分类失败时回退到 qa，保证主流程可用。
        intent = "qa"

    return {**state, "intent": intent}
