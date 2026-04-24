# Systemd Service Files

This directory contains draft and active service definitions for long-running AXIOM processes.

## Available Units

- [axiom-beta-api.service](D:\New folder\AXIOM\infra\systemd\axiom-beta-api.service): runs the FastAPI app for Node Beta on port `8000`
- [axiom-beta-scheduler.service](D:\New folder\AXIOM\infra\systemd\axiom-beta-scheduler.service): runs the APScheduler process for Node Beta
- [axiom-gamma-bot.service](D:\New folder\AXIOM\infra\systemd\axiom-gamma-bot.service): intended to run the Gamma bot process

## Production Readiness

- Beta API service is close to usable.
- Beta scheduler service is close to usable.
- Gamma bot service needs correction before use because its `Environment=` lines are malformed and will not parse as intended.

## Installation Pattern

Typical Linux install flow:

```bash
sudo cp infra/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable axiom-beta-api
sudo systemctl enable axiom-beta-scheduler
sudo systemctl start axiom-beta-api
sudo systemctl start axiom-beta-scheduler
```

Adjust usernames, paths, and environment-file locations before enabling services on a real host.
