param(
    [string]$Session,
    [string]$Out
)
$base = if ($env:COWORKER_DIR) { $env:COWORKER_DIR } else { "$env:USERPROFILE\claude-coworker-model" }
$venv = "$base\.venv\Scripts\python.exe"
$tool = "$base\tools\extract-chat"
& $venv $tool $Session -o $Out
