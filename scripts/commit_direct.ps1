#!/usr/bin/env pwsh
# Direct commit script - simpler, for staged files one-by-one

param([switch]$Confirm)

$repoRoot = git rev-parse --show-toplevel
if (-not $repoRoot) { Write-Error "Not in a git repo"; exit 1 }
Set-Location $repoRoot

$logDir = "docs/git_commits"
$diffDir = "$logDir/diffs"
$logFile = "$logDir/git_commit_log.csv"

# Ensure dirs exist
@($logDir, $diffDir) | ForEach-Object { if (-not (Test-Path $_)) { New-Item -ItemType Directory -Path $_ -Force | Out-Null } }

# Header for CSV
if (-not (Test-Path $logFile) -or (Get-Item $logFile).Length -eq 0) {
    "CommitSHA,File,DateISO,Message" | Out-File -FilePath $logFile -Encoding utf8 -Force
}

# Get all staged files
$files = @(git diff --name-only --cached)
if ($files.Count -eq 0) { Write-Host "No staged files."; exit 0 }

Write-Host "Found $($files.Count) staged files" -ForegroundColor Cyan

$committed = 0
$errors = @()

foreach ($file in $files) {
    Write-Host "`n[$($committed + 1)/$($files.Count)] File: $file" -ForegroundColor Cyan

    # Get diff
    $diff = git diff --cached -- $file
    $stats = git diff --cached --numstat -- $file

    # Save diff
    $safeName = $file -replace '[:\\\/]', '_'
    $diffFile = "$diffDir/$safeName.diff"
    $diff | Out-File -FilePath $diffFile -Encoding utf8 -Force

    # Generate message
    if ($stats -match '(\d+)\s+(\d+)') {
        $adds = $matches[1]; $dels = $matches[2]
        $summary = "$adds additions, $dels deletions"
    } else {
        $summary = "file update"
    }

    $prefix = 'chore'
    if ($file -match '\.md$|^docs/') { $prefix = 'docs' }
    elseif ($file -match '^tests/') { $prefix = 'test' }
    elseif ($file -match '^app/.*\.py$') { $prefix = 'feat' }

    $msg = "$($prefix): update $file ($summary)"

    # Show and confirm if requested
    if ($Confirm) {
        Write-Host "Message: $msg" -ForegroundColor Yellow
        $resp = Read-Host "Commit? (Y/n)"
        if ($resp -match '^[Nn]') { Write-Host "Skipped."; continue }
    }

    # Commit
    try {
        git commit -m $msg -- $file 2>&1 | ForEach-Object { Write-Host "  $_" }
        $sha = git rev-parse --short HEAD
        $date = (Get-Date).ToString("o")
        "`"$sha`",`"$file`",`"$date`",`"$msg`"" | Add-Content -Path $logFile -Encoding utf8
        $committed++
        Write-Host "✓ Committed $sha" -ForegroundColor Green
    } catch {
        $errors += @{file=$file; error=$_.Exception.Message}
        Write-Host "✗ Error: $_" -ForegroundColor Red
    }
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "Committed: $committed / $($files.Count)" -ForegroundColor Green
if ($errors.Count -gt 0) {
    Write-Host "Errors: $($errors.Count)" -ForegroundColor Red
    $errors | ConvertTo-Json | Out-File "$logDir/errors.json" -Encoding utf8 -Force
}
Write-Host "Log: $logFile" -ForegroundColor Yellow
Write-Host "Diffs: $diffDir" -ForegroundColor Yellow
