# job-hunter family — one-shot installer for Windows (PowerShell 5+)
#
# Installs all 7 family skills (orchestrator + 6 members) into each supported
# agent-harness skills directory:
#   $HOME\.claude\skills\<member>\     (Claude Code)
#   $HOME\.agents\skills\<member>\     (OpenAI Codex AND OpenClaw - shared path)
#   $HOME\.hermes\skills\<member>\     (Hermes Agent)
#
# Members: job-hunter (orchestrator), career-profile, job-search,
#          resume-tailor, cover-letter, application-tracker, outcome-learning.
#
# TWO WAYS TO RUN - both install all 7 skills into all harnesses:
#   1. OFFLINE (from the unzipped family bundle - no GitHub needed):
#        Expand-Archive job-hunter-FAMILY-installer-only-v6.0.0.zip -DestinationPath .
#        .\job-hunter\install\install.ps1
#   2. ONLINE (clones the repo; needs access to the GitHub repo):
#        iwr https://raw.githubusercontent.com/wexxwuther/job-hunter/main/install/install.ps1 -UseBasicParsing | iex

$ErrorActionPreference = 'Stop'

$Repo    = 'wexxwuther/job-hunter'
$Branch  = 'main'
$Members = @('job-hunter','career-profile','job-search','resume-tailor','cover-letter','application-tracker','outcome-learning')
$Roots   = @('.claude','.agents','.hermes')
$TmpDir  = Join-Path $env:TEMP ("job-hunter-install-" + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $TmpDir | Out-Null

try {
    # --- Find the source: prefer LOCAL (running from the unzipped bundle), else clone. ---
    # When run from the bundle this script is at <root>\job-hunter\install\install.ps1, so the
    # family root (the dir holding the 6 member dirs) is the script dir's parent.
    $src = $null
    if ($PSScriptRoot) {
        $candidate = Split-Path $PSScriptRoot -Parent
        if (Test-Path (Join-Path $candidate 'job-hunter\SKILL.md')) {
            $src = $candidate
            Write-Host "==> Installing from local files (no download): $src"
        }
    }

    if (-not $src) {
        Write-Host "==> Local bundle not detected; downloading job-hunter family (branch: $Branch)..."
        $git = Get-Command git -ErrorAction SilentlyContinue
        if ($git) {
            & git clone --depth=1 --branch $Branch "https://github.com/$Repo.git" (Join-Path $TmpDir 'src') | Out-Null
        } else {
            $zipPath = Join-Path $TmpDir 'src.zip'
            Invoke-WebRequest -UseBasicParsing -Uri "https://github.com/$Repo/archive/refs/heads/$Branch.zip" -OutFile $zipPath
            Expand-Archive -Path $zipPath -DestinationPath $TmpDir -Force
            Move-Item -Path (Join-Path $TmpDir "job-hunter-$Branch") -Destination (Join-Path $TmpDir 'src')
            Remove-Item $zipPath -Force
        }
        $src = Join-Path $TmpDir 'src'
    }

    foreach ($member in $Members) {
        $memberSrc = Join-Path $src $member
        if (-not (Test-Path $memberSrc)) {
            Write-Warning "family member '$member' not found in repo; skipping."
            continue
        }
        foreach ($root in $Roots) {
            $dest = Join-Path $HOME (Join-Path "$root\skills" $member)
            Write-Host "==> Installing $member -> $dest"
            $parent = Split-Path $dest -Parent
            if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
            if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
            Copy-Item -Path $memberSrc -Destination $dest -Recurse -Force
            foreach ($strip in @('tests', 'docs\superpowers')) {
                $p = Join-Path $dest $strip
                if (Test-Path $p) { Remove-Item $p -Recurse -Force }
            }
        }
    }

    Write-Host ""
    Write-Host "Done. Installed the job-hunter family (7 skills) to ~/.claude, ~/.agents (Codex+OpenClaw), and ~/.hermes."
    Write-Host 'Restart your agent and try: "Help me run my whole job search."'
}
finally {
    if (Test-Path $TmpDir) { Remove-Item $TmpDir -Recurse -Force -ErrorAction SilentlyContinue }
}
