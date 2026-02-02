"""ReAct Agent implementation for Code Chat mode.

Implements a state machine that follows the ReAct pattern:
1. PLANNING: LLM generates thought about what to do
2. EXECUTING: Run selected tool
3. OBSERVING: Process tool result
4. Loop until COMPLETED or max iterations

Supports:
- Model tier routing per tool via presets
- Streaming events via AsyncIterator
- Cancellation handling
- Comprehensive error recovery

Author: Backend Architect
Phase: Code Chat Implementation (Task 5)
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import AsyncIterator, Dict, List, Optional, Any
import uuid

import aiofiles

from app.models.code_chat import (
    AgentState,
    CodeChatRequest,
    CodeChatStreamEvent,
    ReActStep,
    ToolCall,
    ToolName,
    PRESETS,
    ToolModelConfig,
)
from app.services.code_chat.tools.base import ToolRegistry
from app.services.code_chat.memory import ConversationMemory, MemoryManager
from app.services.code_chat.context import get_retriever_for_context

logger = logging.getLogger(__name__)


class ReActAgent:
    """LangGraph-inspired ReAct agent with state machine.

    Executes queries through a planning-execution-observation loop
    with configurable model tiers per tool via presets.

    Architecture:
        - State Machine: IDLE → PLANNING → EXECUTING → OBSERVING → ... → COMPLETED
        - Model Selector: Routes to appropriate model tier (fast/balanced/powerful)
        - Tool Registry: Executes tools with validation and error handling
        - Memory Manager: Maintains conversation context across turns

    Attributes:
        model_selector: Service for selecting LLM model instances
        tool_registry: ToolRegistry with registered tools
        memory_manager: MemoryManager for session memories
        _active_sessions: Dict[str, bool] for cancellation tracking

    Example:
        >>> agent = ReActAgent(model_selector, tool_registry, memory_manager)
        >>> request = CodeChatRequest(
        ...     query="Add logging to main.py",
        ...     workspace_path="/workspace/project",
        ...     preset="coding"
        ... )
        >>> async for event in agent.run(request):
        ...     if event.type == "answer":
        ...         print(event.content)
    """

    SYSTEM_PROMPT = """You are an expert coding assistant with access to tools.

Available tools:
{tools_description}

IMPORTANT: Respond in EXACTLY this format:

For taking an action:
Thought: [Your reasoning about what to do next]
Action: tool_name(arg1="value1", arg2="value2")

For providing final answer:
Thought: [Summary of what was done]
Answer: [Complete response to the user]

