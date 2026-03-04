#!/bin/bash
# Install Docker and Docker Compose on Ubuntu (run with: sudo bash install-docker.sh)

set -e

# Prerequisites
apt-get update
apt-get install -y apt-transport-https ca-certificates curl software-properties-common

# Docker GPG key and repo
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine + Compose plugin
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Enable and start
systemctl enable docker
systemctl start docker

# Optional: allow your user to run docker without sudo
echo "To run Docker without sudo, run: sudo usermod -aG docker \$USER"
echo "Then log out and back in."
echo ""
echo "Docker: $(docker --version)"
echo "Docker Compose: $(docker compose version)"
