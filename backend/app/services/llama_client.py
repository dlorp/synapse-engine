"""HTTP client wrapper for llama.cpp server API.

This module provides an async HTTP client for communicating with llama.cpp
model servers, including health checks and completion generation with retry logic.
"""

import asyncio
from typing import Dict, Any, Optional

import httpx

from app.core.logging import get_logger


class LlamaCppClient:
    """Async HTTP client for llama.cpp server API.

    Provides methods for health checking and completion generation with
    automatic retries and linear backoff for transient failures.

    Attributes:
        base_url: Base URL of the llama.cpp server (e.g., http://localhost:8080)
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts for failed requests
        retry_delay: Delay in seconds between retry attempts (linear backoff)
        _client: Underlying httpx.AsyncClient instance
        _logger: Logger instance for structured logging
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = 10,
        max_retries: int = 3,
        retry_delay: int = 2
    ) -> None:
        """Initialize llama.cpp client.

        Args:
            base_url: Base URL of the llama.cpp server
            timeout: Request timeout in seconds (default: 10)
            max_retries: Maximum retry attempts (default: 3)
            retry_delay: Delay in seconds between retries (default: 2)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Create async HTTP client with timeout configuration
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=5.0),
            follow_redirects=True
        )

        self._logger = get_logger(__name__)

    async def close(self) -> None:
        """Close the HTTP client and cleanup resources.

        Should be called during application shutdown to properly
        close all connections.
        """
        await self._client.aclose()

    async def health_check(self) -> Dict[str, Any]:
        """Check health status of the llama.cpp server.

        Calls the /health endpoint to verify server availability and status.

        Returns:
            Dictionary with health check results:
                - status: Server status (ok, loading_model, error, unreachable)
                - latency_ms: Request latency in milliseconds
                - error: Optional error message if health check failed

        Example:
            >>> client = LlamaCppClient("http://localhost:8080")
            >>> health = await client.health_check()
            >>> print(health["status"])
            'ok'
        """
        start_time = asyncio.get_event_loop().time()

        try:
            response = await self._client.get(
                f"{self.base_url}/health",
                timeout=5.0  # Shorter timeout for health checks
            )

            elapsed_ms = (asyncio.get_event_loop().time() - start_time) * 1000

            # Parse response
            if response.status_code == 200:
                data = response.json()
                server_status = data.get('status', 'unknown')

                return {
                    'status': server_status,
                    'latency_ms': elapsed_ms,
                    'error': None
                }
            else:
                self._logger.warning(
                    f"Health check returned non-200 status",
                    extra={
                        'base_url': self.base_url,
                        'status_code': response.status_code
                    }
                )
                return {
                    'status': 'error',
                    'latency_ms': elapsed_ms,
                    'error': f"HTTP {response.status_code}"
                }

        except httpx.TimeoutException:
            elapsed_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            self._logger.warning(
                f"Health check timeout",
                extra={'base_url': self.base_url}
            )
            return {
                'status': 'unreachable',
                'latency_ms': elapsed_ms,
                'error': 'Timeout'
            }

        except httpx.ConnectError as e:
            elapsed_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            self._logger.warning(
                f"Health check connection failed",
                extra={'base_url': self.base_url, 'error': str(e)}
            )
            return {
                'status': 'unreachable',
                'latency_ms': elapsed_ms,
                'error': f'Connection failed: {str(e)}'
            }

        except Exception as e:
            elapsed_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            self._logger.error(
                f"Health check unexpected error",
                extra={'base_url': self.base_url, 'error': str(e)},
                exc_info=True
            )
            return {
                'status': 'error',
                'latency_ms': elapsed_ms,
                'error': str(e)
            }

    async def generate_completion(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        stop: Optional[list[str]] = None
    ) -> Dict[str, Any]:
        """Generate text completion from the llama.cpp server.

        Sends a completion request with automatic retries on transient failures.
        Uses linear backoff between retries.

        Args:
            prompt: Input prompt text
            max_tokens: Maximum tokens to generate (default: 512)
            temperature: Sampling temperature 0.0-2.0 (default: 0.7)
            stop: Optional list of stop sequences

        Returns:
            Dictionary with completion results:
                - content: Generated text
                - tokens_predicted: Number of tokens generated
                - tokens_evaluated: Number of input tokens processed
                - error: Optional error message if generation failed

        Raises:
            httpx.HTTPError: If all retry attempts fail

        Example:
            >>> client = LlamaCppClient("http://localhost:8080")
            >>> result = await client.generate_completion(
            ...     prompt="What is Python?",
            ...     max_tokens=100
            ... )
            >>> print(result["content"])
            'Python is a high-level programming language...'
        """
        request_body = {
            'prompt': prompt,
            'n_predict': max_tokens,
            'temperature': temperature,
            'stop': stop or [],
            'stream': False  # We don't support streaming yet
        }

        last_exception: Optional[Exception] = None

        # Retry loop with linear backoff
        # Note: max_retries=0 means 1 attempt (no retries), max_retries=1 means 2 attempts (1 retry), etc.
        for attempt in range(self.max_retries + 1):
            try:
                self._logger.debug(
                    f"Completion request attempt {attempt + 1}/{self.max_retries + 1}",
                    extra={
                        'base_url': self.base_url,
                        'prompt_length': len(prompt),
                        'max_tokens': max_tokens
                    }
                )

                response = await self._client.post(
                    f"{self.base_url}/completion",
                    json=request_body,
                    timeout=self.timeout
                )

                # Success case
                if response.status_code == 200:
                    data = response.json()

                    self._logger.info(
                        f"Completion generated successfully",
                        extra={
                            'base_url': self.base_url,
                            'tokens_predicted': data.get('tokens_predicted', 0),
                            'tokens_evaluated': data.get('tokens_evaluated', 0)
                        }
                    )

                    return {
                        'content': data.get('content', ''),
                        'tokens_predicted': data.get('tokens_predicted', 0),
                        'tokens_evaluated': data.get('tokens_evaluated', 0),
                        'error': None
                    }

                # Non-200 response
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    self._logger.warning(
                        f"Completion request failed",
                        extra={
                            'base_url': self.base_url,
                            'status_code': response.status_code,
                            'attempt': attempt + 1
                        }
                    )

                    # Don't retry on client errors (4xx)
                    if 400 <= response.status_code < 500:
                        return {
                            'content': '',
                            'tokens_predicted': 0,
                            'tokens_evaluated': 0,
                            'error': error_msg
                        }

                    last_exception = httpx.HTTPStatusError(
                        error_msg,
                        request=response.request,
                        response=response
                    )

            except httpx.TimeoutException as e:
                self._logger.warning(
                    f"Completion request timeout",
                    extra={
                        'base_url': self.base_url,
                        'attempt': attempt + 1,
                        'timeout': self.timeout
                    }
                )
                last_exception = e

            except httpx.ConnectError as e:
                self._logger.warning(
                    f"Completion request connection failed",
                    extra={
                        'base_url': self.base_url,
                        'attempt': attempt + 1,
                        'error': str(e)
                    }
                )
                last_exception = e

            except Exception as e:
                self._logger.error(
                    f"Completion request unexpected error",
                    extra={
                        'base_url': self.base_url,
                        'attempt': attempt + 1,
                        'error': str(e)
                    },
                    exc_info=True
                )
                last_exception = e

            # Linear backoff before retry
            if attempt < self.max_retries:
                self._logger.debug(
                    f"Retrying after {self.retry_delay}s delay",
                    extra={'attempt': attempt + 1}
                )
                await asyncio.sleep(self.retry_delay)

        # All retries exhausted
        self._logger.error(
            f"Completion request failed after {self.max_retries + 1} attempts",
            extra={'base_url': self.base_url}
        )

        return {
            'content': '',
            'tokens_predicted': 0,
            'tokens_evaluated': 0,
            'error': f'Failed after {self.max_retries} attempts: {str(last_exception)}'
        }
