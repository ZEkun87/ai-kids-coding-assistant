def retrieve_node(state: dict):
    question = state["question"]

    # TODO:
    docs = ["Python for循环语法：for i in range()", "range函数用于生成序列"]

    return {**state, "documents": docs}
