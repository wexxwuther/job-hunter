# job-hunter family — one-shot installer for Windows (PowerShell 5+)
#
# Installs all 6 family skills (orchestrator + 5 members) into each supported
# agent-harness skills directory:
#   $HOME\.claude\skills\<member>\     (Claude Code)
#   $HOME\.agents\skills\<member>\     (OpenAI Codex AND OpenClaw - shared path)
#   $HOME\.hermes\skills\<member>\     (Hermes Agent)
#
# Members: job-hunter (orchestrator), career-profile, job-search,
#          resume-tailor, application-tracker, outcome-learning.
#
# Usage (remote):
#   iwr https://raw.githubusercontent.com/wexxwuther/job-hunter/main/install/install.ps1 -UseBasicParsing | iex
# Or, after cloning:
#   .\install\install.ps1

$ErrorActionPreference = 'Stop'

$Repo    = 'wexxwuther/job-hunter'
$Branch  = 'main'
$Members = @('job-hunter','career-profile','job-search','resume-tailor','application-tracker','outcome-learning')
$Roots   = @('.claude','.agents','.hermes')
$TmpDir  = Join-Path $env:TEMP ("job-hunter-install-" + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $TmpDir | Out-Null

try {
    Write-Host "==> Downloading job-hunter family (branch: $Branch)..."
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
    Write-Host "Done. Installed the job-hunter family (6 skills) to ~/.claude, ~/.agents (Codex+OpenClaw), and ~/.hermes."
    Write-Host 'Restart your agent and try: "Help me run my whole job search."'
}
finally {
    if (Test-Path $TmpDir) { Remove-Item $TmpDir -Recurse -Force -ErrorAction SilentlyContinue }
}
