# Deploy node-gamma to chetas-pentium-node (192.168.1.50)
Write-Host "Deploying shared package to 192.168.1.50..."
$shared_dir = Resolve-Path "../../packages/shared"
scp -r "$shared_dir" chetas@192.168.1.50:/home/chetas/axiom/packages/

Write-Host "Deploying node-gamma to 192.168.1.50..."
$source_dir = Resolve-Path "../../packages/node-gamma"
scp -r "$source_dir" chetas@192.168.1.50:/home/chetas/axiom/packages/
Write-Host "Done."