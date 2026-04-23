param(
    [string]$BetaIp = "192.168.X.X",
    [string]$BetaUser = "user",
    [string]$GammaIp = "192.168.Y.Y",
    [string]$GammaUser = "user",
    [string]$WorkspacePath = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
)

$BuildDir = "$WorkspacePath\build"

function Copy-DeployTree {
    param(
        [string]$Source,
        [string]$Destination
    )

    $excludeDirs = @(".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build")
    $excludeFiles = @("*.pyc", "*.pyo", ".DS_Store")

    if (-not (Test-Path $Destination)) {
        New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    }

    Get-ChildItem -Path $Source -Recurse -File | Where-Object {
        $fullPath = $_.FullName
        $skipDir = $false
        foreach ($dir in $excludeDirs) {
            if ($fullPath -match [regex]::Escape("\$dir\")) {
                $skipDir = $true
                break
            }
        }
        if ($skipDir) { return $false }

        foreach ($pattern in $excludeFiles) {
            if ($_.Name -like $pattern) {
                return $false
            }
        }
        return $true
    } | ForEach-Object {
        $relative = $_.FullName.Substring($Source.Length).TrimStart('\')
        $target = Join-Path $Destination $relative
        $targetDir = Split-Path -Parent $target
        if (-not (Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }
        Copy-Item -LiteralPath $_.FullName -Destination $target -Force
    }
}

# Clean and create build directory
if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir }
New-Item -ItemType Directory -Path $BuildDir | Out-Null

Write-Host "?? Packaging Node-Beta..." -ForegroundColor Cyan
$BetaTemp = "$BuildDir\node-beta-deploy"
New-Item -ItemType Directory -Path $BetaTemp | Out-Null
Copy-DeployTree -Source "$WorkspacePath\packages\node-beta" -Destination "$BetaTemp\node-beta"
Copy-DeployTree -Source "$WorkspacePath\packages\shared" -Destination "$BetaTemp\shared"
Copy-DeployTree -Source "$WorkspacePath\infra\systemd" -Destination "$BetaTemp\infra\systemd"
Copy-DeployTree -Source "$WorkspacePath\infra\scripts" -Destination "$BetaTemp\infra\scripts"
Set-Location -Path $BetaTemp
tar.exe -czf "$BuildDir\node-beta.tar.gz" .
Set-Location -Path $WorkspacePath

Write-Host "?? Packaging Node-Gamma..." -ForegroundColor Cyan
$GammaTemp = "$BuildDir\node-gamma-deploy"
New-Item -ItemType Directory -Path $GammaTemp | Out-Null
Copy-DeployTree -Source "$WorkspacePath\packages\node-gamma" -Destination "$GammaTemp\node-gamma"
Copy-DeployTree -Source "$WorkspacePath\packages\shared" -Destination "$GammaTemp\shared"
Copy-DeployTree -Source "$WorkspacePath\infra\systemd" -Destination "$GammaTemp\infra\systemd"
Copy-DeployTree -Source "$WorkspacePath\infra\scripts" -Destination "$GammaTemp\infra\scripts"
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
