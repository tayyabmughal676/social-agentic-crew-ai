"""
CrewAI LinkedIn Post Writer Application

This module ensures proper initialization before CrewAI imports.
"""
import os

# Set dummy OPENAI_API_KEY before CrewAI imports to prevent validation errors
# CrewAI checks for OpenAI even when using Groq, so we provide a dummy key
# This is set early to ensure it's available before any CrewAI imports
if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "sk-not-used-using-groq-instead"


