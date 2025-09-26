#!/usr/bin/env pwsh

<#
.SYNOPSIS
    Amplifier Docker Wrapper Script for PowerShell
.DESCRIPTION
    Runs Amplifier in a Docker container for any target project directory
.PARAMETER ProjectPath
    Path to the target project directory
.PARAMETER DataDir
    Optional path to Amplifier data directory (defaults to ./amplifier-data)
.EXAMPLE
    ./amplify.ps1 "C:\MyProject"
.EXAMPLE
    ./amplify.ps1 "C:\MyProject" "C:\amplifier-data"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectPath,

    [Parameter(Mandatory=$false)]
    [string]$DataDir
)

# Function to write colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[Amplifier] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[Amplifier] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[Amplifier] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[Amplifier] $Message" -ForegroundColor Red
}

# Check if Docker is installed and running
try {
    $dockerVersion = docker --version 2>$null
    if (-not $dockerVersion) {
        throw "Docker not found"
    }
} catch {
    Write-Error "Docker is not installed or not in PATH. Please install Docker Desktop first."
    exit 1
}

try {
    docker info 2>$null | Out-Null
} catch {
    Write-Error "Docker is not running. Please start Docker Desktop first."
    exit 1
}

# Validate and resolve paths
if (-not (Test-Path $ProjectPath)) {
    Write-Error "Target project directory does not exist: $ProjectPath"
    exit 1
}

$TargetProject = Resolve-Path $ProjectPath
if (-not $DataDir) {
    $DataDir = Join-Path (Get-Location) "amplifier-data"
}

# Create data directory if it doesn't exist
if (-not (Test-Path $DataDir)) {
    New-Item -ItemType Directory -Path $DataDir -Force | Out-Null
}

# Resolve data directory path
$ResolvedDataDir = Resolve-Path $DataDir

Write-Status "Target Project: $TargetProject"
Write-Status "Data Directory: $ResolvedDataDir"

# Build Docker image if it doesn't exist
$ImageName = "amplifier:latest"
try {
    docker image inspect $ImageName 2>$null | Out-Null
    Write-Status "Using existing Docker image: $ImageName"
} catch {
    Write-Status "Building Amplifier Docker image..."
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    docker build -t $ImageName $ScriptDir
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to build Docker image"
        exit 1
    }
    Write-Success "Docker image built successfully"
}

# Prepare environment variables
$EnvArgs = @()

# Forward API keys if they exist
$ApiKeys = @(
    "ANTHROPIC_API_KEY",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_DEFAULT_REGION",
    "AWS_REGION"
)

foreach ($Key in $ApiKeys) {
    $Value = [Environment]::GetEnvironmentVariable($Key)
    if ($Value) {
        $EnvArgs += "-e"
        $EnvArgs += "$Key=$Value"
        Write-Status "Forwarding $Key"
    }
}

# Check if we have any API keys
if ($EnvArgs.Count -eq 0) {
    Write-Warning "No API keys detected in environment."
    Write-Warning "Make sure to set ANTHROPIC_API_KEY or AWS credentials before running."
}

# Convert Windows paths to Docker-compatible paths
$DockerProjectPath = $TargetProject.Path -replace '\\', '/' -replace '^([A-Z]):', '/mnt/$1'.ToLower()
$DockerDataPath = $ResolvedDataDir.Path -replace '\\', '/' -replace '^([A-Z]):', '/mnt/$1'.ToLower()

# For Windows Docker Desktop, use the original Windows paths
if ($IsWindows -or $env:OS -eq "Windows_NT") {
    $DockerProjectPath = $TargetProject.Path
    $DockerDataPath = $ResolvedDataDir.Path
}

# Run the Docker container
Write-Status "Starting Amplifier container..."
Write-Status "Press Ctrl+C to exit when done"

$ContainerName = "amplifier-$(Split-Path -Leaf $TargetProject)-$PID"

$DockerArgs = @(
    "run", "-it", "--rm"
    $EnvArgs
    "-e", "TARGET_DIR=/workspace"
    "-e", "AMPLIFIER_DATA_DIR=/app/amplifier-data"
    "-v", "$($DockerProjectPath):/workspace"
    "-v", "$($DockerDataPath):/app/amplifier-data"
    "--name", $ContainerName
    $ImageName
)

try {
    & docker @DockerArgs
    Write-Success "Amplifier session completed"
} catch {
    Write-Error "Failed to run Amplifier container: $_"
    exit 1
}