<#
.SYNOPSIS
    PowerShell equivalent of the Makefile targets, for Windows machines without a usable make.

.DESCRIPTION
    Every command here does exactly what the same-named make target does. Keep the two in sync:
    if you add a target to the Makefile, add it to $Commands below.

.EXAMPLE
    .\scripts\dev.ps1 help
    .\scripts\dev.ps1 test
    .\scripts\dev.ps1 up
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string] $Command = 'help',

    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]] $Rest
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot

# NOTE: the parameter is deliberately NOT called $Args - that is a PowerShell automatic
# variable and shadowing it silently drops every argument.
function Invoke-InDir {
    param([string] $Dir, [string] $Exe, [string[]] $ArgList)
    Push-Location (Join-Path $Root $Dir)
    try {
        & $Exe @ArgList
        if ($LASTEXITCODE -ne 0) { throw "$Exe exited with code $LASTEXITCODE" }
    }
    finally { Pop-Location }
}

function Invoke-Compose {
    param([string[]] $ArgList)
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "docker is not installed or not on PATH. Install Docker Desktop, then re-run."
    }
    Invoke-InDir -Dir '.' -Exe 'docker' -ArgList $ArgList
}

$Commands = @{
    'help'        = { Invoke-InDir '.' 'python' @('scripts/make_help.py') }
    'venv'        = { Invoke-InDir '.' 'python' @('scripts/venv_setup.py', '--create') }
    'install'     = { Invoke-InDir '.' 'python' @('scripts/venv_setup.py', '--install') }
    'up'          = { Invoke-Compose @('compose', '-f', 'infra/docker-compose.yml', 'up', '-d') }
    'down'        = { Invoke-Compose @('compose', '-f', 'infra/docker-compose.yml', 'down') }
    'check-infra' = { Invoke-InDir '.' 'python' @('scripts/check_infra.py') }
    'up-maps'     = { Invoke-Compose @('compose', '-f', 'infra/docker-compose.yml', '-f', 'infra/docker-compose.maps.yml', 'up', '-d') }
    'migrate'     = { Invoke-InDir 'backend' 'python' @('-m', 'alembic', 'upgrade', 'head') }
    'seed'        = { Invoke-InDir 'backend' 'python' @('-m', 'app.cli', 'seed') }
    'backend-dev' = { Invoke-InDir 'backend' 'python' @('-m', 'uvicorn', 'app.main:create_app', '--factory', '--reload', '--port', '8000') }
    'ingestor'    = { Invoke-InDir 'backend' 'python' @('-m', 'app.ingestor') }
    'worker'      = { Invoke-InDir 'backend' 'python' @('-m', 'celery', '-A', 'app.workers.celery_app', 'worker', '--loglevel=info') }
    'beat'        = { Invoke-InDir 'backend' 'python' @('-m', 'celery', '-A', 'app.workers.celery_app', 'beat', '--loglevel=info') }
    'test'        = { Invoke-InDir 'backend' 'python' (@('-m', 'pytest') + $Rest) }
    'lint'        = { Invoke-InDir '.' 'python' @('scripts/lint.py') }
    'format'      = { Invoke-InDir 'backend' 'python' @('-m', 'ruff', 'format', '.') }
    'api-client'  = { Invoke-InDir '.' 'python' @('scripts/not_ready.py', 'api-client', 'A02') }
    'sim-quick'   = { Invoke-InDir 'simulator' 'python' @('-m', 'sim', 'suite', 'quick') }
    'sim-full'    = { Invoke-InDir 'simulator' 'python' @('-m', 'sim', 'suite', 'full') }
    'maps'        = { Invoke-InDir '.' 'python' @('scripts/not_ready.py', 'maps', 'I02b') }
}

if (-not $Commands.ContainsKey($Command)) {
    Write-Host "Unknown command '$Command'." -ForegroundColor Red
    Write-Host "Available: $(($Commands.Keys | Sort-Object) -join ', ')"
    exit 2
}

& $Commands[$Command]
