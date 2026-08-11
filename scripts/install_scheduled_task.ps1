[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateScript({ Test-Path -LiteralPath $_ -PathType Leaf })]
    [string] $ConfigPath
)

$ErrorActionPreference = 'Stop'
$TaskName = 'CrossBorderEcommerceDailyReport'
$RunDailyPath = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot 'run_daily.py')).Path
$ResolvedConfigPath = (Resolve-Path -LiteralPath $ConfigPath).Path
$PythonExecutable = (Get-Command python -CommandType Application | Select-Object -First 1).Source

if (-not $PythonExecutable) {
    throw '找不到当前 Python 可执行文件。'
}

$ActionArguments = '"{0}" --config "{1}"' -f $RunDailyPath, $ResolvedConfigPath
$Action = New-ScheduledTaskAction -Execute $PythonExecutable -Argument $ActionArguments
$Trigger = New-ScheduledTaskTrigger -Daily -At '09:00'
$Settings = New-ScheduledTaskSettingsSet -WakeToRun -StartWhenAvailable

Write-Host "计划任务名称: $TaskName"
Write-Host "计划任务动作: `"$PythonExecutable`" $ActionArguments"
Write-Host '计划任务时间: 每日 09:00'

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description 'Generate the cross-border ecommerce daily report.' `
    -Force
