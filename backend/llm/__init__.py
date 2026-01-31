"""
LLM Module
"""
from llm.base import BaseLLMClient
from llm.openai_client import OpenAIClient
from llm.anthropic_client import AnthropicClient
from core.config import settings


def create_llm_client(provider: str = None) -> BaseLLMClient:
    """
    Factory function to create LLM client
    
    Args:
        provider: 'openai' or 'anthropic', defaults to settings.default_llm_provider
        
    Returns:
        Configured LLM client instance
    """
    config = settings.get_llm_config(provider)
    
    if config["provider"] == "openai":
        return OpenAIClient(
            api_key=config["api_key"],
            model=config["model"]
        )
    elif config["provider"] == "anthropic":
        return AnthropicClient(
            api_key=config["api_key"],
            model=config["model"]
        )
    else:
        raise ValueError(f"Unknown provider: {config['provider']}")