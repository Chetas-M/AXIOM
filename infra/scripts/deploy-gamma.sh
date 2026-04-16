#!/bin/bash
# Deployment script for gamma
echo "Deploying shared package to 192.168.1.50..."
scp -r "../../packages/shared" chetas@192.168.1.50:/home/chetas/axiom/packages/

echo "Deploying node-gamma to 192.168.1.50..."
scp -r "../../packages/node-gamma" chetas@192.168.1.50:/home/chetas/axiom/packages/
echo "Done."
