# Fix Startup Script Line Endings for Azure

Write-Host "Converting startup.sh to Unix line endings (LF)..." -ForegroundColor Cyan

$file = "startup.sh"

if (Test-Path $file) {
    # Read content and convert CRLF to LF
    $content = Get-Content $file -Raw
    $content = $content -replace "`r`n", "`n"
    
    # Write back without newline at end
    [System.IO.File]::WriteAllText((Resolve-Path $file), $content, [System.Text.UTF8Encoding]::new($false))
    
    Write-Host "Success! Line endings converted." -ForegroundColor Green
    Write-Host "File: $file" -ForegroundColor Gray
} else {
    Write-Host "Error: File not found: $file" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Commit and push changes to GitHub"
Write-Host "2. Set startup command in Azure Portal: bash startup.sh"
Write-Host "3. Add environment variables (see AZURE_FIX.md)"
