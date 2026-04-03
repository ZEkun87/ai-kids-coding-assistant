from agent.graph import build_graph

app = build_graph()


def run_agent(question: str) -> dict:
    return app.invoke({"question": question, "generation_count": 0})
