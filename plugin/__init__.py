"""
Superpowers Plugin for Hermes Agent
====================================

Injects process-driven workflow guidance via the ``pre_llm_call`` hook.
On each turn the hook examines conversation state and — when appropriate —
nudges the agent toward brainstorming, planning, delegation, verification,
and documentation.

The guidance is injected as ephemeral user-message context (not persisted
to the session DB), so it doesn't pollute conversation history.

Configuration (config.yaml):
    plugins:
      superpowers:
        # Minimum tool calls in the conversation before nudging toward
        # planning / delegation.  Set to 0 to always nudge.
        tool_call_threshold: 3
        # Whether to nudge on the very first turn of a session.
        nudge_first_turn: true
        # Enable memory / documentation reminders.
        memory_reminders: true
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration defaults
# ---------------------------------------------------------------------------

_DEFAULT_TOOL_CALL_THRESHOLD = 3
_DEFAULT_NUDGE_FIRST_TURN = True
_DEFAULT_MEMORY_REMINDERS = True


def _load_config() -> Dict[str, Any]:
    """Read plugin-specific config from config.yaml."""
    try:
        from hermes_cli.config import load_config
        cfg = load_config()
        return cfg.get("plugins", {}).get("superpowers", {})
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Conversation analysis helpers
# ---------------------------------------------------------------------------

def _count_tool_calls(history: List[Dict[str, Any]]) -> int:
    """Count total tool calls in conversation history."""
    count = 0
    for msg in history:
        if msg.get("role") == "assistant":
            tool_calls = msg.get("tool_calls") or []
            count += len(tool_calls)
    return count


def _has_plan_reference(history: List[Dict[str, Any]]) -> bool:
    """Check if the conversation already references a plan."""
    plan_signals = [
        ".hermes/plans/",
        "writing-plans",
        "executing-plans",
        "brainstorming",
        "## Plan",
        "implementation plan",
    ]
    for msg in history:
        content = msg.get("content", "")
        if isinstance(content, str):
            for signal in plan_signals:
                if signal.lower() in content.lower():
                    return True
    return False


def _is_multi_step_task(user_message: str) -> bool:
    """Heuristic: does the user's message describe a multi-step task?"""
    multi_step_signals = [
        " and then ",
        " after that ",
        " followed by ",
        " steps:",
        " step 1",
        "1.",
        "first,",
        "set up",
        "configure",
        "implement",
        "build",
        "create a",
        "migrate",
        "refactor",
        "deploy",
        "research",
        "investigate",
        "analyze",
        "compare",
    ]
    msg_lower = user_message.lower()
    matches = sum(1 for s in multi_step_signals if s in msg_lower)
    # Require at least 2 signal matches or message is long (>200 chars)
    return matches >= 2 or (matches >= 1 and len(user_message) > 200)


# ---------------------------------------------------------------------------
# Context generation
# ---------------------------------------------------------------------------

_PLANNING_NUDGE = """\
<superpowers-guidance>
This looks like a multi-step task. Before diving into implementation, consider:

1. **Brainstorm first** — use the `brainstorming` skill to clarify requirements, \
explore approaches, and get user approval on a design.
2. **Write a plan** — use the `writing-plans` skill to create a step-by-step plan \
with verification checkpoints.
3. **Delegate independent work** — use `delegate_task` (batch mode) to run \
independent subtasks in parallel, keeping your context clean.
4. **Verify before claiming done** — run verification commands and show evidence \
before marking anything complete.
5. **Document results** — save the plan and outcomes to `.hermes/plans/` and \
persist key decisions to memory for future sessions.

Available skills in `skills/software-development/`:
- brainstorming, writing-plans, executing-plans, subagent-driven-development
- dispatching-parallel-agents, systematic-debugging, test-driven-development
- verification-before-completion, finishing-a-development-branch
- receiving-code-review, requesting-code-review, writing-skills
</superpowers-guidance>"""

