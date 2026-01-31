"""
Anthropic LLM Client Module
Implements LLM interface using Anthropic's Claude models

Features:
- Claude 3.5 Sonnet and other Claude models
- Streaming and non-streaming completions
- Automatic retry logic
- Token usage tracking
- Error handling
"""
import logging
from typing import List, Dict, AsyncIterator
from anthropic import (
    AsyncAnthropic, 
    APIError, 
    RateLimitError, 
    APIConnectionError
)
from llm.base import BaseLLMClient

logger = logging.getLogger(__name__)


class AnthropicClient(BaseLLMClient):
    """
    Anthropic API client implementation
    
    Wraps Anthropic's AsyncAnthropic client with production-ready
    error handling and retry logic.
    """
    
    def __init__(
        self, 
        api_key: str, 
        model: str = "claude-3-5-sonnet-20241022",
        max_retries: int = 3
    ):
        """
        Initialize Anthropic client
        
        Args:
            api_key: Anthropic API key
            model: Model name (claude-3-5-sonnet-20241022, etc.)
            max_retries: Maximum retry attempts on failures
        """
        self.client = AsyncAnthropic(
            api_key=api_key,
            max_retries=max_retries
        )
        self.model = model
        self.max_retries = max_retries
        
        logger.info(f"Initialized Anthropic client with model: {model}")
    
    async def complete(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = None,
        temperature: float = 0.0,
        max_tokens: int = 4000
    ) -> str:
        """
        Generate completion using Anthropic Messages API
        
        Args:
            messages: Conversation messages
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum response length
            
        Returns:
            Generated text response
            
        Raises:
            APIError: If Anthropic API returns an error
            RateLimitError: If rate limit is exceeded
        """
        try:
            logger.debug(f"Requesting Anthropic completion with {len(messages)} messages")
            
            # Call Anthropic API
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt or "",  # System prompt separate from messages
                messages=messages
            )
            
            # Extract response text from content blocks
            # Anthropic returns list of content blocks
            completion_text = ""
            for block in response.content:
                if block.type == "text":
                    completion_text += block.text
            
            # Log token usage
            logger.info(
                f"Anthropic completion: {response.usage.input_tokens} input + "
                f"{response.usage.output_tokens} output tokens"
            )
            
            return completion_text
            
        except RateLimitError as e:
            logger.error(f"Anthropic rate limit exceeded: {e}")
            raise Exception(
                "Rate limit exceeded. Please try again in a moment or upgrade your plan."
            )
        
        except APIConnectionError as e:
            logger.error(f"Anthropic connection error: {e}")
            raise Exception(
                "Could not connect to Anthropic API. Please check your internet connection."
            )
        
        except APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise Exception(f"Anthropic API error: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error in Anthropic completion: {e}", exc_info=True)
            raise Exception(f"Unexpected error: {str(e)}")
    
    async def stream_complete(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = None,
        temperature: float = 0.0,
        max_tokens: int = 4000
    ) -> AsyncIterator[str]:
        """
        Stream completion tokens as they're generated
        
        Provides real-time text generation for responsive UIs.
        
        Args:
            messages: Conversation messages
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum response length
            
        Yields:
            Text chunks as strings
            
        Raises:
            APIError: If Anthropic API returns an error
        """
        try:
            logger.debug("Starting Anthropic streaming completion")
            
            # Create streaming request using context manager
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt or "",
                messages=messages
            ) as stream:
                # Stream text chunks as they arrive
                chunk_count = 0
                async for text in stream.text_stream:
                    chunk_count += 1
                    yield text
                
                logger.info(f"Streamed {chunk_count} chunks from Anthropic")
            
        except RateLimitError as e:
            logger.error(f"Anthropic rate limit during streaming: {e}")
            raise Exception("Rate limit exceeded during streaming")
        
        except Exception as e:
            logger.error(f"Error during Anthropic streaming: {e}", exc_info=True)
            raise Exception(f"Streaming error: {str(e)}")
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return "anthropic"
    
    def get_model_name(self) -> str:
        """Get model name"""
        return self.model