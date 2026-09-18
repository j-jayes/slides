# Export a .pptx to one PNG per slide via PowerPoint COM, and optionally a PDF.
#
# This doubles as the corruption test: if the package is malformed, PowerPoint
# raises a repair prompt and Presentations.Open fails rather than returning.
#
#   powershell -File tools/shoot_pptx.ps1 -Deck ../reports/my-deck.pptx
#   powershell -File tools/shoot_pptx.ps1 -Deck deck.pptx -Pdf deck.pdf
#
# PowerPoint is the only renderer here, and the right one: it is what the
# colleague will open the deck in, so what it draws is what they will see.
param(
    [Parameter(Mandatory = $true)][string]$Deck,
    [string]$OutDir = "$env:TEMP\claude\pptxshots",
    [string]$Pdf
)

$deckPath = (Resolve-Path $Deck).Path
if (Test-Path $OutDir) { Remove-Item $OutDir -Recurse -Force }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

# New-Object -ComObject returns the RUNNING PowerPoint if there is one, and
# quitting it would close the decks the user has open. So attach when one is
# already running, and only quit an instance this script started.
try {
    $ppt = [System.Runtime.InteropServices.Marshal]::GetActiveObject("PowerPoint.Application")
    $attached = $true
}
catch {
    $ppt = New-Object -ComObject PowerPoint.Application
    $attached = $false
}

# Likewise, a deck the user already has open must not be closed underneath
# them -- Presentations.Open would just hand back the open window.
$pres = $null
foreach ($p in $ppt.Presentations) {
    if ($p.FullName -eq $deckPath) { $pres = $p; break }
}
$wasOpen = $null -ne $pres

try {
    # msoTrue/msoFalse: ReadOnly, Untitled, WithWindow
    if (-not $wasOpen) { $pres = $ppt.Presentations.Open($deckPath, -1, 0, 0) }
    $pres.SaveCopyAs($OutDir, 18)   # 18 = ppSaveAsPNG, one file per slide
    if ($Pdf) {
        # SaveCopyAs, not SaveAs: SaveAs repoints the open presentation at the
        # new file, and on a labelled deck it can raise a modal label prompt
        # that never returns when nobody is at the keyboard.
        $pdfPath = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine((Get-Location).Path, $Pdf))
        $pres.SaveCopyAs($pdfPath, 32)   # 32 = ppSaveAsPDF
        Write-Output "pdf: $pdfPath"
    }
    Write-Output "slides: $($pres.Slides.Count)"
    if (-not $wasOpen) { $pres.Close() }
}
finally {
    if (-not $attached) { $ppt.Quit() }
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($ppt) | Out-Null
}

Get-ChildItem -Path $OutDir -Recurse -Filter *.PNG | ForEach-Object { $_.FullName }
