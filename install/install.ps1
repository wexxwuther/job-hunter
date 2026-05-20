# job-hunter — one-shot installer for Windows (PowerShell 5+)
# Installs the skill into all four supported agent paths:
#   $HOME\.claude\skills\job-hunter\      (Claude Code)
#   $HOME\.codex\skills\job-hunter\       (OpenAI Codex)
#   $HOME\.openclaw\skills\job-hunter\    (OpenClaw)
#   $HOME\.hermes\skills\job-hunter\      (Hermes Agent)
#
# Usage (remote):
#   iwr https://raw.githubusercontent.com/wexxwuther/job-hunter/main/install/install.ps1 -UseBasicParsing | iex
#
# Or, after cloning:
#   .\install\install.ps1

$ErrorActionPreference = 'Stop'

$Repo   = 'wexxwuther/job-hunter'
$Branch = 'main'
$TmpDir = Join-Path $env:TEMP ("job-hunter-install-" + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $TmpDir | Out-Null

try {
    Write-Host "==> Downloading job-hunter (branch: $Branch)..."

    $git = Get-Command git -ErrorAction SilentlyContinue
    if ($git) {
        & git clone --depth=1 --branch $Branch "https://github.com/$Repo.git" (Join-Path $TmpDir 'job-hunter') | Out-Null
    } else {
        $zipPath = Join-Path $TmpDir 'src.zip'
        Invoke-WebRequest -UseBasicParsing -Uri "https://github.com/$Repo/archive/refs/heads/$Branch.zip" -OutFile $zipPath
        Expand-Archive -Path $zipPath -DestinationPath $TmpDir -Force
        Move-Item -Path (Join-Path $TmpDir "job-hunter-$Branch") -Destination (Join-Path $TmpDir 'job-hunter')
        Remove-Item $zipPath -Force
    }

    $src = Join-Path $TmpDir 'job-hunter'

    # Strip git history and developer-only files before install
    foreach ($strip in @('.git', '.github', 'install')) {
        $p = Join-Path $src $strip
        if (Test-Path $p) { Remove-Item $p -Recurse -Force }
    }

    $dests = @(
        (Join-Path $HOME '.claude\skills\job-hunter'),
        (Join-Path $HOME '.codex\skills\job-hunter'),
        (Join-Path $HOME '.openclaw\skills\job-hunter'),
        (Join-Path $HOME '.hermes\skills\job-hunter')
    )

    foreach ($dest in $dests) {
        Write-Host "==> Installing to $dest"
        $parent = Split-Path $dest -Parent
        if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
        if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
        Copy-Item -Path $src -Destination $dest -Recurse -Force
    }

    Write-Host ""
    Write-Host "Done. Restart your agent and try:"
    Write-Host '  "Find me senior backend jobs in Seattle, $180k+, that aren''t ghost listings."'
}
finally {
    if (Test-Path $TmpDir) { Remove-Item $TmpDir -Recurse -Force -ErrorAction SilentlyContinue }
}
