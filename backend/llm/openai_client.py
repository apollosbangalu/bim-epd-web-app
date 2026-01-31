"""
OpenAI LLM Client Module
Implements LLM interface using OpenAI's GPT models

Features:
- GPT-4 and GPT-3.5-turbo support
- Streaming and non-streaming completions
- Automatic retry with exponential backoff
- Rate limit handling
- Token usage tracking
"""
import logging
from typing import List, Dict, AsyncIterator
from openai import AsyncOpenAI, APIError, RateLimitError, APIConnectionError
from llm.base import BaseLLMClient

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """
    OpenAI API client implementation
    
    Wraps OpenAI's AsyncOpenAI client with retry logic and error handling
    suitable for production use.
    """
    
    def __init__(
        self, 
        api_key: str, 
        model: str = "gpt-4",
        max_retries: int = 3
    ):
        """
        Initialize OpenAI client
        
        Args:
            api_key: OpenAI API key
            model: Model name (gpt-4, gpt-4-turbo-preview, gpt-3.5-turbo)
            max_retries: Maximum number of retry attempts on failures
        """
        self.client = AsyncOpenAI(
            api_key=api_key,
            max_retries=max_retries
        )
        self.model = model
        self.max_retries = max_retries
        
        logger.info(f"Initialized OpenAI client with model: {model}")
    
    async def complete(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = None,
        temperature: float = 0.0,
        max_tokens: int = 4000
    ) -> str:
        """
        Generate completion using OpenAI Chat API
        
        Args:
            messages: Conversation messages
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum response length
            
        Returns:
            Generated text response
            
        Raises:
            APIError: If OpenAI API returns an error
            RateLimitError: If rate limit is exceeded
        """
        # Prepend system prompt if provided
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages
        
        try:
            logger.debug(f"Requesting OpenAI completion with {len(messages)} messages")
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                n=1,  # Generate single completion
                stop=None  # No custom stop sequences
            )
            
            # Extract response text
            completion_text = response.choices[0].message.content
            
            # Log token usage for monitoring
            usage = response.usage
            logger.info(
                f"OpenAI completion: {usage.prompt_tokens} prompt + "
                f"{usage.completion_tokens} completion = {usage.total_tokens} total tokens"
            )
            
            return completion_text
            
        except RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            raise Exception(
                "Rate limit exceeded. Please try again in a moment or upgrade your plan."
            )
        
        except APIConnectionError as e:
            logger.error(f"OpenAI connection error: {e}")
            raise Exception(
                "Could not connect to OpenAI API. Please check your internet connection."
            )
        
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise Exception(f"OpenAI API error: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI completion: {e}", exc_info=True)
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
        
        Yields text chunks in real-time for responsive UI updates.
        
        Args:
            messages: Conversation messages
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum response length
            
        Yields:
            Text chunks as strings
            
        Raises:
            APIError: If OpenAI API returns an error
        """
        # Prepend system prompt if provided
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages
        
        try:
            logger.debug(f"Starting OpenAI streaming completion")
            
            # Create streaming request
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                n=1,
                stop=None,
                stream=True  # Enable streaming
            )
            
            # Stream chunks as they arrive
            chunk_count = 0
            async for chunk in stream:
                # Extract content from chunk
                if chunk.choices[0].delta.content:
                    chunk_text = chunk.choices[0].delta.content
                    chunk_count += 1
                    yield chunk_text
            
            logger.info(f"Streamed {chunk_count} chunks from OpenAI")
            
        except RateLimitError as e:
            logger.error(f"OpenAI rate limit during streaming: {e}")
            raise Exception("Rate limit exceeded during streaming")
        
        except Exception as e:
            logger.error(f"Error during OpenAI streaming: {e}", exc_info=True)
            raise Exception(f"Streaming error: {str(e)}")
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return "openai"
    
    def get_model_name(self) -> str:
        """Get model name"""
        return self.model