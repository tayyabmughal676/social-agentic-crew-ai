"""
LLM setup utilities - Alternative solutions for handling CrewAI OpenAI validation
"""
import os
import warnings
from contextlib import contextmanager
from typing import Optional
from langchain_groq import ChatGroq


from crewai import LLM

def get_llm() -> LLM:
    """
    Get the configured LLM instance.
    Currently configured for local LM Studio.
    """
    return LLM(
        model="openai/zai-org/glm-4.6v-flash",
        base_url="http://localhost:1234/v1",
        api_key="lm-studio",
        timeout=120,
        max_tokens=2048,
        temperature=0.7
    )


@contextmanager
def suppress_openai_warning():
    """
    Context manager to suppress OpenAI API key warnings during CrewAI imports.
    
    Usage:
        with suppress_openai_warning():
            from crewai import Crew, Task, LLM
    """
    # Set dummy key temporarily
    original_key = os.environ.get("OPENAI_API_KEY")
    if not original_key:
        os.environ["OPENAI_API_KEY"] = "sk-dummy"
    
    # Suppress warnings
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        warnings.filterwarnings("ignore", message=".*OPENAI_API_KEY.*")
        warnings.filterwarnings("ignore", message=".*Error importing native provider.*")
        try:
            yield
        finally:
            # Restore original key if it wasn't set
            if not original_key:
                os.environ.pop("OPENAI_API_KEY", None)


def setup_crewai_environment():
    """
    Setup environment variables before CrewAI imports.
    This is the simplest solution - just sets a dummy key.
    """
    if not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = "sk-not-used-using-groq-instead"

