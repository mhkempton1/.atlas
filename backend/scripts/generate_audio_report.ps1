$ErrorActionPreference = "Stop"

# Define Paths
$reportPath = "c:\Users\mhkem\.atlas\OVERNIGHT_REPORT.md"
$outputPath = "c:\Users\mhkem\.atlas\OVERNIGHT_REPORT.wav"

if (-not (Test-Path $reportPath)) {
    Write-Error "Report not found at $reportPath"
}

# 1. Read and Clean Text for Speech
$text = Get-Content $reportPath -Raw

# Remove markdown symbols for better speech
$cleanText = $text -replace '#+ ', '' # Headings
$cleanText = $cleanText -replace '\*\*([^\*]+)\*\*', '$1' # Bold
$cleanText = $cleanText -replace '\* ', 'Point: ' # Bullet points
$cleanText = $cleanText -replace '`', '' # Code ticks
$cleanText = $cleanText -replace '\[([^\]]+)\]\([^\)]+\)', '$1' # Links

$intro = "Atlas Overnight Intelligence Report. Date: February 11th, 2026. `n"
$finalText = $intro + $cleanText

# 2. Synthesize to File
Write-Host "Synthesizing to $outputPath..."
Add-Type -AssemblyName System.Speech
$synth = New-Object -TypeName System.Speech.Synthesis.SpeechSynthesizer
$synth.SetOutputToWaveFile($outputPath)
$synth.Speak($finalText)
$synth.Dispose()

Write-Host "✅ Audio report generated successfully."
