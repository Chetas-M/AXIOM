# Nginx Configurations

This directory is reserved for reverse-proxy configuration that can sit in front of AXIOM services, especially the Beta API.

## Intended Uses

- expose Node Beta safely on an internal network
- terminate TLS in front of FastAPI services
- route stable hostnames to Alpha, Beta, or Gamma where needed

## Current State

- no concrete Nginx config files are committed yet
- treat this folder as a placeholder for future proxy assets

If you operationalize Nginx for this project, document the chosen ports, upstreams, and auth model here alongside the config files.
