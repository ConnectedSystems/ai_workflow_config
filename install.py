#!/usr/bin/env python3
"""
One-shot setup for ai_workflow_config.

Usage:
    uv run install.py --api-key YOUR_KEY [options]
    uv run install.py --check             # health-check only
    uv run install.py --generate-only     # generate files without touching env/scripts
"""

import argparse
import os
import platform
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from string import Template

REPO_DIR     = Path(__file__).parent
TEMPLATES    = REPO_DIR / "templates"
SCRIPTS_DIR  = REPO_DIR / "scripts"
COWORKER_URL = "https://github.com/imkunal007219/claude-coworker-model.git"

IS_WINDOWS = platform.system() == "Windows"

# Args passed to `graphify` for each platform's install command.
# All platforms use: graphify install [--platform <name>]
GRAPHIFY_PLATFORMS: dict[str, list[str]] = {
    "claude":      ["install"],
    "codex":       ["install", "--platform", "codex"],
    "opencode":    ["install", "--platform", "opencode"],
    "copilot":     ["install", "--platform", "copilot"],
    "vscode":      ["install", "--platform", "vscode"],
    "aider":       ["install", "--platform", "aider"],
    "claw":        ["install", "--platform", "claw"],
    "droid":       ["install", "--platform", "droid"],
    "trae":        ["install", "--platform", "trae"],
    "trae-cn":     ["install", "--platform", "trae-cn"],
    "gemini":      ["install", "--platform", "gemini"],
    "hermes":      ["install", "--platform", "hermes"],
    "kiro":        ["install", "--platform", "kiro"],
    "pi":          ["install", "--platform", "pi"],
    "cursor":      ["install", "--platform", "cursor"],
    "antigravity": ["install", "--platform", "antigravity"],
}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Install ai_workflow_config tools")
    p.add_argument("--api-key",       default=os.environ.get("WORKER_API_KEY", ""),
                   help="Worker LLM API key")
    p.add_argument("--worker-url",    default=os.environ.get("WORKER_BASE_URL", "https://integrate.api.nvidia.com/v1"),
                   help="OpenAI-compatible base URL for the worker LLM")
    p.add_argument("--worker-model",  default=os.environ.get("WORKER_MODEL", "google/gemma-3-27b-it"),
                   help="Model identifier string (any model supported by the endpoint)")
    p.add_argument("--bin-dir",       default=Path.home() / "bin",
                   type=Path, help="Directory for wrapper scripts (added to PATH)")
    p.add_argument("--coworker-dir",  default=Path.home() / "claude-coworker-model",
                   type=Path, help="Where to clone/find claude-coworker-model")
    p.add_argument("--output-dir",    default=REPO_DIR / "outputs",
                   type=Path, help="Where to write CLAUDE.md and settings files")
    p.add_argument("--project-type",  choices=["julia", "general"], default="julia",
                   help="Adjusts CLAUDE.md template sections")
    p.add_argument("--graphify-platform", default="claude",
                   choices=sorted(GRAPHIFY_PLATFORMS),
                   metavar="{" + ",".join(sorted(GRAPHIFY_PLATFORMS)) + "}",
                   help="AI platform to register graphify with (default: claude)")
    p.add_argument("--check",         action="store_true",
                   help="Run health check against installed tiers and exit")
    p.add_argument("--generate-only", action="store_true",
                   help="Only write CLAUDE.md / settings; skip env/script install")
    return p.parse_args()


# ---------------------------------------------------------------------------
# Coworker model
# ---------------------------------------------------------------------------

def check_uv() -> None:
    if not shutil.which("uv"):
        print("ERROR: 'uv' not found. Install it from https://docs.astral.sh/uv/")
        sys.exit(1)


def setup_coworker(coworker_dir: Path) -> None:
    if not (coworker_dir / ".git").exists():
        print(f"[1/5] Cloning coworker model → {coworker_dir}")
        subprocess.run(["git", "clone", COWORKER_URL, str(coworker_dir)], check=True)
    else:
        print(f"[1/5] Coworker model already at {coworker_dir}, skipping clone")

    venv = coworker_dir / ".venv"
    python = venv / ("Scripts" if IS_WINDOWS else "bin") / ("python.exe" if IS_WINDOWS else "python")

    if not python.exists():
        print("      Creating venv with uv …")
        subprocess.run(["uv", "venv", ".venv"], cwd=coworker_dir, check=True)
        req = coworker_dir / "requirements.txt"
        if req.exists():
            subprocess.run(["uv", "pip", "install", "-r", "requirements.txt"],
                           cwd=coworker_dir, check=True)
    else:
        print("      Venv already exists, skipping")


# ---------------------------------------------------------------------------
# Environment variables
# ---------------------------------------------------------------------------

def set_env_persistent(name: str, value: str) -> None:
    """Set a user-level persistent environment variable on the current OS."""
    if IS_WINDOWS:
        subprocess.run(
            ["powershell", "-Command",
             f'[System.Environment]::SetEnvironmentVariable("{name}", "{value}", "User")'],
            check=True
        )
    else:
        # Also set in current process so subsequent steps can use it
        os.environ[name] = value


