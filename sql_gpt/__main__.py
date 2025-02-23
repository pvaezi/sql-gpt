import argparse
import json

from sql_gpt.constants import MAX_AGENT_RECURSION_LIMIT
from sql_gpt.graph import Graph
from sql_gpt.llm import LLM
from sql_gpt.querier import Querier
from sql_gpt.state import ChatState

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SQL GPT CLI")
    parser.add_argument(
        "-l",
        "--llm",
        type=str,
        required=True,
        help="LLM model to use (e.g., 'openai', etc.)",
    )
    parser.add_argument(
        "--llm-kwargs",
        type=str,
        help="json string of LLM parameters (e.g., '{\"temperature\": 0.5}')",
    )
    parser.add_argument(
        "-e",
        "--executor",
        type=str,
        required=True,
        help="The SQL executor to use (e.g., 'duckdb', etc.)",
    )
    parser.add_argument(
        "--executor-kwargs",
        type=str,
        help='json string of executor parameters (e.g., \'{"database": "my_database.db"}\')',
    )
    args = parser.parse_args()

    # Initialize ChatState with LLM and Querier
    chat_state = ChatState(
        model=LLM.get(args.llm, json.loads(args.llm_kwargs) if args.llm_kwargs else {}),
        querier=Querier.get(
            args.executor,
            json.loads(args.executor_kwargs) if args.executor_kwargs else {},
        ),
    )
    graph = Graph().graph
    graph.invoke(chat_state, config={"recursion_limit": MAX_AGENT_RECURSION_LIMIT})
