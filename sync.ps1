<#
.SYNOPSIS
Safely synchronize the Problem-Dissector repository, run verification gates, check secrets, and commit.

.DESCRIPTION
Supports routine sync, PR workflow (-PR), and verification checks.
#>

[CmdletBinding()]
param (
    [Alias("m")]
    [string]$Message,

    [switch]$PullOnly,

    [switch]$SkipAudit,

    [switch]$NoPush,

    [switch]$PR,

    [int]$Issue,

    [string]$Reviewer
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Status {
    param(
        [string]$Message,
        [System.ConsoleColor]$Color = [System.ConsoleColor]::Cyan
    )
    Write-Host "[$((Get-Date).ToString('HH:mm:ss'))] $Message" -ForegroundColor $Color
}

function Write-Notice {
    param([string]$Message)
    Write-Status -Message $Message -Color ([System.ConsoleColor]::Yellow)
}

function Write-Success {
    param([string]$Message)
    Write-Status -Message $Message -Color ([System.ConsoleColor]::Green)
}

function Find-StagedSecrets {
    $stagedDiff = git diff --cached -U0 2>$null
    if (-not $stagedDiff) { return @() }

    $addedLines = $stagedDiff | Where-Object { $_ -match '^\+[^+]' } | ForEach-Object { $_.Substring(1) }
    if (-not $addedLines) { return @() }

    $secretPatterns = @(
        'AKIA[0-9A-Z]{16}'
        'sk-[a-zA-Z0-9]{20,}'
        'sk-ant-[a-zA-Z0-9\-]{20,}'
        'ghp_[a-zA-Z0-9]{36}'
        'github_pat_[a-zA-Z0-9_]{20,}'
        'AIza[0-9A-Za-z\-_]{35}'
        'xox[baprs]-[0-9a-zA-Z\-]{10,}'
        '-----BEGIN (RSA|EC|OPENSSH|PGP|DSA)? ?PRIVATE KEY-----'
        '(?i)(api[_-]?key|secret|password|token|passwd)\s*[:=]\s*[''"][^''"\s]{8,}[''"]'
    )

    $hits = @()
    foreach ($line in $addedLines) {
        foreach ($pattern in $secretPatterns) {
            if ($line -match $pattern) {
                $snippet = $line.Trim()
                $hits += [PSCustomObject]@{
                    Pattern = $pattern
                    Snippet = $snippet.Substring(0, [Math]::Min(60, $snippet.Length))
                }
                break
            }
        }
    }

    return @($hits)
}

function Run-Tests {
    if (Test-Path "tests") {
        Write-Status "Running pytest verification suite..."
        python -m pytest tests/ -v
        if ($LASTEXITCODE -ne 0) {
            throw "Pytest verification failed! Aborting sync."
        }
        Write-Success "All tests passed!"
    }
}

try {
    Write-Status "Starting Problem-Dissector repository synchronization..."

    $gitRoot = git rev-parse --show-toplevel 2>$null
    if (-not $gitRoot) {
        throw "Current directory is not a valid Git repository."
    }

    $currentBranch = (git branch --show-current 2>$null)
    if ($currentBranch) { $currentBranch = $currentBranch.Trim() }
    if (-not $currentBranch) { $currentBranch = "main" }

    $hasRemote = [bool](git remote get-url origin 2>$null)

    if ($PullOnly) {
        if ($hasRemote) {
            git pull origin $currentBranch --rebase --autostash
            Write-Success "PullOnly requested. Synchronization complete!"
        }
        exit 0
    }

    # 1. Tests Gate
    if (-not $SkipAudit) {
        Run-Tests
    }

    # 2. Check changes
    $status = git status --porcelain
    if (-not $status) {
        Write-Success "Working directory clean. Nothing to commit."
        exit 0
    }

    # 3. Stage
    Write-Status "Staging changes..."
    git add -A

    # 4. Secret scan
    Write-Status "Scanning staged changes for accidental secrets..."
    $secretHits = @(Find-StagedSecrets)
    if ($secretHits.Count -gt 0) {
        Write-Host "SECURITY HALT: Potential secrets detected in diff!" -ForegroundColor Red
        foreach ($hit in $secretHits) {
            Write-Host "Pattern : $($hit.Pattern)" -ForegroundColor Yellow
            Write-Host "Snippet : $($hit.Snippet)" -ForegroundColor White
        }
        git reset
        throw "Aborting commit due to potential credential leak."
    }

    # 5. Commit message
    $commitMsg = $Message
    if ([string]::IsNullOrWhiteSpace($commitMsg)) {
        $commitMsg = "chore(dissector): synchronize repository changes"
    }

    # 6. Commit
    Write-Status "Committing changes..."
    git commit -m $commitMsg
    Write-Success "Commit created successfully!"

    # 7. Push or PR
    if (-not $NoPush) {
        if ($hasRemote) {
            Write-Status "Pushing branch '$currentBranch' to origin..."
            git push -u origin $currentBranch
            Write-Success "Pushed to origin/$currentBranch!"
        }

        if ($PR) {
            Write-Status "Opening Pull Request on GitHub..."
            $prTitle = $commitMsg
            $prBody = "Automated Pull Request via sync.bat/sync.ps1.`n`nCloses #$Issue"
            $ghCmd = "gh pr create --title `"$prTitle`" --body `"$prBody`""
            if ($Reviewer) {
                $ghCmd += " --reviewer $Reviewer"
            }
            Invoke-Expression $ghCmd
            Write-Success "Pull Request created!"
        }
    }

    Write-Success "🎉 Problem-Dissector sync complete!"
}
catch {
    Write-Host "Sync Error: $_" -ForegroundColor Red
    exit 1
}
