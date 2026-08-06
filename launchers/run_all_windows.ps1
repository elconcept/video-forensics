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
$hostProfile = Join-Path $ResultsDir "host_profile_${session}.json"

& video-forensics-host-profile --output $hostProfile
if ($LASTEXITCODE -ne 0) { throw "host-profile failed" }

function Get-FfmpegHwAccels([string]$FfmpegPath) {
    $output = & $FfmpegPath -hide_banner -hwaccels 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Nie udało się odczytać akceleratorów FFmpeg."
    }
    return @(
        $output | ForEach-Object { $_.ToString().Trim().ToLowerInvariant() } |
            Where-Object { $_ -match '^[a-z0-9_]+$' }
    )
}

function Get-DetectedGpu {
    $controllers = @(Get-CimInstance -ClassName Win32_VideoController -ErrorAction Stop)
    $presentDisplayIds = @()
    if (Get-Command Get-PnpDevice -ErrorAction SilentlyContinue) {
        $presentDisplayIds = @(
            Get-PnpDevice -Class Display -PresentOnly -ErrorAction SilentlyContinue |
                Where-Object { $_.Status -eq "OK" } |
                ForEach-Object { $_.InstanceId }
        )
    }

    return @(
        $controllers | Where-Object {
            $_.ConfigManagerErrorCode -eq 0 -and
            ($presentDisplayIds.Count -eq 0 -or $presentDisplayIds -contains $_.PNPDeviceID)
        } | ForEach-Object {
            $vendor = "Other"
            if ($_.Name -match '(?i)Intel') { $vendor = "Intel" }
            elseif ($_.Name -match '(?i)NVIDIA') { $vendor = "NVIDIA" }
            elseif ($_.Name -match '(?i)AMD|Radeon|Advanced Micro Devices') { $vendor = "AMD" }

            [PSCustomObject]@{
                Name = $_.Name
                Vendor = $vendor
                PNPDeviceID = $_.PNPDeviceID
                DriverVersion = $_.DriverVersion
                Status = $_.Status
                ConfigManagerErrorCode = $_.ConfigManagerErrorCode
            }
        }
    )
}

function Add-ProfileIfUsable(
    [System.Collections.Generic.List[string]]$ProfileList,
    [string]$ProfilePath,
    [bool]$Condition
) {
    if ($Condition -and (Test-Path -LiteralPath $ProfilePath)) {
        if (-not $ProfileList.Contains($ProfilePath)) {
            $ProfileList.Add($ProfilePath)
        }
    }
}

$gpus = @(Get-DetectedGpu)
if ($gpus.Count -eq 0) {
    Write-Warning "Nie wykryto aktywnego kontrolera GPU. Zostaną uruchomione tylko profile programowe."
}
else {
    Write-Host "Wykryte aktywne GPU:"
    $gpus | Format-Table Name, Vendor, DriverVersion, Status -AutoSize
}

$gpuInventoryPath = Join-Path $sessionDir "windows_gpu_inventory.json"
$gpus | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $gpuInventoryPath -Encoding UTF8

$hwaccels = @(Get-FfmpegHwAccels $Ffmpeg)
$hwaccelPath = Join-Path $sessionDir "ffmpeg_hwaccels.json"
$hwaccels | ConvertTo-Json | Set-Content -LiteralPath $hwaccelPath -Encoding UTF8

$hasIntel = @($gpus | Where-Object { $_.Vendor -eq "Intel" }).Count -gt 0
$hasNvidia = @($gpus | Where-Object { $_.Vendor -eq "NVIDIA" }).Count -gt 0
$hasAmd = @($gpus | Where-Object { $_.Vendor -eq "AMD" }).Count -gt 0
$hasD3d11va = $hwaccels -contains "d3d11va"
$hasQsv = $hwaccels -contains "qsv"
$hasCuda = $hwaccels -contains "cuda"

$profiles = [System.Collections.Generic.List[string]]::new()
Add-ProfileIfUsable $profiles "profiles\decoder_matrix\software_single_thread.json" $true
Add-ProfileIfUsable $profiles "profiles\decoder_matrix\software_automatic_threads.json" $true
Add-ProfileIfUsable $profiles "profiles\decoder_matrix\windows_intel_qsv.json" ($hasIntel -and $hasQsv)
Add-ProfileIfUsable $profiles "profiles\decoder_matrix\windows_intel_d3d11va.json" ($hasIntel -and $hasD3d11va)
Add-ProfileIfUsable $profiles "profiles\decoder_matrix\windows_nvidia_d3d11va.json" ($hasNvidia -and $hasD3d11va)
Add-ProfileIfUsable $profiles "profiles\decoder_matrix\windows_nvidia_cuda.json" ($hasNvidia -and $hasCuda)
Add-ProfileIfUsable $profiles "profiles\decoder_matrix\windows_amd_d3d11va.json" ($hasAmd -and $hasD3d11va)

if ($profiles.Count -eq 0) {
    throw "Nie znaleziono żadnego istniejącego profilu dekodera."
}

Write-Host "Profile wybrane na podstawie GPU i możliwości FFmpeg:"
$profiles | ForEach-Object { Write-Host "  - $_" }

foreach ($file in $files) {
    $safeStem = $file.BaseName -replace '[^A-Za-z0-9._-]', '_'
    $fileRoot = Join-Path $ResultsDir $safeStem
    $out = Join-Path $fileRoot $session
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


    & video-forensics-result-summary $out
    if ($LASTEXITCODE -ne 0) { throw "summary failed for $($file.Name)" }

    & video-forensics-cross-run-compare $fileRoot
    if ($LASTEXITCODE -ne 0) { throw "cross-run comparison failed for $($file.Name)" }
}

Write-Host "Completed session timestamp: $session"
