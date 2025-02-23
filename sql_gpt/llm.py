from abc import ABC, abstractmethod
from typing import List

from langchain_core.messages import BaseMessage

from sql_gpt.logging import logger


class LLM(ABC):
    """
    Abstract base class for Language Model (LLM) implementations.
    This class defines the interface for invoking LLMs and provides a factory method
    to get an instance of a specific LLM implementation.
    """

    @abstractmethod
    def invoke(self, prompt: List[BaseMessage]) -> BaseMessage:
        """
        Invokes the LLM with the given prompt.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @classmethod
    def get(cls, llm_name: str, llm_kwargs: dict):
        """
        Returns the LLM instance.
        """
        models = {"openai": OpenAI}
        return models.get(llm_name.lower(), OpenAI)(**llm_kwargs)


class OpenAI(LLM):
    """
    OpenAI LLM implementation.
    """

    def __init__(self, **kwargs):
        from langchain_openai import ChatOpenAI

        self.model = ChatOpenAI(**{**{"model": "gpt-4o-mini"}, **kwargs})
        logger.debug(f"OpenAI LLM initialized with parameters: {kwargs}")

    def invoke(self, prompt: List[BaseMessage]) -> BaseMessage:
        """
        Invokes the LLM with the given prompt.
        """
        return self.model.invoke(prompt)
