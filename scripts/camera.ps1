# IoT camera simulator for Windows PowerShell (no extra installs needed).
# Usage:
#   .\scripts\camera.ps1                 -> sends 5 random plates
#   .\scripts\camera.ps1 -Plate 12-345-67 -> sends one plate
#   .\scripts\camera.ps1 -Count 12        -> sends 12 plates (triggers FULL CAPACITY)
param(
  [string]$Plate,
  [int]$Count = 5,
  [string]$ApiUrl = "http://localhost:5000/api/entry"
)

function Send-Plate($p) {
  Write-Host "Camera detected plate: $p"
  try {
    $res = Invoke-RestMethod -Method Post -Uri $ApiUrl -ContentType "application/json" `
           -Body (@{ plate = $p } | ConvertTo-Json)
    Write-Host "  -> docked as $($res.car.ship_class)" -ForegroundColor Green
  } catch {
    Write-Host "  -> $($_.ErrorDetails.Message)" -ForegroundColor Red
  }
}

if ($Plate) { Send-Plate $Plate }
else {
  1..$Count | ForEach-Object {
    $p = "{0:D2}-{1:D3}-{2:D2}" -f (Get-Random -Max 100), (Get-Random -Max 1000), (Get-Random -Max 100)
    Send-Plate $p
    Start-Sleep -Seconds 1
  }
}
