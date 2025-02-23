from abc import abstractmethod
from typing import List

from sql_gpt.logging import logger


class Querier:
    """
    Abstract base class for database query implementations.
    This class defines the interface for connecting to a database and executing SQL queries.
    Subclasses should implement the `connect` and `query` methods.
    """

    def load_table(self, table_name: str) -> str:
        return table_name

    @abstractmethod
    def query(self, sql_text: str) -> List[tuple]:
        """
        Executes the SQL query and returns the result.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @classmethod
    def get(cls, querier_name: str, querier_kwargs: dict) -> "Querier":
        """
        Returns the LLM instance.
        """
        queriers = {"duckdb": DuckdbQuerier}
        return queriers[querier_name.lower()](**querier_kwargs)


class DuckdbQuerier(Querier):
    """
    Querier implementation for tabular files, such as parquet or CSV files.
    This class allows querying tabular data stored in files.
    Uses DuckDB for querying.
    """

    def __init__(self, **kwargs) -> None:
        import duckdb

        self.db_conn = duckdb.connect(**kwargs)
        self.df_counter = 1

    def load_table(self, table_name: str) -> str:
        """
        Builds a table connection
        """
        self.db_conn.execute(
            f"CREATE OR REPLACE TABLE df{self.df_counter} AS SELECT * FROM '{table_name}';"
        )
        logger.debug(f"Table 'df{self.df_counter}' loaded from '{table_name}'.")
        self.df_counter += 1
        return f"df{self.df_counter - 1}"

    def query(self, sql_text: str) -> List[tuple]:
        """
        Executes the SQL query and returns the result.
        """
        return self.db_conn.execute(sql_text).fetchall()
