from agent.graph import build_graph

app = build_graph()


def run_agent(question: str):
    result = app.invoke({"question": question})
    return result.get("final_answer", "")
