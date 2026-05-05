param(
    [string[]]$Paths,
    [string]$Question,
    [int]$MaxTokens = 8192,
    [string]$Model = $env:WORKER_MODEL
)
$base = if ($env:COWORKER_DIR) { $env:COWORKER_DIR } else { "$env:USERPROFILE\claude-coworker-model" }
$venv = "$base\.venv\Scripts\python.exe"
$tool = "$base\tools\ask-kimi"
& $venv $tool --paths $Paths --question $Question --max-tokens $MaxTokens --model $Model
