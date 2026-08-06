param(
    [string]$EvidenceDir = "work\evidence",
    [string]$ResultsDir = "work\results",
    [string]$Python = "python",
    [string]$Ffmpeg = "ffmpeg",
    [string]$Ffprobe = "ffprobe"
)

$ErrorActionPreference = "Stop"

& "$PSScriptRoot\bootstrap_windows.ps1"
New-Item -ItemType Directory -Force -Path $EvidenceDir, $ResultsDir | Out-Null

$extensions = @(".mp4", ".mov", ".mkv", ".avi", ".m4v", ".hevc", ".h265")
$files = Get-ChildItem -LiteralPath $EvidenceDir -File | Where-Object {
    $extensions -contains $_.Extension.ToLowerInvariant()
} | Sort-Object Name

if ($files.Count -eq 0) {
    throw "No supported video files in $EvidenceDir"
}

$session = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
$sessionDir = Join-Path $ResultsDir $session
New-Item -ItemType Directory -Force -Path $sessionDir | Out-Null
$hostProfile = Join-Path $sessionDir "host_profile.json"

& video-forensics-host-profile --output $hostProfile
if ($LASTEXITCODE -ne 0) { throw "host-profile failed" }

$profiles = @(
    "profiles\decoder_matrix\software_single_thread.json",
    "profiles\decoder_matrix\software_automatic_threads.json",
    "profiles\decoder_matrix\windows_intel_qsv.json",
    "profiles\decoder_matrix\windows_intel_d3d11va.json",
    "profiles\decoder_matrix\windows_nvidia_d3d11va.json",
    "profiles\decoder_matrix\windows_nvidia_cuda.json"
) | Where-Object { Test-Path -LiteralPath $_ }

foreach ($file in $files) {
    $safeStem = $file.BaseName -replace '[^A-Za-z0-9._-]', '_'
    $out = Join-Path $sessionDir $safeStem
    New-Item -ItemType Directory -Force -Path $out | Out-Null

    & video-forensics analyze $file.FullName --output (Join-Path $out "baseline")
    if ($LASTEXITCODE -ne 0) { throw "baseline failed for $($file.Name)" }

    & video-forensics-run-matrix $file.FullName `
        --output (Join-Path $out "matrix") `
        --ffmpeg $Ffmpeg `
        --ffprobe $Ffprobe
    if ($LASTEXITCODE -ne 0) { throw "matrix failed for $($file.Name)" }

    $visualArgs = @(
        $file.FullName,
        "--host-profile", $hostProfile,
        "--output", (Join-Path $out "visual_frames"),
        "--ffmpeg", $Ffmpeg
    )
    foreach ($profile in $profiles) {
        $visualArgs += @("--profile", $profile)
    }
    & video-forensics-export-visual-frames @visualArgs
    if ($LASTEXITCODE -ne 0) { throw "frame export failed for $($file.Name)" }

    & video-forensics-audio-samples $file.FullName `
        --output (Join-Path $out "audio_samples") `
        --ffmpeg $Ffmpeg `
        --ffprobe $Ffprobe
    if ($LASTEXITCODE -ne 0) { throw "audio analysis failed for $($file.Name)" }

    & video-forensics-submission-bundle (Join-Path $out "visual_frames") `
        --output (Join-Path $out "${safeStem}_email_review.zip")
    if ($LASTEXITCODE -ne 0) { throw "submission bundle failed for $($file.Name)" }

    & $Python -m video_forensics.native.bundle_decoder_results `
        (Join-Path $out "matrix") `
        --output (Join-Path $out "${safeStem}_matrix.zip")
    if ($LASTEXITCODE -ne 0) { throw "matrix bundle failed for $($file.Name)" }
}

Write-Host "Completed session: $sessionDir"
