$projectName = "taskflow"
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$output = Join-Path $PSScriptRoot "$projectName-$timestamp.zip"

$temp = Join-Path $env:TEMP "$projectName-export"

if (Test-Path $temp) {
    Remove-Item $temp -Recurse -Force
}

New-Item -ItemType Directory -Path $temp | Out-Null

$excludeDirs = @(
    "venv",
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    "media",
    "staticfiles"
)

$excludeFiles = @(
    ".env",
    "*.pyc",
    "*.zip"
)

Get-ChildItem $PSScriptRoot -Force | ForEach-Object {
    if ($excludeDirs -contains $_.Name) {
        return
    }

    if ($_.Name -eq ".env") {
        return
    }

    if ($_.Extension -eq ".zip") {
        return
    }

    Copy-Item $_.FullName $temp -Recurse -Force
}

Get-ChildItem $temp -Recurse -Force |
    Where-Object {
        $_.PSIsContainer -and $_.Name -eq "__pycache__"
    } |
    Remove-Item -Recurse -Force

Get-ChildItem $temp -Recurse -Force -Filter "*.pyc" |
    Remove-Item -Force

Compress-Archive -Path "$temp\*" -DestinationPath $output -Force

Remove-Item $temp -Recurse -Force

Write-Host ""
Write-Host "Created: $output"