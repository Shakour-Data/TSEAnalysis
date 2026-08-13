param(
    [switch]$AutoCommit,
    [switch]$DryRun
)

# Ensure we run from repo root
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path) | Out-Null
Set-Location -Path ".." | Out-Null

# Prepare output locations
$logDir = "docs/git_commits"
$diffDir = Join-Path $logDir "diffs"
$logFile = Join-Path $logDir "git_commit_log.csv"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
if (-not (Test-Path $diffDir)) { New-Item -ItemType Directory -Path $diffDir | Out-Null }
if (-not (Test-Path $logFile)) { "CommitSHA,File,DateISO,Message" | Out-File -FilePath $logFile -Encoding utf8 }

# Get staged files
$staged = git diff --name-only --cached | Where-Object { $_ -ne "" }
if (-not $staged) {
    Write-Host "No staged files found. Nothing to commit." -ForegroundColor Yellow
    exit 0
}

$index = 0
$errors = @()

foreach ($file in $staged) {
    $index++
    Write-Host "[$index/$($staged.Count)] Processing: $file" -ForegroundColor Cyan

    # get diff and stats
    $diff = git --no-pager diff --cached -- $file 2>$null
    $numstat = git diff --cached --numstat -- $file 2>$null | Out-String
    $numstat = $numstat.Trim()

    # sanitize filename for diff storage
    $safeName = $file -replace '[\\/:]','_' -replace ' ','_'
    $diffPath = Join-Path $diffDir ("$safeName.diff")
    $diff | Out-File -FilePath $diffPath -Encoding utf8

    # generate commit prefix by heuristics
    $prefix = 'chore'
    if ($file -match '^docs/|\.md$') { $prefix = 'docs' }
    elseif ($file -match '^tests/|test_') { $prefix = 'test' }
    elseif ($file -match '^scripts/') { $prefix = 'chore' }
    elseif ($file -match '^app/|\.py$') { $prefix = 'chore' }
    elseif ($file -match '^models/') { $prefix = 'model' }

    # short summary from numstat if available
    if ($numstat -match '^(\d+)\s+(\d+)\s+') {
        $added = $matches[1]
        $removed = $matches[2]
        $summary = "$added additions, $removed deletions"
    } else {
        $summary = "content update"
    }

    $msg = "$($prefix): update $file — $summary (per-file commit)"

    # If DryRun, only record proposed commit (no actual git commit)
    if ($DryRun) {
        $dryLog = Join-Path $logDir "dryrun_proposals.csv"
        if (-not (Test-Path $dryLog)) { "File,ProposedMessage,Numstat,DiffPath" | Out-File -FilePath $dryLog -Encoding utf8 }
        $proposal = "`"$file`",`"$msg`",`"$numstat`",`"$diffPath`""
        Add-Content -Path $dryLog -Value $proposal -Encoding utf8
        Write-Host "[DryRun] Proposal recorded for $file" -ForegroundColor Yellow
        continue
    }

    try {
        # Commit only this file (use staged changes for the path)
        git commit -m "$msg" -- $file 2>&1 | Out-String | Write-Host
        if ($LASTEXITCODE -ne 0) { throw "git commit failed for $file" }

        # get commit sha
        $sha = git rev-parse --short HEAD
        $dateIso = (Get-Date).ToString("o")

        # append to CSV log (quote message)
        $csvLine = "`"$sha`",`"$file`",`"$dateIso`",`"$msg`""
        $csvLine | Add-Content -Path $logFile -Encoding utf8

        Write-Host "Committed $file -> $sha" -ForegroundColor Green

        # validation: check git status and ensure file not staged
        $porcelain = git status --porcelain -- $file | Out-String
        if ($porcelain.Trim() -ne "") {
            Write-Host "Warning: $file still shows changes in status:" -ForegroundColor Yellow
            Write-Host $porcelain
        }
    } catch {
        $err = $_.Exception.Message
        Write-Host "Error committing $file: $err" -ForegroundColor Red
        $errors += @{File=$file; Error=$err}
    }

}

# Summary
Write-Host "\nCommit run completed. Total files processed: $($staged.Count)" -ForegroundColor Cyan
if ($errors.Count -gt 0) {
    Write-Host "Errors encountered: $($errors.Count)" -ForegroundColor Red
    $errPath = Join-Path $logDir "errors.json"
    $errors | ConvertTo-Json | Out-File -FilePath $errPath -Encoding utf8
    Write-Host "See $errPath for details." -ForegroundColor Yellow
} else {
    Write-Host "All files committed successfully." -ForegroundColor Green
}

Write-Host "Log written to: $logFile" -ForegroundColor Cyan
Write-Host "Diffs saved under: $diffDir" -ForegroundColor Cyan

exit 0
