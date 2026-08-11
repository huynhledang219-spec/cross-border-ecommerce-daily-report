[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateScript({ Test-Path -LiteralPath $_ -PathType Leaf })]
    [string] $ConfigPath,

    [string] $PythonExecutable
)

$ErrorActionPreference = 'Stop'
$TaskName = 'CrossBorderEcommerceDailyReport'
$RunDailyPath = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot 'run_daily.py')).Path
$ResolvedConfigPath = (Resolve-Path -LiteralPath $ConfigPath).Path

if ($PythonExecutable) {
    $ResolvedPythonExecutable = (Resolve-Path -LiteralPath $PythonExecutable).Path
}
else {
    $PythonCommand = Get-Command python -CommandType Application -ErrorAction Stop |
        Select-Object -First 1
    $ResolvedPythonExecutable = (Resolve-Path -LiteralPath $PythonCommand.Source).Path
}

if (-not (Test-Path -LiteralPath $ResolvedPythonExecutable -PathType Leaf)) {
    throw 'The Python executable does not exist.'
}

$PreflightCode = @'
import importlib.util
import pathlib
import sys
import yaml
import playwright

script_path = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(script_path.parent))
spec = importlib.util.spec_from_file_location("run_daily_preflight", script_path)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load run_daily.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
'@

& $ResolvedPythonExecutable -c $PreflightCode $RunDailyPath
if ($LASTEXITCODE -ne 0) {
    throw 'Python preflight failed; the scheduled task was not registered.'
}

$ActionArguments = '"{0}" --config "{1}"' -f $RunDailyPath, $ResolvedConfigPath
$Action = New-ScheduledTaskAction -Execute $ResolvedPythonExecutable -Argument $ActionArguments
$Trigger = New-ScheduledTaskTrigger -Daily -At '09:00'
$Settings = New-ScheduledTaskSettingsSet -WakeToRun -StartWhenAvailable

Write-Host "Proposed task name: $TaskName"
Write-Host "Proposed task action: `"$ResolvedPythonExecutable`" $ActionArguments"
Write-Host 'Proposed schedule: daily at 09:00'

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description 'Generate the cross-border ecommerce daily report.' `
    -Force
