[CmdletBinding()]
param(
  [ValidateRange(1,4)][int]$jobs = 3
)

function Get-ThreadCount {
    param([int]$Jobs)
    switch ($Jobs) {
        1 { return 12 }
        2 { return 6 }
        3 { return 4 }
        4 { return 3 }
        default { return 2 }
    }
}

$threads = Get-ThreadCount -Jobs $jobs

# --- WhisperX switches ---
$whisperx_switches = @(
  "--model", "large",
  "--language", "fi",
  "--device", "cpu",
  "--compute_type", "int8",
  "--no_align",
  "--diarize",
  "--chunk_size", "30",
  "--vad_method", "pyannote",
  "--vad_onset", "0.6",
  "--vad_offset", "0.6",
  "--batch_size", "1",
  "--verbose", "True",
  "--print_progress", "True",
  "--output_format", "all"
)

# --- PowerShell 7 check ---
if ($PSVersionTable.PSVersion.Major -lt 7) {
  $pwsh = Get-Command pwsh -ErrorAction SilentlyContinue
  if ($pwsh) { & $pwsh -NoLogo -File $MyInvocation.MyCommand.Path @args; exit $LASTEXITCODE }
  throw "PowerShell 7+ required. Install pwsh and re-run."
}

# --- Virtualenv check (FIXED) ---
$virtualenv_py = (where.exe python.exe 2>$null | Select-Object -First 1)
if ('C:\Users\utu\source\ChatGPT\Uiskotie9\Scripts\python.exe' -ne $virtualenv_py) {
  & 'C:\Users\utu\source\ChatGPT\Uiskotie9\Scripts\activate.ps1'
}

# --- HF token check ---
$who = & hf auth whoami 2>$null
if (-not $who -or $who -match "Not logged in") {
    Write-Host "No Hugging Face login found, running hf auth login..."
    & hf auth login
}

# --- Load token from cache ---
$tokenPath = "$env:HF_HOME\token"
if (Test-Path $tokenPath) {
    $env:HUGGINGFACE_HUB_TOKEN = (Get-Content $tokenPath -Raw).Trim()
}

# --- Thread caps ---
$env:CT2_THREAD_COUNT = $threads
$env:OMP_NUM_THREADS  = $threads
$env:MKL_NUM_THREADS  = $threads

# --- Files ---
$files = Get-ChildItem -File | Where-Object { $_.Extension -in ".mp3", ".wav" }
if ($files.Count -lt $jobs) {
    $jobs = $files.Count
    $threads = Get-ThreadCount -Jobs $jobs
}

# --- Parallel loop ---
$files | ForEach-Object -Parallel {
    $env:HUGGINGFACE_HUB_TOKEN = $using:env:HUGGINGFACE_HUB_TOKEN
    $env:CT2_THREAD_COUNT      = $using:env:CT2_THREAD_COUNT
    $env:OMP_NUM_THREADS       = $using:env:OMP_NUM_THREADS
    $env:MKL_NUM_THREADS       = $using:env:MKL_NUM_THREADS

    $p    = $_.FullName
    $name = $_.BaseName

    # jobid = short stable hash
    $jobid = (Get-FileHash -Algorithm SHA1 -InputStream (
                  [IO.MemoryStream]::new([Text.Encoding]::UTF8.GetBytes($p))
              )).Hash.Substring(0,8)

    $outDir = Join-Path -Path (Get-Location) -ChildPath $name
    if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }

    $start = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content run.log "[$jobid] $p -- job started at $start"

    # run WhisperX
    & $using:virtualenv_py -m whisperx $using:whisperx_switches `
        --output_dir $outDir $p 1> (Join-Path $outDir "$name.log") 2>&1 3>&1 4>&1 5>&1 6>&1 |
        ForEach-Object { "[$jobid] $_" } | Add-Content -Path "run.log"

    $end = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content run.log "[$jobid] $p -- job finished at $end -- exit code $LASTEXITCODE"
} -ThrottleLimit $jobs
