param(
    [Parameter(Mandatory=$true)][string]$Video,
    [Parameter(Mandatory=$true)][string]$Output,
    [string]$Ffmpeg = "ffmpeg.exe",
    [string]$Ffprobe = "ffprobe.exe"
)
$ErrorActionPreference = "Stop"
python -m video_forensics.native.decoder_matrix $Video --profile profiles/decoder_matrix/software_single_thread.json --output $Output --ffmpeg $Ffmpeg --ffprobe $Ffprobe
python -m video_forensics.native.decoder_matrix $Video --profile profiles/decoder_matrix/software_automatic_threads.json --output $Output --ffmpeg $Ffmpeg --ffprobe $Ffprobe
python -m video_forensics.native.decoder_matrix $Video --profile profiles/decoder_matrix/windows_nvidia_d3d11va.json --output $Output --ffmpeg $Ffmpeg --ffprobe $Ffprobe
python -m video_forensics.native.decoder_matrix $Video --profile profiles/decoder_matrix/windows_nvidia_cuda.json --output $Output --ffmpeg $Ffmpeg --ffprobe $Ffprobe
