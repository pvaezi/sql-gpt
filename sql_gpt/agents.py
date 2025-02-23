from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from sql_gpt.constants import MAX_RETRY_SQL_GENERATION
from sql_gpt.logging import log, logger
from sql_gpt.state import ChatState, DataLoadEvent, SqlEvent


def prompter(state: ChatState) -> ChatState:
    """
    Gets user input and processes special commands (/q to quit, /load to load data).
    Updates the state with the new user question or additional clarification details.
    """
    # print last message content
    logger.critical(state.messages[-1].content)
    # get user input prompt
    user_input = input(">>> User prompt (/q to quit, /load to load data): ")
    # if requesting to quit, set next step to END
    if user_input.lower().startswith("/q"):
        state.next_step = "END"
    # if requesting to load data, parse the command and set the next step to load_table
    elif user_input.lower().startswith("/load"):
        try:
            # Expected format: /load table_name table_columns_description
            _, table_name, table_columns_description = user_input.split()
            state.data_load_event = DataLoadEvent(
                table_name=table_name,
                table_columns_description=table_columns_description,
            )
            state.next_step = "load_table"
        except Exception:
            logger.exception(
                "Error parsing load command. Expected usage: /load <table_name> "
                "<table_columns_description>"
            )
            state.update_history(
                SystemMessage(
                    content="Please load your data first using the command /load <table_name> "
                    "<table_columns_description>"
                )
            )
            state.next_step = "prompter"
    # asking question without loading data should be short-circuited
    elif not state.table_schemas:
        # If no table schemas are loaded, inform the user.
        state.update_history(
            SystemMessage(
                content="Please load your data first using the command /load <table_name> "
                "<table_columns_description>"
            )
        )
        state.next_step = "prompter"
    # otherwise it is a user question to parse
    else:
        # This new input could be a new question or clarification details.
        state.update_history(HumanMessage(content=user_input))
        # Reset the SQL event state.
        state.sql_event = SqlEvent(user_question=user_input)
        state.next_step = "build_query"
    return state


@log
def load_table(state: ChatState) -> ChatState:
    """
    If applicable load files to tables, reads table column metadata, and appends the table schema
    to the state.
    """
    table_name = state.data_load_event.table_name
    table_columns_description = state.data_load_event.table_columns_description
    state.next_step = "prompter"

    try:
        table_name = state.querier.load_table(table_name)  # type: ignore
    except Exception as e:
        logger.exception("Error loading data into DuckDB. Please check the file path and format.")
        state.update_history(SystemMessage(content=f"Loading data failed with error:{str(e)}"))
        return state

    # Load metadata
    try:
        with open(table_columns_description, "r") as fp:  # type: ignore
            meta = fp.read()
    except Exception as e:
        logger.exception("Error loading data into DuckDB. Please check the file path and format.")
        state.update_history(
            SystemMessage(content=f"Loading table column schemas failed with error:{str(e)}")
        )
        return state

    # Append the loaded table info to the state.
    table_info = f"Table: {table_name}\n{meta}\n"
    state.table_schemas += table_info
    # Update conversation history.
    state.update_history(
        SystemMessage(content=f"Table '{table_name}' loaded with metadata:\n{table_info}")
    )
    return state


@log
def build_query(state: ChatState) -> ChatState:
    """
    Builds a DuckDB SQL query by analyzing the user question, previous interactions,
    table schemas, and any error messages from previous attempts.

    The prompt instructs the LLM to:
      - Deeply analyze the user's intent based on the current question and interaction history.
      - Generate a complete DuckDB SQL query if the intent is clear.
      - If the intent is ambiguous, ask for additional details in a free-form clarification
        message.
      - If a previous SQL query resulted in an error, incorporate the error message and correct
        the query.

    Returns only the SQL query text (or a clarification question) without extra commentary.
    """
    llm_response = state.model.invoke(state.get_history())

    # If a clarification is needed, ask for more details.
    if llm_response.content.startswith("[CLARIFICATION]"):
        clarification_text = llm_response.content.split("[CLARIFICATION]")[1].strip()
        clarification_msg = (
            "Your question is ambiguous. "
            f"Please provide additional details: {clarification_text}"
        )
        state.update_history(AIMessage(content=clarification_msg))
        state.next_step = "prompter"
        return state

    query_text = llm_response.content.replace("```sql", "").replace("```", "").strip()
    logger.debug(query_text)
    state.update_history(AIMessage(content=query_text))
    state.sql_event.sql_text = query_text
    state.next_step = "execute_query"
    return state


@log
def execute_query(state: ChatState) -> ChatState:
    """
    Executes the generated SQL query. If execution fails, the error message is captured,
    and the state is updated to trigger query regeneration.
    """
    try:
        result = state.querier.query(state.sql_event.sql_text)  # type: ignore
        state.sql_event.sql_result = result
        state.sql_event.error = None
        state.next_step = "post_execution"
    except Exception as e:
        state.sql_event.sql_result = None
        state.sql_event.error = str(e)
        state.sql_event.retry_count += 1
        logger.exception("SQL execution failed with error: %s", str(e))
        if state.sql_event.retry_count > MAX_RETRY_SQL_GENERATION:
            state.update_history(
                AIMessage(
                    content="Sorry, I was unable to execute the user requests "
                    "after several attempts."
                )
            )
            state.next_step = "prompter"
        else:
            state.update_history(
                AIMessage(
                    content=(f"Generated SQL query raised this error:\n{state.sql_event.error}\n")
                )
            )
            state.next_step = "build_query"
    return state


@log
def post_execution(state: ChatState) -> ChatState:
    """
    Processes the SQL query result and generates a concise, human-readable summary.
    """
    sql_results = AIMessage(content=f"SQL results are: {state.sql_event.sql_result}")
    state.update_history(sql_results)
    interpret_msgs = [
        SystemMessage(
            content="You are an intelligent assistant that summarizes SQL query results based on "
            f"given table schemas. \nTable Schemas: {state.table_schemas}"
        ),
        HumanMessage(content=state.sql_event.user_question),
        AIMessage(content=f"Generated SQL Text is: {state.sql_event.sql_text}"),
        sql_results,
    ]
    llm_response = state.model.invoke(interpret_msgs)
    state.update_history(AIMessage(content=llm_response.content))
    state.sql_event.ai_response = llm_response.content
    state.next_step = "prompter"
    return state


def route_to_next_step(state: ChatState) -> str:
    """Determines the next lang graph step based on the current state."""
    logger.debug(f"Routing to next step: {state.next_step}")
    return state.next_step
