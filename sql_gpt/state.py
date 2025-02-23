from typing import List

from langchain_core.messages import BaseMessage, SystemMessage
from pydantic import BaseModel, ConfigDict, Field

from sql_gpt.constants import MAX_ROW_LIMIT_SQL_QUERY
from sql_gpt.llm import LLM
from sql_gpt.querier import Querier


class SqlEvent(BaseModel):
    """
    Represents an SQL event with user question, generated SQL text, and execution.

    Attributes:
        user_question (str): User's natural language question.
        sql_text (str): Generated SQL query text.
        sql_result (List[tuple]): Query result.
        ai_response (str): Human-friendly AI response generated from the SQL result.
        error (str): Error message (if any) from SQL execution.
        retry_count (int): Number of retries attempted.
    """

    user_question: str | None = Field(None)
    sql_text: str | None = Field(None)
    sql_result: List[tuple] | None = Field(None)
    ai_response: str | None = Field(None)
    error: str | None = Field(None)
    retry_count: int = 0


class DataLoadEvent(BaseModel):
    """
    Represent Data Load Event with table name, file path, and metadata path.

    Attributes:
        table_name (str): Name of the table to be loaded. If file based table, it is the file name.
        table_columns_description (str): Path to the metadata file.
    """

    table_name: str | None = Field(None)
    table_columns_description: str | None = Field(None)


class ChatState(BaseModel):
    """
    Represents the state of the chat session.

    Attributes:
        messages (List[BaseMessage]): Conversation history.
        sql_event (SqlEvent): Last SQL event.
        data_load_event (DataLoadEvent): Data loader details (if a table is being loaded).
        table_schemas (str): Table schemas and metadata.
        next_step (str): Next step in the LangGraph.
    """

    model: LLM
    querier: Querier
    messages: List[BaseMessage] = [
        SystemMessage(
            content="Welcome to SQL GPT. This tool allows you to ask questions from your data, "
            "by querying the data for you.\n"
            "Please load your data first using the command /load <table_name> "
            "<table_columns_description>.\n"
            "After loading your data, you can ask me questions about your data, and I will query "
            "your data for you for insights.\n"
            "You can quit the program by typing /q."
        )
    ]
    sql_event: SqlEvent = SqlEvent()
    data_load_event: DataLoadEvent = DataLoadEvent()
    table_schemas: str = ""
    next_step: str = "prompter"

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def system_message(self):
        """Define the system message with table schemas."""
        return SystemMessage(
            content=(
                "You are an intelligent assistant that converts natural language questions "
                "into correct DuckDB SQL queries.\n"
                "Your goal is to generate a SQL query by considering the user's intent, "
                "previous interactions, and the table schemas.\n\n"
                "Return format:\n"
                "1. If the intent is clear, generate a complete DuckDB SQL query that satisfies "
                "the request. Return only the SQL query text without any extra commentary. Limit "
                f"query response to {MAX_ROW_LIMIT_SQL_QUERY} rows at most.\n"
                "2. If the intent is ambiguous, ask a follow-up clarification question that "
                "requests additional details. Prefix your clarification question with "
                '"[CLARIFICATION]" as output.\n\n'
                "Instructions:\n"
                "1. Consider the user's intent based on the current question.\n"
                "2. If any previous SQL query resulted in an error, incorporate the error "
                "message and generate a corrected query.\n"
                "3. If previous user questions or clarifications are relevant, include them "
                "in your analysis.\n\n"
                "Table schemas: " + self.table_schemas
            )
        )

    def get_history(self):
        """Return history formatted for OpenAI"""
        return [self.system_message] + self.messages

    def update_history(self, new_message):
        """Append new messages to history"""
        self.messages.append(new_message)