def append_unix_rc(lines: list[str]) -> None:
    rc_files = []
    for rc in (".bashrc", ".zshrc", ".profile"):
        p = Path.home() / rc
        if p.exists():
            rc_files.append(p)
    if not rc_files:
        rc_files = [Path.home() / ".bashrc"]

    block = "\n# --- ai_workflow_config ---\n" + "\n".join(lines) + "\n# ---\n"
    for rc in rc_files:
        content = rc.read_text()
        if "ai_workflow_config" in content:
            print(f"      {rc.name}: block already present, skipping")
        else:
            rc.write_text(content + block)
            print(f"      Appended to {rc}")


def install_env_vars(args: argparse.Namespace) -> None:
    print("[2/5] Setting persistent environment variables …")
    env_vars = {
        "WORKER_API_KEY":   args.api_key,
        "WORKER_BASE_URL":  args.worker_url,
        "WORKER_MODEL":     args.worker_model,
        "COWORKER_DIR":     str(args.coworker_dir),
    }
    if IS_WINDOWS:
        for name, value in env_vars.items():
            set_env_persistent(name, value)
            print(f"      SET (User) {name}={value}")
        # Ensure bin dir is on PATH
        _add_to_path_windows(args.bin_dir)
    else:
        export_lines = [f'export {k}="{v}"' for k, v in env_vars.items()]
        export_lines.append(f'export PATH="{args.bin_dir}:$PATH"')
        append_unix_rc(export_lines)

    # Also set in this process so health check works immediately
    for k, v in env_vars.items():
        os.environ[k] = v


def _add_to_path_windows(bin_dir: Path) -> None:
    import winreg  # only imported on Windows
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ)
    try:
        current_path, _ = winreg.QueryValueEx(key, "PATH")
    except FileNotFoundError:
        current_path = ""
    winreg.CloseKey(key)

    bin_str = str(bin_dir)
    if bin_str not in current_path:
        new_path = f"{bin_str};{current_path}" if current_path else bin_str
        subprocess.run(
            ["powershell", "-Command",
             f'[System.Environment]::SetEnvironmentVariable("PATH", "{new_path}", "User")'],
            check=True
        )
        print(f"      Added {bin_dir} to User PATH")


# ---------------------------------------------------------------------------
# Script installation
# ---------------------------------------------------------------------------

