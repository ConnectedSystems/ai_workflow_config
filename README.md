# ai_workflow_config

One-shot setup for a three-tier Claude Code token-budget strategy:

| Tier | Tool | Purpose |
|------|------|---------|
| 1 | Worker LLM (`ask-nim`) | Bulk file reading, boilerplate generation |
| 2 | Graphify | Codebase knowledge graph navigation |
| 3 | Kaimon.jl MCP | Live Julia REPL, type inspection, debugging |

The worker LLM can be any model on any OpenAI-compatible endpoint. Defaults are NVIDIA NIM + Gemma, but swapping providers only requires changing two env vars.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) — used for all Python venv and package management

## Quick start

```bash
uv run install.py --api-key YOUR_KEY
```

This will:
1. Clone and configure `claude-coworker-model` (uv venv + deps)
2. Set `WORKER_API_KEY`, `WORKER_BASE_URL`, `WORKER_MODEL`, `COWORKER_DIR` as persistent env vars
3. Install `ask-nim`, `nim-write`, `extract-chat` wrappers to `~/bin`
4. Install Graphify (`uv tool install graphifyy`) and register it with your AI platform
5. Generate `CLAUDE.md`, `.claude/settings.json`, `.claude/mcp_config.json`, `.claudeignore`
6. Run a health check

## Options

```
--api-key             Worker LLM API key (required unless --generate-only)
--worker-url          OpenAI-compatible base URL  [https://integrate.api.nvidia.com/v1]
--worker-model        Model identifier            [google/gemma-3-27b-it]
--bin-dir             Script install dir          [~/bin]
--coworker-dir        Where to clone coworker model  [~/claude-coworker-model]
--output-dir          Where to write CLAUDE.md etc.  [cwd]
--project-type        julia | general             [julia]
--graphify-platform   AI platform to register graphify with  [claude]
--generate-only       Skip env vars and script install; only write config files
--check               Health check against installed tiers and exit
```

Supported `--graphify-platform` values:

| Value | Platform |
|-------|----------|
| `claude` | Claude Code (default) |
| `codex` | OpenAI Codex |
| `opencode` | OpenCode |
| `copilot` | GitHub Copilot CLI |
| `vscode` | VS Code Copilot Chat |
| `aider` | Aider |
| `claw` | OpenClaw |
| `droid` | Factory Droid |
| `trae` | Trae |
| `trae-cn` | Trae CN |
| `gemini` | Gemini CLI |
| `hermes` | Hermes |
| `kiro` | Kiro IDE/CLI |
| `pi` | Pi coding agent |
| `cursor` | Cursor |
| `antigravity` | Google Antigravity |

**Swapping providers** — only env vars need changing, no reinstall required:

```bash
# Example: switch to OpenRouter
export WORKER_API_KEY="sk-or-..."
export WORKER_BASE_URL="https://openrouter.ai/api/v1"
export WORKER_MODEL="anthropic/claude-haiku-4-5"
```

## After running

Generated files are written to `outputs/` (gitignored). Copy them to their destinations:

1. **`outputs/CLAUDE.md`** — copy to `~/.claude/CLAUDE.md` (user-wide) or your project root.
2. **`outputs/.claude/settings.json`** — copy to your project's `.claude/`; pre-authorises wrapper scripts so Claude Code won't prompt on every call.
3. **`outputs/.claude/mcp_config.json`** — merge into your Claude Code MCP settings after Kaimon is running.
4. **`outputs/.claudeignore`** — copy to your project root.

### Still needed (manual)

```bash
# Run Claude skill for each project - builds the knowledge graph
/graphify .

# Kaimon (Julia 1.12+ required)
git clone https://github.com/kahliburke/Kaimon.jl ~/Kaimon.jl
cd ~/Kaimon.jl && ./bin/kaimon
# Press 'i' in the dashboard to write MCP config
# Press 'g' to add Gate snippet to ~/.julia/config/startup.jl
```

## Repo structure

```
pyproject.toml           # minimal project file — enables uv run install.py
install.py               # main installer (stdlib only)
templates/
  CLAUDE.md              # parameterised CLAUDE.md template (≤100 lines)
  CLAUDE_julia_section.md
  .claudeignore          # sensible defaults
  claude_settings.json   # Claude Code permissions + hooks template
  mcp_config.json        # Kaimon + Graphify MCP server registration
scripts/
  ask-nim / ask-nim.ps1
  nim-write / nim-write.ps1
  extract-chat / extract-chat.ps1
```
