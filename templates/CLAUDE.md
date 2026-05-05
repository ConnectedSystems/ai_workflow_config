# CLAUDE.md — AI Workflow Config

## Token Budget: Three-Tier Delegation

| Tier | Tool | Use when |
|------|------|----------|
| 1 | **Worker LLM** (`ask-nim`) | Reading >400 lines, 3+ files at once, generating boilerplate |
| 2 | **Graphify** (`graphify query`) | Any question about codebase structure |
| 3 | **Kaimon MCP** *(if available)* | Any Julia execution, type inspection, or debugging |

**Default:** use Claude directly only for tasks under ~2 000 tokens, architectural decisions, subtle bugs, or Julia type/dispatch reasoning.

---

## Tier 1: Worker LLM Commands

```bash
# Read and summarise files (returns summary only — do NOT read source directly)
ask-nim --paths file1 file2 --question "What does X do?"

# Generate boilerplate (review output; make surgical edits)
nim-write --spec "description" --context style_ref_file --target output_file

# Extract session transcript before doc updates
extract-chat ~/.claude/projects/<proj>/session.jsonl -o /tmp/chat.txt
ask-nim --paths /tmp/chat.txt docs/current.md --question "What doc edits are needed?"
```

**Windows (PowerShell):**
```powershell
ask-nim.ps1  -Paths file1,file2  -Question "What does X do?"
nim-write.ps1 -Spec "..." -Context ref -Target out
extract-chat.ps1 -Session "$$env:APPDATA\claude\projects\<proj>\session.jsonl" -Out "$$env:TEMP\chat.txt"
```

**Corpus ordering:** always put file paths before the question — enables prefix caching on repeated calls.

**Do NOT delegate to worker:** debugging logic bugs, architectural decisions, Julia type inference, cases needing exact line numbers for edits.

---

## Tier 2: Graphify (codebase graph)

graphify is a Claude Code skill — invoke it with `/graphify` inside a Claude Code session, not from the terminal.

```
/graphify .                                          # build / refresh the knowledge graph
/graphify . --update                                 # re-extract only changed files
/graphify query "what connects solver to data loading?"
/graphify explain "SomeModule"
/graphify path "InputParser" "OutputWriter"
```

Read `graphify-out/GRAPH_REPORT.md` at the start of any codebase exploration task. Never grep source files for structural questions.

---

## Tier 3: Kaimon MCP Tools (Julia live session — use only if Kaimon is running)

Before using any Kaimon tool, confirm the MCP server is active. If unavailable, fall back to reading source files directly or using the worker LLM.

| Task | Tool |
|------|------|
| Run code | `ex` |
| Inspect type | `type_info` |
| Find methods | `search_methods` |
| Expand macro | `macro_expand` |
| Check IR / types | `code_typed`, `code_lowered` |
| Run tests | `run_tests` |
| Profile | `profile_code` |
| Packages | `pkg_add`, `pkg_rm` |
| Debug | `start_debug_session`, `debug_step_*`, `debug_continue` |

If Kaimon drops: restart `./bin/kaimon`, press `g` to reconnect Gate.

$JULIA_SECTION
---

## Shell Detection

- Windows (`$$IsWindows` true): use `.ps1` scripts, `$$env:VAR`, backtick continuation
- Linux/macOS: use bash scripts, `$$VAR`, backslash continuation
- Never hardcode `/home/` or `C:\Users\` — use `~` / `$$HOME` / `$$env:USERPROFILE`

---

## Maintenance

| Event | Action |
|-------|--------|
| After a session | `extract-chat` → `ask-nim` doc pipeline |
| After adding files | `/graphify . --update` (in Claude Code session) |
| Kaimon dropped | Restart `./bin/kaimon`, press `g` |
| Swap worker model | Change `WORKER_MODEL` env var only |
| New Julia domain tools | Add `GateTool(fn)` to Gate `serve()` |

Worker model: `${WORKER_MODEL}` | API: `${WORKER_BASE_URL}`
