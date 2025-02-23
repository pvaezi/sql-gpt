from langgraph.graph import END, START, StateGraph

from sql_gpt.agents import (
    build_query,
    execute_query,
    load_table,
    post_execution,
    prompter,
    route_to_next_step,
)
from sql_gpt.state import ChatState


class Graph:
    """
    This class represents the state graph for the SQL GPT agent.
    It initializes the graph with nodes and edges, defining the flow of the agent's operations.
    """

    def __init__(self) -> None:
        graph_builder = StateGraph(ChatState)
        graph_builder.add_node("prompter", prompter)
        graph_builder.add_node("load_table", load_table)
        graph_builder.add_node("build_query", build_query)
        graph_builder.add_node("execute_query", execute_query)
        graph_builder.add_node("post_execution", post_execution)

        # Define edges between nodes.
        graph_builder.add_edge(START, "prompter")
        graph_builder.add_conditional_edges(
            "prompter",
            route_to_next_step,
            {
                "prompter": "prompter",
                "load_table": "load_table",
                "build_query": "build_query",
                "END": END,
            },
        )
        graph_builder.add_edge("load_table", "prompter")
        graph_builder.add_conditional_edges(
            "build_query",
            route_to_next_step,
            {"prompter": "prompter", "execute_query": "execute_query"},
        )
        graph_builder.add_conditional_edges(
            "execute_query",
            route_to_next_step,
            {
                "build_query": "build_query",
                "post_execution": "post_execution",
                "prompter": "prompter",
            },
        )
        graph_builder.add_edge("post_execution", "prompter")

        self.graph = graph_builder.compile()

    def visualize(self) -> None:
        """
        Visualize the Lang Graph using the Mermaid syntax.
        """
        import io

        from PIL import Image

        image = Image.open(io.BytesIO(self.graph.get_graph().draw_mermaid_png()))
        image.show()
