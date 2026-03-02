#!/bin/bash
set -e

# ---------------------------------------------------------
# SELECT YOUR PLATFORM BY CHANGING THE COMPOSE FILE:
#
# GPU (AMD ROCm)  → docker-compose.gpu.yaml
# CPU (Intel/Windows/Linux) → docker-compose.cpu.yaml
# ARM (Apple Silicon M1/M2/M3) → docker-compose.arm.yaml
#
# Example:
#   sudo docker compose -f docker-compose.cpu.yaml up -d
# ---------------------------------------------------------

COMPOSE_FILE="docker-compose.gpu.yaml"   # <--- CHANGE THIS LINE

# ---------------------------------------------------------
# Build and start the selected environment
# ---------------------------------------------------------
sudo docker compose -f "$COMPOSE_FILE" build
sudo docker compose -f "$COMPOSE_FILE" up -d

# ---------------------------------------------------------
# Pull the model inside the Ollama container
# ---------------------------------------------------------
sudo docker exec -it ollama ollama pull qwen2.5:7b

# ---------------------------------------------------------
# Open the docx2md container for interactive work
# ---------------------------------------------------------
clear
sudo docker exec -it docx2md bash
