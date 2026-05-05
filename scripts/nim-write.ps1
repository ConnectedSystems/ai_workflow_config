param(
    [string]$Spec,
    [string]$Context,
    [string]$Target,
    [int]$MaxTokens = 16384,
    [string]$Model = $env:WORKER_MODEL
)
$base = if ($env:COWORKER_DIR) { $env:COWORKER_DIR } else { "$env:USERPROFILE\claude-coworker-model" }
$venv = "$base\.venv\Scripts\python.exe"
$tool = "$base\tools\kimi-write"
& $venv $tool --spec $Spec --context $Context --target $Target --max-tokens $MaxTokens --model $Model
