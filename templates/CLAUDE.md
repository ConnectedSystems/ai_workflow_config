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
extract-chat.ps1 -Session "$env:APPDATA\claude\projects\<proj>\session.jsonl" -Out "$env:TEMP\chat.txt"
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

## Julia Guidelines

- Package ops: use `pkg_add` / `pkg_rm` via Kaimon — not bare `julia -e 'Pkg.add(...)'`
- Generated code must include explicit type annotations on function signatures
- Test generation via `nim-write`: request `@testset` / `@test` and pass an existing test file as `--context`
- Prefer `using` over `import` unless selective imports are needed for disambiguation
- Numeric/scientific code: pass an existing `.jl` file as `nim-write --context` to match type annotation conventions


---

## Shell Detection & Tool Selection

- **Windows:** use the **PowerShell tool** (never Bash tool). Use `.ps1` scripts, `$env:VAR`, backtick continuation.
- **Linux/macOS:** use the **Bash tool** (never PowerShell tool). Use bash scripts, `$VAR`, backslash continuation.
- Never try Bash first and fall back to PowerShell (or vice versa) — detect the platform once and use the right tool immediately.
- Never hardcode `/home/` or `C:\Users\` — use `~` / `$HOME` / `$env:USERPROFILE`

---

## Worker Delegation Rules

When asked to analyze, summarize, or search across multiple files:
DELEGATE to ask-nim with relevant file paths.

When asked to generate boilerplate, tests, or documentation:
DELEGATE to nim-write with appropriate reference files.

When asked to review session history:
DELEGATE to extract-chat.

## REQUIRED: Pre-Read Checklist (consult before every Read/Grep call)

Before using the Read or Grep tool, answer:
1. Is the file >400 lines? → use `ask-nim`
2. Am I opening 3+ files? → use `ask-nim`
3. Am I searching for specific text over 3+ files? → use `ask-nim`
4. Is this a structural/overview question? → check `graphify-out/GRAPH_REPORT.md` if it
   exists or ask to run `/graphify` if it does not.
5. Am I generating boilerplate? → use `nim-write`

**NEVER read files directly when any of the above is true.**
Only bypass this gate for: logic bugs, architectural decisions, Julia type inference, tasks
needing exact line numbers.

---

## Maintenance

| Event | Action |
|-------|--------|
| After a session | `extract-chat` → `ask-nim` doc pipeline |
| After adding files | `/graphify . --update` (in Claude Code session) |
| Kaimon dropped | Restart `./bin/kaimon`, press `g` |
| Swap worker model | Change `WORKER_MODEL` env var only |
| New Julia domain tools | Add `GateTool(fn)` to Gate `serve()` |

Worker model: `google/gemma-4-31b-it` | API: `https://integrate.api.nvidia.com/v1`
