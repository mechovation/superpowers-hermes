# superpowers-hermes

Process-driven workflow skills for [Hermes Agent](https://github.com/NousResearch/hermes-agent), adapted from [obra/superpowers](https://github.com/obra/superpowers).

## What This Is

A collection of SKILL.md files and a Hermes plugin that enforce systematic workflows: planning before execution, delegation to subagents, verification before completion claims, and documentation of results.

These skills are designed for **any multi-step task** — not just coding. Research, system configuration, data analysis, and creative work all benefit from structured process.

## Skills

| Skill | Purpose |
|-------|---------|
| **brainstorming** | Design-first for any non-trivial task — clarify intent, explore approaches, get approval |
| **dispatching-parallel-agents** | `delegate_task` batch mode for independent parallel work |
| **executing-plans** | Load plan, execute with subagents, checkpoint reviews |
| **finishing-a-development-branch** | Verify, present options, execute, clean up |
| **receiving-code-review** | Technical evaluation over performative agreement |
| **using-git-worktrees** | Isolated workspaces with safety verification |
| **verification-before-completion** | Evidence before assertions — no exceptions |
| **writing-skills** | How to author new Hermes skills |

## Installation

### Docker Build (recommended)

Add to your Hermes `Dockerfile` after `COPY . /opt/hermes`:

```dockerfile
RUN git clone --depth 1 https://github.com/mechovation/superpowers-hermes.git /tmp/superpowers && \
    for skill in /tmp/superpowers/skills/*/; do \
      name=$(basename "$skill"); \
      dest=/opt/hermes/skills/software-development/"$name"; \
      [ -d "$dest" ] || cp -r "$skill" "$dest"; \
    done && \
    cp -r /tmp/superpowers/plugin/* /opt/hermes/plugins/superpowers/ && \
    rm -rf /tmp/superpowers
```

The `[ -d "$dest" ]` guard skips skills that Hermes already has adapted versions of (e.g., `systematic-debugging`, `test-driven-development`, `writing-plans`, `subagent-driven-development`, `requesting-code-review`, `plan`).

### Manual

```bash
# Skills
cp -r skills/* /path/to/hermes-agent/skills/software-development/

# Plugin (optional — provides automatic workflow nudges)
cp -r plugin/* /path/to/hermes-agent/plugins/superpowers/
```

## Plugin

The `plugin/` directory contains a Hermes plugin that hooks into `pre_llm_call` to inject contextual workflow guidance:

- **Planning nudge** — when a multi-step task is detected without an existing plan
- **Delegation nudge** — when context is accumulating (many tool calls without delegation)
- **Verification nudge** — when user signals completion ("done", "merge", "commit")
- **Memory nudge** — reminds to document outcomes after significant work

Configure in `config.yaml`:

```yaml
plugins:
  superpowers:
    tool_call_threshold: 3    # tool calls before nudging
    nudge_first_turn: true    # nudge on first message
    memory_reminders: true    # documentation reminders
```

## Hermes Adaptations

Key differences from the original superpowers:

- **`delegate_task`** instead of Claude Code's `Agent` tool
- **`terminal`**, **`read_file`**, **`search_files`** instead of `Bash`, `Read`, `Grep`
- **`.hermes/plans/`** for plan/spec storage instead of `docs/superpowers/specs/`
- **Memory provider** integration for persisting decisions across sessions
- **No Claude Code-specific references** (`EnterPlanMode`, `TodoWrite`, `Skill` tool)
- **Broader scope** — skills emphasize any multi-step task, not just coding

## Credits

Based on [superpowers](https://github.com/obra/superpowers) by Jesse Vincent. Adapted for Hermes Agent by the mechovation team.

## License

MIT