_VERIFICATION_NUDGE = """\
<superpowers-guidance>
Before claiming this work is complete, remember the verification-before-completion skill:
- Run the actual verification command (tests, build, check)
- Show the output as evidence
- Only then claim success
Evidence before assertions.
</superpowers-guidance>"""

_MEMORY_NUDGE = """\
<superpowers-guidance>
This task is producing results worth documenting:
- Save the plan and outcomes to `.hermes/plans/` for reference
- Persist key decisions, rationale, and lessons to memory
- If using LLM Wiki, structure findings as wiki entries for retrieval
</superpowers-guidance>"""

_DELEGATION_NUDGE = """\
<superpowers-guidance>
This conversation is accumulating significant context. Consider using \
`delegate_task` to offload independent subtasks to subagents — they get \
isolated context and won't flood your working memory.

Use batch mode for parallel execution:
```python
delegate_task(tasks=[
    {"goal": "...", "context": "...", "toolsets": ["terminal", "file"]},
    {"goal": "...", "context": "...", "toolsets": ["terminal", "file"]},
])
```
</superpowers-guidance>"""


def _build_context(
    user_message: str,
    history: List[Dict[str, Any]],
    is_first_turn: bool,
    config: Dict[str, Any],
) -> Optional[str]:
    """Build the ephemeral context to inject, or None if no nudge needed."""

    threshold = config.get("tool_call_threshold", _DEFAULT_TOOL_CALL_THRESHOLD)
    nudge_first = config.get("nudge_first_turn", _DEFAULT_NUDGE_FIRST_TURN)
    memory_reminders = config.get("memory_reminders", _DEFAULT_MEMORY_REMINDERS)

    tool_count = _count_tool_calls(history)
    has_plan = _has_plan_reference(history)
    is_multi_step = _is_multi_step_task(user_message)

    parts: List[str] = []

    # First turn with a multi-step task: nudge toward planning
    if is_first_turn and nudge_first and is_multi_step and not has_plan:
        parts.append(_PLANNING_NUDGE)

    # Mid-conversation: lots of tool calls without a plan
    elif tool_count >= threshold and not has_plan and is_multi_step:
        parts.append(_PLANNING_NUDGE)

    # Heavy context accumulation: suggest delegation
    if tool_count > threshold * 3 and not has_plan:
        parts.append(_DELEGATION_NUDGE)

    # Completion signals in user message: nudge verification
    completion_signals = [
        "done", "finished", "complete", "ready", "ship it",
        "looks good", "merge", "commit", "push",
    ]
    if any(s in user_message.lower() for s in completion_signals):
        parts.append(_VERIFICATION_NUDGE)

    # Memory/documentation reminder after significant work
    if memory_reminders and tool_count > threshold * 2:
        parts.append(_MEMORY_NUDGE)

    return "\n\n".join(parts) if parts else None


# ---------------------------------------------------------------------------
# Hook callback
# ---------------------------------------------------------------------------

def _on_pre_llm_call(
    session_id: str = "",
    user_message: str = "",
    conversation_history: list | None = None,
    is_first_turn: bool = False,
    model: str = "",
    platform: str = "",
    **kwargs: Any,
) -> Optional[Dict[str, str]]:
    """pre_llm_call hook — returns context dict or None."""
    history = conversation_history or []
    config = _load_config()

    ctx = _build_context(user_message, history, is_first_turn, config)
    if ctx:
        return {"context": ctx}
    return None


def _on_session_start(**kwargs: Any) -> None:
    """on_session_start hook — log activation."""
    logger.info("Superpowers plugin active — process-driven workflow guidance enabled")


# ---------------------------------------------------------------------------
# Plugin entry point
# ---------------------------------------------------------------------------

def register(ctx: Any) -> None:
    """Called by PluginManager during discovery."""
    ctx.register_hook("pre_llm_call", _on_pre_llm_call)
    ctx.register_hook("on_session_start", _on_session_start)
    logger.info("Superpowers plugin registered (pre_llm_call + on_session_start)")
