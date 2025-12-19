"""
Agent modules for LinkedIn Post Writer

This module ensures proper initialization before CrewAI imports in agents.
"""
import os

# Set dummy OPENAI_API_KEY before CrewAI imports to prevent validation errors
# CrewAI checks for OpenAI even when using Groq, so we provide a dummy key
if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "sk-not-used-using-groq-instead"