def install_scripts(bin_dir: Path, coworker_dir: Path) -> None:
    print(f"[3/5] Installing wrapper scripts → {bin_dir}")
    bin_dir.mkdir(parents=True, exist_ok=True)

    src_scripts = list(SCRIPTS_DIR.glob("*"))
    for src in src_scripts:
        if IS_WINDOWS and not src.suffix == ".ps1":
            continue
        if not IS_WINDOWS and src.suffix == ".ps1":
            continue
        dst = bin_dir / src.name
        shutil.copy2(src, dst)
        if not IS_WINDOWS:
            dst.chmod(dst.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        print(f"      {src.name} → {dst}")


# ---------------------------------------------------------------------------
# Graphify
# ---------------------------------------------------------------------------

def setup_graphify(graphify_platform: str) -> None:
    print(f"[4/6] Setting up Graphify (platform: {graphify_platform}) …")

    if not shutil.which("graphify"):
        print("      graphify not found — installing via uv tool …")
        subprocess.run(["uv", "tool", "install", "graphifyy"], check=True)
    else:
        print("      graphify already installed, skipping")

    subprocess.run(["graphify"] + GRAPHIFY_PLATFORMS[graphify_platform], check=True)
    print(f"      graphify registered for {graphify_platform}")

    # The installed skill uses `pip install graphifyy` for its self-check; replace with uv.
    skill_paths = [
        Path.home() / ".claude" / "skills" / "graphify" / "SKILL.md",
        Path(os.environ.get("APPDATA", "")) / "claude" / "skills" / "graphify" / "SKILL.md",
    ]
    for skill in skill_paths:
        if skill.exists():
            original = skill.read_text(encoding="utf-8")
            patched = original.replace("pip install graphifyy", "uv pip install graphifyy")
            if patched != original:
                skill.write_text(patched, encoding="utf-8")
                print(f"      Patched pip → uv in {skill}")
            else:
                print(f"      {skill}: no pip reference found, skipping patch")
            break

    print("      Open Claude Code in each project and type: /graphify .")


# ---------------------------------------------------------------------------
# File generation
# ---------------------------------------------------------------------------

def _load_template(name: str) -> Template:
    return Template((TEMPLATES / name).read_text(encoding="utf-8"))


def generate_claude_md(output_dir: Path, args: argparse.Namespace) -> None:
    tmpl = _load_template("CLAUDE.md")
    subs = dict(
        WORKER_MODEL   = args.worker_model,
        WORKER_BASE_URL = args.worker_url,
        PROJECT_TYPE   = args.project_type,
        JULIA_SECTION  = _load_julia_section() if args.project_type == "julia" else "",
    )
    out = output_dir / "CLAUDE.md"
    out.write_text(tmpl.substitute(subs), encoding="utf-8")
    print(f"      Generated {out}")


def _load_julia_section() -> str:
    path = TEMPLATES / "CLAUDE_julia_section.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def generate_settings(output_dir: Path, args: argparse.Namespace) -> None:
    tmpl = _load_template("claude_settings.json")
    bin_dir_escaped = str(args.bin_dir).replace("\\", "\\\\")
    out = output_dir / ".claude" / "settings.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(tmpl.substitute(BIN_DIR=bin_dir_escaped), encoding="utf-8")
    print(f"      Generated {out}")


def generate_mcp_config(output_dir: Path) -> None:
    tmpl = _load_template("mcp_config.json")
    out = output_dir / ".claude" / "mcp_config.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        print(f"      {out} already exists — skipping (edit manually to merge)")
        return
    out.write_text(tmpl.substitute(), encoding="utf-8")
    print(f"      Generated {out}")


def copy_claudeignore(output_dir: Path) -> None:
    src = TEMPLATES / ".claudeignore"
    dst = output_dir / ".claudeignore"
    if dst.exists():
        print(f"      .claudeignore already exists — skipping")
        return
    shutil.copy2(src, dst)
    print(f"      Copied .claudeignore → {dst}")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def health_check(bin_dir: Path) -> int:
    print("\n=== Health Check ===")
    failures = 0

    # Tier 1 — worker LLM wrapper
    script = "ask-nim.ps1" if IS_WINDOWS else "ask-nim"
    wrapper = bin_dir / script
    if wrapper.exists():
        print(f"[OK]  Tier 1: {wrapper} found")
    else:
        print(f"[FAIL] Tier 1: {wrapper} not found — run install.py without --check first")
        failures += 1

    # Tier 2 — Graphify
    if shutil.which("graphify"):
        print("[OK]  Tier 2: graphify in PATH")
    else:
        print("[WARN] Tier 2: graphify not in PATH — run install.py again to fix")

    # Tier 3 — Kaimon (check if MCP config lists it)
    mcp_config = Path.home() / ".claude" / "claude_mcp_settings.json"
    if mcp_config.exists() and "kaimon" in mcp_config.read_text().lower():
        print("[OK]  Tier 3: Kaimon found in MCP config")
    else:
        print("[WARN] Tier 3: Kaimon not in MCP config — start kaimon and press 'i'")

    # Env vars
    for var in ("WORKER_API_KEY", "WORKER_BASE_URL", "WORKER_MODEL", "COWORKER_DIR"):
        val = os.environ.get(var, "")
        if val:
            display = val[:12] + "…" if len(val) > 12 else val
            print(f"[OK]  {var}={display}")
        else:
            print(f"[FAIL] {var} not set")
            failures += 1

    print(f"\n{'All checks passed.' if failures == 0 else f'{failures} failure(s) — see above.'}")
    return failures


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()

    if args.check:
        sys.exit(health_check(args.bin_dir))

    if not args.api_key and not args.generate_only:
        print("ERROR: --api-key is required (or set WORKER_API_KEY)")
        sys.exit(1)

    check_uv()
    print(f"Platform: {platform.system()} | Output: {args.output_dir}\n")

    if not args.generate_only:
        setup_coworker(args.coworker_dir)
        install_env_vars(args)
        install_scripts(args.bin_dir, args.coworker_dir)
        setup_graphify(args.graphify_platform)
    else:
        print("[1-4/6] Skipped (--generate-only)")

    print("[5/6] Generating config files …")
    generate_claude_md(args.output_dir, args)
    generate_settings(args.output_dir, args)
    generate_mcp_config(args.output_dir)
    copy_claudeignore(args.output_dir)

    print("\n[6/6] Running health check …")
    health_check(args.bin_dir)

    out = args.output_dir
    print(f"\nDone. Generated files are in {out}/ — deploy them as follows:")
    print(f"  1. {out}/CLAUDE.md")
    print(f"       Copy to your project root or ~/.claude/CLAUDE.md")
    print(f"  2. {out}/.claude/settings.json")
    print(f"       Copy to your project's .claude/ (safe to replace if it doesn't exist yet)")
    print(f"  3. {out}/.claude/mcp_config.json")
    print(f"       MERGE into your existing MCP config — do not replace outright")
    print(f"  4. {out}/.claudeignore")
    print(f"       MERGE into your existing .claudeignore — do not replace outright")
    print(f"  5. In each project, open Claude Code and type: /graphify .")
    print(f"       graphify is a Claude Code skill — /graphify builds the knowledge graph inside a session.")
    print(f"       Optional: run 'graphify hook install' in the terminal to auto-rebuild on every git commit.")
    print(f"  6. Start Kaimon:    cd ~/Kaimon.jl && ./bin/kaimon  (press 'i' for MCP config)")
    if not IS_WINDOWS:
        print(f"  7. Reload shell:    source ~/.bashrc  (or open a new terminal)")


if __name__ == "__main__":
    main()
