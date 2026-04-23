param(
    [string]$BetaIp = "192.168.X.X",
    [string]$BetaUser = "user",
    [string]$GammaIp = "192.168.Y.Y",
    [string]$GammaUser = "user"
)

$WorkspacePath = "D:\New folder\AXIOM"
$BuildDir = "$WorkspacePath\build"

# Clean and create build directory
if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir }
New-Item -ItemType Directory -Path $BuildDir | Out-Null

Write-Host "?? Packaging Node-Beta..." -ForegroundColor Cyan
$BetaTemp = "$BuildDir\node-beta-deploy"
New-Item -ItemType Directory -Path $BetaTemp | Out-Null
Copy-Item -Recurse "$WorkspacePath\packages\node-beta" "$BetaTemp\node-beta"
Copy-Item -Recurse "$WorkspacePath\packages\shared" "$BetaTemp\shared"
Copy-Item -Recurse "$WorkspacePath\infra" "$BetaTemp\infra"
Set-Location -Path $BetaTemp
tar.exe -czf "$BuildDir\node-beta.tar.gz" .
Set-Location -Path $WorkspacePath

Write-Host "?? Packaging Node-Gamma..." -ForegroundColor Cyan
$GammaTemp = "$BuildDir\node-gamma-deploy"
New-Item -ItemType Directory -Path $GammaTemp | Out-Null
Copy-Item -Recurse "$WorkspacePath\packages\node-gamma" "$GammaTemp\node-gamma"
Copy-Item -Recurse "$WorkspacePath\packages\shared" "$GammaTemp\shared"
Copy-Item -Recurse "$WorkspacePath\infra" "$GammaTemp\infra"
Set-Location -Path $GammaTemp
tar.exe -czf "$BuildDir\node-gamma.tar.gz" .
Set-Location -Path $WorkspacePath

Write-Host "`n? Packaging Complete! Here are the commands to transfer them:`n" -ForegroundColor Green

Write-Host "To deploy to Beta Node:" -ForegroundColor Yellow
Write-Host "scp $BuildDir\node-beta.tar.gz ${BetaUser}@${BetaIp}:~/"
Write-Host "ssh ${BetaUser}@${BetaIp} `"mkdir -p ~/axiom-beta && tar -xzf ~/node-beta.tar.gz -C ~/axiom-beta && cd ~/axiom-beta && python3 -m venv venv && source venv/bin/activate && pip install -r node-beta/requirements.txt`""

Write-Host "`nTo deploy to Gamma Node:" -ForegroundColor Yellow
Write-Host "scp $BuildDir\node-gamma.tar.gz ${GammaUser}@${GammaIp}:~/"
Write-Host "ssh ${GammaUser}@${GammaIp} `"mkdir -p ~/axiom-gamma && tar -xzf ~/node-gamma.tar.gz -C ~/axiom-gamma && cd ~/axiom-gamma && python3 -m venv venv && source venv/bin/activate && pip install -r node-gamma/requirements.txt`""
