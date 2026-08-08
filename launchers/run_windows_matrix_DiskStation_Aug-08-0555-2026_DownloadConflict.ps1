param(
    [Parameter(Mandatory=$true)][ValidateSet("intel", "nvidia")][string]$Platform,
    [Parameter(Mandatory=$true)][string]$Video,
    [Parameter(Mandatory=$true)][string]$Output,
    [string]$Ffmpeg = "ffmpeg.exe",
    [string]$Ffprobe = "ffprobe.exe"
)

$ErrorActionPreference = "Stop"
$Profiles = @(
    "profiles/decoder_matrix/software_single_thread.json",
    "profiles/decoder_matrix/software_automatic_threads.json"
)

if ($Platform -eq "intel") {
    $Profiles += "profiles/decoder_matrix/windows_intel_qsv.json"
    $Profiles += "profiles/decoder_matrix/windows_intel_d3d11va.json"
} else {
    $Profiles += "profiles/decoder_matrix/windows_nvidia_d3d11va.json"
    $Profiles += "profiles/decoder_matrix/windows_nvidia_cuda.json"
}

New-Item -ItemType Directory -Force -Path $Output | Out-Null

foreach ($Profile in $Profiles) {
    python -m video_forensics.native.decoder_matrix $Video `
        --profile $Profile --output $Output --ffmpeg $Ffmpeg --ffprobe $Ffprobe

    python -m video_forensics.native.perceptual_decoder_run $Video `
        --profile $Profile --output $Output --ffmpeg $Ffmpeg
}

$Bundle = Join-Path (Split-Path -Parent $Output) ((Split-Path -Leaf $Output) + ".zip")
python -m video_forensics.native.bundle_decoder_results $Output --output $Bundle
Write-Host "Decoder matrix completed: $Output"
Write-Host "Bundle created: $Bundle"
