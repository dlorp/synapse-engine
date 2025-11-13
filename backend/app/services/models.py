"""Model management service for health checking and load balancing.

This module provides the ModelManager class which orchestrates multiple
llama.cpp model instances, performs health checks, and implements load
balancing across model tiers.
"""

import asyncio
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.core.exceptions import (
    ModelNotFoundError,
    ModelUnavailableError,
    NoModelsAvailableError,
    QueryTimeoutError
)
from app.core.logging import get_logger
from app.models.config import ModelConfig
from app.models.model import ModelState, ModelStatus, SystemStatus
from app.services.llama_client import LlamaCppClient


class ModelManager:
    """Manager for orchestrating multiple llama.cpp model instances.

    Responsibilities:
    - Health checking all configured models
    - Load balancing across FAST tier instances
    - Model selection based on tier and availability
    - Tracking model metrics and state

    Attributes:
        models: Dictionary mapping model IDs to their configurations
        _clients: Dictionary of LlamaCppClient instances per model
        _model_states: Current state tracking for each model
        _health_task: Background task for periodic health checks
        _request_counts: Request counter per model for load balancing
        _logger: Logger instance
    """

    def __init__(self, models: Dict[str, ModelConfig]) -> None:
        """Initialize ModelManager with model configurations.

        Args:
            models: Dictionary mapping model IDs to ModelConfig instances
        """
        self.models = models
        self._clients: Dict[str, LlamaCppClient] = {}
        self._model_states: Dict[str, Dict] = {}
        self._health_task: Optional[asyncio.Task] = None
        self._request_counts: Dict[str, int] = defaultdict(int)
        self._running = False
        self._logger = get_logger(__name__)

        # Initialize clients and state for each model
        for model_id, config in models.items():
            # Create llama.cpp client
            self._clients[model_id] = LlamaCppClient(
                base_url=config.url,
                timeout=config.timeout_seconds,
                max_retries=config.max_retries,
                retry_delay=config.retry_delay_seconds
            )

            # Initialize state tracking
            self._model_states[model_id] = {
                'state': ModelState.OFFLINE,
                'is_healthy': False,
                'consecutive_failures': 0,
                'last_check': datetime.now(timezone.utc),
                'latency_ms': 0.0,
                'error_message': None,
                'request_count': 0,
                'error_count': 0,
                'total_response_time_ms': 0.0,
                'uptime_seconds': 0,
                'start_time': datetime.now(timezone.utc),
                # Time-series metrics (20 datapoints each for sparklines)
                'tokens_per_second_history': deque(maxlen=20),
                'memory_gb_history': deque(maxlen=20),
                'latency_ms_history': deque(maxlen=20),
                'last_tokens_per_second': 0.0,
                'last_memory_gb': 0.0
            }

        self._logger.info(
            f"ModelManager initialized with {len(models)} models",
            extra={'model_ids': list(models.keys())}
        )

    async def start(self) -> None:
        """Start the ModelManager and begin background health checking.

        Initiates periodic health checks for all configured models.
        Should be called during application startup.
        """
        if self._running:
            self._logger.warning("ModelManager already running")
            return

        self._running = True
        self._logger.info("Starting ModelManager health checking")

        # Perform initial health check
        await self.check_all_models()

        # Start background health checking task
        self._health_task = asyncio.create_task(self._health_check_loop())

        self._logger.info("ModelManager started successfully")

    async def stop(self) -> None:
        """Stop the ModelManager and cleanup resources.

        Cancels background tasks and closes all HTTP clients.
        Should be called during application shutdown.
        """
        if not self._running:
            return

        self._running = False
        self._logger.info("Stopping ModelManager")

        # Cancel health check task
        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass

        # Close all clients
        for client in self._clients.values():
            await client.close()

        self._logger.info("ModelManager stopped")

    async def _health_check_loop(self) -> None:
        """Background loop for periodic health checking.

        Runs continuously until ModelManager is stopped, checking
        model health at configured intervals.
        """
        while self._running:
            try:
                # Wait for the health check interval (use minimum from all models)
                if self.models:
                    min_interval = min(
                        config.health_check_interval
                        for config in self.models.values()
                    )
                else:
                    # No models configured - use default interval
                    min_interval = 10.0

                await asyncio.sleep(min_interval)

                # Perform health checks
                await self.check_all_models()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(
                    f"Error in health check loop: {e}",
                    exc_info=True
                )
                # Continue running even if health check fails
                await asyncio.sleep(10)

    async def check_all_models(self) -> None:
        """Check health of all models in parallel.

        Updates internal state based on health check results.
        Detects and logs state changes (healthy -> unhealthy, etc.).
        """
        self._logger.debug("Checking health of all models")

        # Run health checks in parallel
        health_checks = [
            self._check_model_health(model_id)
            for model_id in self.models.keys()
        ]

        await asyncio.gather(*health_checks, return_exceptions=True)

    async def _check_model_health(self, model_id: str) -> None:
        """Check health of a single model.

        Args:
            model_id: Model identifier to check
        """
        client = self._clients[model_id]
        state = self._model_states[model_id]
        previous_state = state['state']

        # Perform health check
        health_result = await client.health_check()

        # Update state based on health check result
        now = datetime.now(timezone.utc)
        state['last_check'] = now
        state['latency_ms'] = health_result['latency_ms']

        server_status = health_result['status']

        if server_status == 'ok':
            # Model is healthy
            state['is_healthy'] = True
            state['consecutive_failures'] = 0
            state['error_message'] = None

            # Determine state based on activity
            if state['request_count'] > 0:
                state['state'] = ModelState.ACTIVE
            else:
                state['state'] = ModelState.IDLE

            # Collect time-series metrics from healthy model
            try:
                stats = await client.get_stats()

                # Update tokens per second metrics
                tokens_per_second = stats.get('tokens_per_second', 0.0)
                state['last_tokens_per_second'] = tokens_per_second
                state['tokens_per_second_history'].append(tokens_per_second)

                # Update memory usage metrics
                memory_gb = stats.get('memory_used_gb', 0.0)
                state['last_memory_gb'] = memory_gb
                state['memory_gb_history'].append(memory_gb)

                # Add latency to history
                state['latency_ms_history'].append(health_result['latency_ms'])

            except Exception as e:
                # Stats collection failed, append zeros to maintain buffer size
                self._logger.debug(
                    f"Failed to collect stats for {model_id}: {e}",
                    extra={'model_id': model_id, 'error': str(e)}
                )
                state['tokens_per_second_history'].append(0.0)
                state['memory_gb_history'].append(0.0)
                state['latency_ms_history'].append(0.0)

        elif server_status == 'loading_model':
            # Model is starting up
            state['is_healthy'] = False
            state['state'] = ModelState.PROCESSING
            state['error_message'] = 'Model is loading'

            # Append zeros for loading models
            state['tokens_per_second_history'].append(0.0)
            state['memory_gb_history'].append(0.0)
            state['latency_ms_history'].append(0.0)

        else:
            # Model is unhealthy or unreachable
            state['is_healthy'] = False
            state['consecutive_failures'] += 1
            state['error_message'] = health_result.get('error', 'Unknown error')

            if server_status == 'unreachable':
                state['state'] = ModelState.OFFLINE
            else:
                state['state'] = ModelState.ERROR

            # Append zeros for unhealthy models to maintain buffer size
            state['tokens_per_second_history'].append(0.0)
            state['memory_gb_history'].append(0.0)
            state['latency_ms_history'].append(0.0)

        # Calculate uptime
        state['uptime_seconds'] = int((now - state['start_time']).total_seconds())

        # Log state changes
        if previous_state != state['state']:
            self._logger.info(
                f"Model {model_id} state changed: {previous_state.value} -> {state['state'].value}",
                extra={
                    'model_id': model_id,
                    'previous_state': previous_state.value,
                    'new_state': state['state'].value,
                    'is_healthy': state['is_healthy']
                }
            )

    async def get_status(self) -> SystemStatus:
        """Get current status of all models and system metrics.

        Returns:
            SystemStatus with all model statuses and aggregate metrics

        Example:
            >>> manager = ModelManager(config.models)
            >>> await manager.start()
            >>> status = await manager.get_status()
            >>> print(f"Active queries: {status.active_queries}")
        """
        now = datetime.now(timezone.utc)

        # Build ModelStatus for each model
        model_statuses: List[ModelStatus] = []

        for model_id, config in self.models.items():
            state = self._model_states[model_id]

            # Calculate average response time
            avg_response_time = 0.0
            if state['request_count'] > 0:
                avg_response_time = (
                    state['total_response_time_ms'] / state['request_count']
                )

            # Get memory statistics from llama.cpp if model is healthy
            memory_used_mb = 0
            memory_total_mb = 8000  # Default fallback

            if state['is_healthy'] and state['state'] != ModelState.OFFLINE:
                try:
                    client = self._clients[model_id]
                    stats = await client.get_stats()

                    if not stats.get('error'):
                        # Get memory usage in GB and convert to MB
                        memory_used_gb = stats.get('memory_used_gb', 0.0)
                        memory_used_mb = int(memory_used_gb * 1024)

                        # Estimate total memory based on tier
                        # Q2 models: ~2-3GB, Q3: ~4-5GB, Q4: ~6-8GB
                        tier_memory_map = {
                            'fast': 3072,      # 3GB in MB
                            'balanced': 5120,  # 5GB in MB
                            'powerful': 8192   # 8GB in MB
                        }
                        memory_total_mb = tier_memory_map.get(config.tier.lower(), 8000)
                except Exception as e:
                    self._logger.debug(
                        f"Failed to get memory stats for {model_id}: {e}",
                        extra={'model_id': model_id}
                    )

            model_status = ModelStatus(
                id=model_id,
                name=config.name,
                tier=config.tier,
                port=config.port,
                state=state['state'],
                memory_used=memory_used_mb,
                memory_total=memory_total_mb,
                request_count=state['request_count'],
                avg_response_time=round(avg_response_time, 2),
                last_active=state['last_check'],
                error_count=state['error_count'],
                uptime_seconds=state['uptime_seconds']
            )

            model_statuses.append(model_status)

        # Calculate aggregate metrics
        total_vram_gb = 16.0  # Mock value
        total_vram_used_gb = sum(m.memory_used for m in model_statuses) / 1024.0

        # Get cache hit rate from cache metrics service
        cache_hit_rate = 0.0
        try:
            from app.services.cache_metrics import get_cache_metrics
            cache_metrics = get_cache_metrics()
            cache_hit_rate = cache_metrics.get_hit_rate()
        except RuntimeError:
            # Cache metrics not initialized - use default 0.0
            pass
        except Exception as e:
            self._logger.warning(
                f"Failed to get cache hit rate: {e}",
                extra={'error': str(e)}
            )

        active_queries = sum(
            1 for m in model_statuses
            if m.state == ModelState.PROCESSING
        )
        total_requests = sum(m.request_count for m in model_statuses)

        return SystemStatus(
            models=model_statuses,
            total_vram_gb=total_vram_gb,
            total_vram_used_gb=round(total_vram_used_gb, 2),
            cache_hit_rate=cache_hit_rate,
            active_queries=active_queries,
            total_requests=total_requests,
            timestamp=now
        )

    async def select_model(self, tier: str) -> str:
        """Select best available model for the specified tier.

        For FAST tier, implements round-robin load balancing across
        healthy instances. For BALANCED/POWERFUL, returns the single instance.

        Args:
            tier: Model tier (fast, balanced, or powerful)

        Returns:
            Model ID of the selected model

        Raises:
            NoModelsAvailableError: If no healthy models available in tier

        Example:
            >>> model_id = await manager.select_model("fast")
            >>> print(f"Selected: {model_id}")
            'qwen_8b_fast'
        """
        # Find all healthy models in the requested tier
        available_models = [
            model_id
            for model_id, config in self.models.items()
            if config.tier == tier and self._model_states[model_id]['is_healthy']
        ]

        if not available_models:
            self._logger.error(
                f"No healthy models available in tier {tier}",
                extra={'tier': tier}
            )
            raise NoModelsAvailableError(
                tier=tier,
                details={
                    'available_tiers': list(set(
                        config.tier
                        for model_id, config in self.models.items()
                        if self._model_states[model_id]['is_healthy']
                    ))
                }
            )

        # For single model in tier, return it
        if len(available_models) == 1:
            return available_models[0]

        # For multiple models (FAST tier), use round-robin based on request counts
        # Select model with lowest request count
        selected_model = min(
            available_models,
            key=lambda m: self._request_counts[m]
        )

        self._logger.debug(
            f"Selected model {selected_model} for tier {tier}",
            extra={
                'tier': tier,
                'model_id': selected_model,
                'request_counts': {
                    m: self._request_counts[m] for m in available_models
                }
            }
        )

        return selected_model

    async def call_model(
        self,
        model_id: str,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> Dict:
        """Generate completion from a specific model.

        Args:
            model_id: Model identifier
            prompt: Input prompt text
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Dictionary with completion results

        Raises:
            ModelNotFoundError: If model_id doesn't exist
            ModelUnavailableError: If model exists but is unhealthy
            QueryTimeoutError: If request exceeds timeout

        Example:
            >>> result = await manager.call_model(
            ...     "qwen_8b_fast",
            ...     "What is Python?",
            ...     max_tokens=100
            ... )
            >>> print(result["content"])
        """
        # Validate model exists
        if model_id not in self.models:
            raise ModelNotFoundError(
                model_id=model_id,
                details={'available_models': list(self.models.keys())}
            )

        # Check model health
        state = self._model_states[model_id]
        if not state['is_healthy']:
            raise ModelUnavailableError(
                model_id=model_id,
                reason=state['error_message'] or 'Model is not healthy',
                details={'state': state['state'].value}
            )

        # Update state to processing
        previous_state = state['state']
        state['state'] = ModelState.PROCESSING

        # Track request
        self._request_counts[model_id] += 1
        start_time = asyncio.get_event_loop().time()

        try:
            # Call model
            client = self._clients[model_id]
            result = await client.generate_completion(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )

            # Calculate response time
            elapsed_ms = (asyncio.get_event_loop().time() - start_time) * 1000

            # Update metrics
            state['request_count'] += 1
            state['total_response_time_ms'] += elapsed_ms

            if result.get('error'):
                state['error_count'] += 1
                self._logger.warning(
                    f"Model {model_id} returned error: {result['error']}",
                    extra={'model_id': model_id, 'error': result['error']}
                )

            self._logger.info(
                f"Model {model_id} completed request",
                extra={
                    'model_id': model_id,
                    'elapsed_ms': round(elapsed_ms, 2),
                    'tokens_generated': result.get('tokens_predicted', 0)
                }
            )

            return result

        except asyncio.TimeoutError:
            state['error_count'] += 1
            config = self.models[model_id]
            raise QueryTimeoutError(
                model_id=model_id,
                timeout_seconds=config.timeout_seconds
            )

        except Exception as e:
            state['error_count'] += 1
            self._logger.error(
                f"Error calling model {model_id}: {e}",
                extra={'model_id': model_id, 'error': str(e)},
                exc_info=True
            )
            raise

        finally:
            # Restore state (will be updated by next health check)
            if state['is_healthy']:
                state['state'] = previous_state if previous_state != ModelState.PROCESSING else ModelState.ACTIVE
