# Export a .pptx to one PNG per slide via PowerPoint COM.
#
# This doubles as the corruption test: if the package is malformed, PowerPoint
# raises a repair prompt and Presentations.Open fails rather than returning.
#
#   powershell -File tools/shoot_pptx.ps1 -Deck tests/reference-smoke.pptx
param(
    [Parameter(Mandatory = $true)][string]$Deck,
    [string]$OutDir = "$env:TEMP\claude\pptxshots"
)

$deckPath = (Resolve-Path $Deck).Path
if (Test-Path $OutDir) { Remove-Item $OutDir -Recurse -Force }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$ppt = New-Object -ComObject PowerPoint.Application
try {
    # msoTrue/msoFalse: ReadOnly, Untitled, WithWindow
    $pres = $ppt.Presentations.Open($deckPath, -1, 0, 0)
    $pres.SaveCopyAs($OutDir, 18)   # 18 = ppSaveAsPNG, one file per slide
    Write-Output "slides: $($pres.Slides.Count)"
    $pres.Close()
}
finally {
    $ppt.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($ppt) | Out-Null
}

Get-ChildItem -Path $OutDir -Recurse -Filter *.PNG | ForEach-Object { $_.FullName }