Rules:
1. Always start with a Thought
2. Use tools to gather information before answering
3. File paths should be relative to the workspace
4. Read files before modifying them
5. When done, provide a clear Answer
6. Only use tools that are listed above
7. Always specify all required parameters for tools
8. Use double quotes for string arguments
"""

    def __init__(
        self,
        model_selector,  # Type hint would be ModelSelector
        tool_registry: ToolRegistry,
        memory_manager: MemoryManager,
    ):
        """Initialize ReAct agent.

        Args:
            model_selector: ModelSelector instance for routing to model tiers
            tool_registry: ToolRegistry with all registered tools
            memory_manager: MemoryManager for conversation memories
        """
        self.model_selector = model_selector
        self.tool_registry = tool_registry
        self.memory_manager = memory_manager
        self._active_sessions: Dict[str, bool] = {}
        self._pending_actions: Dict[
            str, Dict[str, Any]
        ] = {}  # session_id -> action data
        self._action_confirmations: Dict[
            str, Optional[bool]
        ] = {}  # action_id -> approved

        logger.info("ReActAgent initialized")

    async def run(self, request: CodeChatRequest) -> AsyncIterator[CodeChatStreamEvent]:
        """Execute ReAct loop with streaming events.

        Main execution flow:
        1. Generate or use provided session_id
        2. Retrieve or create conversation memory
        3. Optionally retrieve CGRAG context
        4. Enter ReAct loop:
           - PLANNING: LLM generates thought and action
           - EXECUTING: Execute selected tool
           - OBSERVING: Process tool result
           - Loop until answer or max iterations
        5. Save conversation turn to memory
        6. Clean up session

        Args:
            request: CodeChatRequest with query and configuration

        Yields:
            CodeChatStreamEvent objects for real-time updates

        Example:
            >>> async for event in agent.run(request):
            ...     if event.type == "thought":
            ...         print(f"Agent thinking: {event.content}")
            ...     elif event.type == "action":
            ...         print(f"Executing: {event.tool.tool.value}")
        """
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        self._active_sessions[session_id] = True

        logger.info(
            f"Starting ReAct loop for session {session_id} "
            f"(preset: {request.preset}, max_iterations: {request.max_iterations})"
        )

        try:
            # Get or create memory
            memory = await self.memory_manager.get_or_create(
                session_id=session_id,
                workspace_path=request.workspace_path,
                context_name=request.context_name,
            )

            # Retrieve CGRAG context if enabled
            cgrag_context = None
            if request.use_cgrag and request.context_name:
                cgrag_context = await self._get_cgrag_context(
                    request.query, request.context_name
                )
                if cgrag_context:
                    yield CodeChatStreamEvent(type="context", content=cgrag_context)

            # Load preset configuration
            if request.preset not in PRESETS:
                logger.warning(f"Unknown preset '{request.preset}', using 'balanced'")
                preset = PRESETS["balanced"]
            else:
                preset = PRESETS[request.preset]

            # Apply tool overrides if provided
            tool_configs = dict(preset.tool_configs)
            if request.tool_overrides:
                for tool_name, config in request.tool_overrides.items():
                    tool_configs[ToolName(tool_name)] = config

            # ReAct loop state
            steps: List[ReActStep] = []
            iteration = 0
            final_answer = None

            # Main ReAct loop
            while iteration < request.max_iterations:
                # Check for cancellation
                if not self._active_sessions.get(session_id, False):
                    logger.info(f"Session {session_id} cancelled")
                    yield CodeChatStreamEvent(
                        type="cancelled",
                        content="Query execution was cancelled",
                        state=AgentState.CANCELLED,
                    )
                    return

                iteration += 1
                logger.debug(f"ReAct iteration {iteration}/{request.max_iterations}")

                # === PLANNING PHASE ===
                yield CodeChatStreamEvent(
                    type="state", state=AgentState.PLANNING, step_number=iteration
                )

                # Build prompt with context
                prompt = self._build_prompt(
                    query=request.query,
                    steps=steps,
                    memory=memory,
                    cgrag_context=cgrag_context,
                )

                # Call LLM for planning
                try:
                    response = await self._call_llm(
                        prompt=prompt, tier=preset.planning_tier, temperature=0.7
                    )
                except Exception as e:
                    logger.error(f"LLM call failed: {e}", exc_info=True)
                    yield CodeChatStreamEvent(
                        type="error",
                        content=f"Failed to generate plan: {str(e)}",
                        state=AgentState.ERROR,
                    )
                    return

                # Parse LLM response
                thought, action_or_answer, is_answer = self._parse_response(response)

                if not thought:
                    logger.warning(f"Failed to parse LLM response: {response[:200]}")
                    yield CodeChatStreamEvent(
                        type="error",
                        content="Failed to parse agent response. Please try again.",
                        state=AgentState.ERROR,
                    )
                    return

                # Emit thought event
                yield CodeChatStreamEvent(
                    type="thought",
                    content=thought,
                    tier=preset.planning_tier,
                    step_number=iteration,
                )

                # Check if we have final answer
                if is_answer:
                    final_answer = action_or_answer
                    yield CodeChatStreamEvent(
                        type="answer",
                        content=final_answer,
                        state=AgentState.COMPLETED,
                        step_number=iteration,
                    )

                    # Save to memory
                    tools_used = [
                        step.action.tool.value for step in steps if step.action
                    ]
                    memory.add_turn(
                        query=request.query,
                        response=final_answer,
                        tools_used=tools_used,
                    )

                    break

                # Parse action
                tool_call = action_or_answer
                if not tool_call:
                    logger.warning("No valid action or answer found in response")
                    yield CodeChatStreamEvent(
                        type="error",
                        content="Agent failed to select an action. Please try again.",
                        state=AgentState.ERROR,
                    )
                    return

                # === EXECUTING PHASE ===
                yield CodeChatStreamEvent(
                    type="state", state=AgentState.EXECUTING, step_number=iteration
                )

                # Check if tool requires user confirmation (write_file, delete_file)
                requires_confirmation = tool_call.tool in [
                    ToolName.WRITE_FILE,
                    ToolName.DELETE_FILE,
                ]
                action_approved = True  # Default: execute immediately

                if requires_confirmation:
                    # Generate action ID
                    action_id = f"{session_id}_{iteration}"

                    # For write_file, get diff preview before execution
                    diff_preview_data = None
                    if tool_call.tool == ToolName.WRITE_FILE:
                        # Simulate execution to get diff preview without writing
                        try:
                            tool = self.tool_registry.get(tool_call.tool)
                            if tool and hasattr(tool, "_create_diff_preview"):
                                path_arg = tool_call.args.get("path", "")
                                content_arg = tool_call.args.get("content", "")

                                # Validate and resolve path
                                resolved_path = tool._validate_and_resolve(path_arg)

                                # Read original content if exists
                                original_content = None
                                change_type = "create"
                                if resolved_path.exists() and resolved_path.is_file():
                                    async with aiofiles.open(
                                        resolved_path, "r", encoding="utf-8"
                                    ) as f:
                                        original_content = await f.read()
                                    change_type = "modify"

                                # Generate diff preview
                                diff_preview = tool._create_diff_preview(
                                    resolved_path,
                                    original_content,
                                    content_arg,
                                    change_type,
                                )
                                diff_preview_data = diff_preview.model_dump()
                        except Exception as e:
                            logger.warning(f"Could not generate diff preview: {e}")

                    # Store pending action
                    self._pending_actions[action_id] = {
                        "session_id": session_id,
                        "tool_call": tool_call,
                        "diff_preview": diff_preview_data,
                    }

                    # Emit action_pending event
                    yield CodeChatStreamEvent(
                        type="action_pending",
                        content=f"Awaiting confirmation for {tool_call.tool.value}",
                        tool=tool_call,
                        tier=tool_configs.get(tool_call.tool, ToolModelConfig()).tier,
                        step_number=iteration,
                        timestamp=datetime.now().isoformat(),
                        data={
                            "action_id": action_id,
                            "diff_preview": diff_preview_data,
                        },
                    )

                    # Wait for confirmation (with timeout)
                    logger.info(f"Waiting for user confirmation on action {action_id}")
                    timeout = 300  # 5 minute timeout
                    poll_interval = 0.5  # Poll every 500ms
                    elapsed = 0

                    while elapsed < timeout:
                        if action_id in self._action_confirmations:
                            action_approved = self._action_confirmations[action_id]
                            logger.info(
                                f"Action {action_id} {'approved' if action_approved else 'rejected'}"
                            )
                            # Clean up confirmation
                            del self._action_confirmations[action_id]
                            del self._pending_actions[action_id]
                            break

                        # Check for cancellation
                        if not self._active_sessions.get(session_id, False):
                            logger.info(
                                f"Session {session_id} cancelled while waiting for confirmation"
                            )
                            yield CodeChatStreamEvent(
                                type="cancelled", content="Session cancelled by user"
                            )
                            return

                        await asyncio.sleep(poll_interval)
                        elapsed += poll_interval

                    if elapsed >= timeout:
                        logger.warning(f"Confirmation timeout for action {action_id}")
                        yield CodeChatStreamEvent(
                            type="error",
                            content="User confirmation timeout - action skipped",
                            state=AgentState.ERROR,
                        )
                        # Clean up
                        if action_id in self._action_confirmations:
                            del self._action_confirmations[action_id]
                        if action_id in self._pending_actions:
                            del self._pending_actions[action_id]
                        action_approved = False
                else:
                    # No confirmation required, emit normal action event
                    yield CodeChatStreamEvent(
                        type="action",
                        content=f"Executing {tool_call.tool.value}",
                        tool=tool_call,
                        tier=tool_configs.get(tool_call.tool, ToolModelConfig()).tier,
                        step_number=iteration,
                    )

                # Execute tool (only if approved)
                if action_approved:
                    try:
                        result = await self.tool_registry.execute(tool_call)
                    except Exception as e:
                        logger.error(f"Tool execution failed: {e}", exc_info=True)
                        result_error = f"Tool execution error: {str(e)}"
                        result_success = False
                    else:
                        result_error = result.error
                        result_success = result.success
                else:
                    # Action was rejected, create error result
                    result_error = "Action rejected by user"
                    result_success = False

                # === OBSERVING PHASE ===
                yield CodeChatStreamEvent(
                    type="state", state=AgentState.OBSERVING, step_number=iteration
                )

                # Format observation
                if result_success:
                    observation = result.output or "Tool executed successfully"

                    # Emit diff preview if present
                    if result.data and "diff" in result.data:
                        yield CodeChatStreamEvent(
                            type="diff_preview", content=result.data["diff"]
                        )

                    # Track file access in memory
                    if (
                        tool_call.tool == ToolName.READ_FILE
                        and "path" in tool_call.args
                    ):
                        memory.add_file_context(
                            path=tool_call.args["path"],
                            content=result.output or "",
                            max_preview=500,
                        )
                else:
                    observation = f"Error: {result_error or 'Unknown error'}"

                yield CodeChatStreamEvent(
                    type="observation", content=observation, step_number=iteration
                )

                # Record step
                step = ReActStep(
                    step_number=iteration,
                    thought=thought,
                    action=tool_call,
                    observation=observation,
                    state=AgentState.OBSERVING,
                    model_tier=preset.planning_tier,
                    timestamp=datetime.now(),
                )
                steps.append(step)

            # Check if we hit max iterations
            if iteration >= request.max_iterations and not final_answer:
                logger.warning(
                    f"Hit max iterations ({request.max_iterations}) without answer"
                )
                yield CodeChatStreamEvent(
                    type="error",
                    content=f"Maximum iterations ({request.max_iterations}) reached without completing task",
                    state=AgentState.ERROR,
                )

        finally:
            # Clean up session
            if session_id in self._active_sessions:
                del self._active_sessions[session_id]
            logger.info(f"Completed ReAct loop for session {session_id}")

    def cancel(self, session_id: str) -> bool:
        """Cancel an active session.

        Sets the cancellation flag for the session, which will be
        checked on the next iteration of the ReAct loop.

        Args:
            session_id: Session to cancel

        Returns:
            True if session was active and cancelled, False otherwise

        Example:
            >>> agent.cancel("abc123")
            True
        """
        if session_id in self._active_sessions:
            self._active_sessions[session_id] = False
            logger.info(f"Cancelled session {session_id}")
            return True
        return False

    def confirm_action(self, action_id: str, approved: bool) -> bool:
        """Confirm or reject a pending action.

        Called by the frontend to approve or reject file operations
        (write_file, delete_file) that require user confirmation.

        Args:
            action_id: Action identifier (format: session_id_iteration)
            approved: True to approve, False to reject

        Returns:
            True if action was found and confirmed, False otherwise

        Example:
            >>> agent.confirm_action("abc123_1", approved=True)
            True
        """
        if action_id in self._pending_actions:
            self._action_confirmations[action_id] = approved
            logger.info(f"Action {action_id} {'approved' if approved else 'rejected'}")
            return True
        logger.warning(f"Action {action_id} not found in pending actions")
        return False

    def _build_prompt(
        self,
        query: str,
        steps: List[ReActStep],
        memory: ConversationMemory,
        cgrag_context: Optional[str] = None,
    ) -> str:
        """Build the LLM prompt with context and history.

        Combines:
        - System prompt with tool descriptions
        - Conversation memory (workspace, project, recent turns)
        - CGRAG context if available
        - Previous ReAct steps (thought → action → observation)
        - Current query

        Args:
            query: User query
            steps: Previous ReAct steps in current loop
            memory: Conversation memory for context
            cgrag_context: Optional CGRAG retrieved context

        Returns:
            Complete prompt string for LLM
        """
        parts = []

        # System prompt
        tools_desc = self._format_tools_description()
        parts.append(self.SYSTEM_PROMPT.format(tools_description=tools_desc))
        parts.append("")

        # Memory context
        context = memory.get_context_for_prompt(include_file_context=True)
        if context:
            parts.append("## Context")
            parts.append(context)
            parts.append("")

        # CGRAG context
        if cgrag_context:
            parts.append("## Retrieved Context")
            parts.append(cgrag_context)
            parts.append("")

        # Current query
        parts.append("## User Query")
        parts.append(query)
        parts.append("")

        # Previous steps
        if steps:
            parts.append("## Previous Steps")
            for step in steps:
                parts.append(f"Thought: {step.thought}")
                if step.action:
                    args_str = self._format_args(step.action.args)
                    parts.append(f"Action: {step.action.tool.value}({args_str})")
                if step.observation:
                    # Truncate long observations
                    obs = step.observation[:500]
                    if len(step.observation) > 500:
                        obs += "\n... (truncated)"
                    parts.append(f"Observation: {obs}")
                parts.append("")

        # Prompt for next step
        parts.append(
            "What should we do next? Provide a Thought and then either an Action or final Answer."
        )

        return "\n".join(parts)

    def _parse_response(self, response: str) -> tuple:
        """Parse LLM response into thought and action/answer.

        Extracts:
        - Thought: Agent's reasoning
        - Action: tool_name(args) OR
        - Answer: Final response to user

        Args:
            response: Raw LLM response text

        Returns:
            Tuple of (thought, action_or_answer, is_answer) where:
                - thought: str or None
                - action_or_answer: ToolCall or str or None
                - is_answer: bool indicating if this is final answer

        Example:
            >>> thought, action, is_answer = agent._parse_response(response)
            >>> if is_answer:
            ...     print(f"Final answer: {action}")
            >>> else:
            ...     print(f"Tool: {action.tool.value}")
        """
        thought = None
        action_or_answer = None
        is_answer = False

        # Extract thought
        thought_match = re.search(
            r"Thought:\s*(.+?)(?=\n(?:Action|Answer):|$)",
            response,
            re.DOTALL | re.IGNORECASE,
        )
        if thought_match:
            thought = thought_match.group(1).strip()

        # Check for Answer (final response)
        answer_match = re.search(
            r"Answer:\s*(.+?)$", response, re.DOTALL | re.IGNORECASE
        )
        if answer_match:
            action_or_answer = answer_match.group(1).strip()
            is_answer = True
            return thought, action_or_answer, is_answer

        # Check for Action (tool call)
        action_match = re.search(r"Action:\s*(\w+)\((.*?)\)", response, re.IGNORECASE)
        if action_match:
            tool_name = action_match.group(1)
            args_str = action_match.group(2)

            # Parse tool name
            try:
                tool = ToolName(tool_name.lower())
            except ValueError:
                logger.warning(f"Unknown tool name: {tool_name}")
                return thought, None, False

            # Parse arguments
            args = self._parse_args(args_str)

            action_or_answer = ToolCall(tool=tool, args=args)
            return thought, action_or_answer, False

        # No valid action or answer found
        return thought, None, False

    def _parse_args(self, args_str: str) -> Dict[str, Any]:
        """Parse argument string into dictionary.

        Parses format: arg1="value1", arg2="value2"

        Args:
            args_str: Argument string from Action

        Returns:
            Dictionary of argument name -> value

        Example:
            >>> args = agent._parse_args('path="src/main.py", content="print()"')
            >>> assert args["path"] == "src/main.py"
        """
        args = {}

        # Pattern: arg_name="value" or arg_name='value'
        pattern = r'(\w+)\s*=\s*["\']([^"\']*)["\']'

        for match in re.finditer(pattern, args_str):
            arg_name = match.group(1)
            arg_value = match.group(2)
            args[arg_name] = arg_value

        return args

    def _format_args(self, args: Dict[str, Any]) -> str:
        """Format arguments dictionary as string.

        Args:
            args: Dictionary of arguments

        Returns:
            Formatted string: arg1="value1", arg2="value2"

        Example:
            >>> formatted = agent._format_args({"path": "file.txt", "content": "text"})
            >>> # Returns: 'path="file.txt", content="text"'
        """
        parts = []
        for key, value in args.items():
            # Escape double quotes in value
            escaped_value = str(value).replace('"', '\\"')
            parts.append(f'{key}="{escaped_value}"')
        return ", ".join(parts)

    def _format_tools_description(self) -> str:
        """Format tool descriptions for system prompt.

        Returns:
            Formatted markdown list of tools with parameters

        Example:
            >>> desc = agent._format_tools_description()
            >>> # Returns:
            >>> # - read_file(path: str): Read file contents
            >>> #   Required: path
            >>> # ...
        """
        tools = self.tool_registry.list_tools()
        parts = []

        for tool in tools:
            # Tool name and description
            parts.append(f"- {tool['name']}: {tool['description']}")

            # Parameters
            schema = tool["parameters"]
            if "properties" in schema:
                param_names = list(schema["properties"].keys())
                required = schema.get("required", [])

                param_strs = []
                for name in param_names:
                    prop = schema["properties"][name]
                    param_type = prop.get("type", "any")
                    param_strs.append(f"{name}: {param_type}")

                parts.append(f"  Parameters: {', '.join(param_strs)}")
                if required:
                    parts.append(f"  Required: {', '.join(required)}")

            # Confirmation requirement
            if tool["requires_confirmation"]:
                parts.append("  ⚠ Requires user confirmation")

            parts.append("")

        return "\n".join(parts)

    async def _call_llm(self, prompt: str, tier: str, temperature: float = 0.7) -> str:
        """Call LLM with specified tier.

        Uses model_selector to route to appropriate model instance
        based on tier (fast/balanced/powerful).

        Args:
            prompt: Prompt text
            tier: Model tier (fast/balanced/powerful)
            temperature: Sampling temperature (0.0-2.0)

        Returns:
            LLM response text

        Raises:
            Exception: If LLM call fails
        """
        logger.debug(f"Calling LLM (tier: {tier}, temp: {temperature})")

        try:
            # Select model for the tier
            model = await self.model_selector.select_model(tier)
            logger.debug(
                f"Selected model {model.model_id} for tier {tier}",
                extra={"model_id": model.model_id, "tier": tier},
            )

            # Get llama.cpp client for the model
            # We'll need to call the server directly using the model's port
            from app.services.llama_client import LlamaCppClient

            # Construct base URL from model's port
            base_url = f"http://localhost:{model.port}"

            # Create client (we could cache these but for now create per-request)
            client = LlamaCppClient(
                base_url=base_url,
                timeout=120,  # 2 minute timeout for completions
                max_retries=2,
            )

            # Generate completion
            result = await client.generate_completion(
                prompt=prompt,
                max_tokens=2048,
                temperature=temperature,
                stop=None,  # Let model decide when to stop
            )

            # Check for errors
            if result.get("error"):
                raise Exception(f"LLM generation error: {result['error']}")

            # Extract content
            content = result.get("content", "")

            if not content:
                raise Exception("LLM returned empty response")

            logger.info(
                "LLM response generated successfully",
                extra={
                    "tier": tier,
                    "model_id": model.model_id,
                    "tokens_predicted": result.get("tokens_predicted", 0),
                    "tokens_evaluated": result.get("tokens_evaluated", 0),
                    "response_length": len(content),
                },
            )

            return content

        except Exception as e:
            logger.error(f"LLM call failed: {e}", exc_info=True)
            raise

    async def _get_cgrag_context(self, query: str, context_name: str) -> Optional[str]:
        """Retrieve CGRAG context for query.

        Uses the context service to get a retriever and perform
        similarity search for relevant context.

        Args:
            query: User query for retrieval
            context_name: CGRAG index name

        Returns:
            Formatted context string or None if retrieval fails

        Example:
            >>> context = await agent._get_cgrag_context(
            ...     "authentication logic",
            ...     "my_project"
            ... )
            >>> if context:
            ...     print(f"Retrieved {len(context)} chars of context")
        """
        try:
            retriever = await get_retriever_for_context(context_name)
            if not retriever:
                logger.warning(f"No retriever available for context '{context_name}'")
                return None

            # Retrieve relevant chunks (token budget: 4000)
            result = await retriever.retrieve(
                query=query, token_budget=4000, min_relevance=0.7
            )

            if not result.artifacts:
                logger.info("No relevant context found")
                return None

            # Format artifacts as context
            parts = []
            for i, artifact in enumerate(result.artifacts, 1):
                parts.append(
                    f"### Relevant Section {i} (score: {artifact.relevance:.2f})"
                )
                parts.append(artifact.content)
                parts.append("")

            context = "\n".join(parts)
            logger.info(
                f"Retrieved {len(result.artifacts)} artifacts "
                f"({result.tokens_used} tokens) for query"
            )

            return context

        except Exception as e:
            logger.error(f"CGRAG retrieval failed: {e}", exc_info=True)
            return None
