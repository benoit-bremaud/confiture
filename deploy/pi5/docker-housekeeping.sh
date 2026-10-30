#!/bin/sh
# Free the disk space that Docker updates leave behind on the Pi 5.
# Removes images no container (running or stopped) uses, and the BuildKit cache.
# Never touches volumes, containers or networks: `docker system prune` would.
set -eu

df_before=$(df --output=used -B1M / | tail -n 1)
docker image prune -a -f
docker builder prune -f
df_after=$(df --output=used -B1M / | tail -n 1)

echo "docker-housekeeping: freed $((df_before - df_after)) MiB on /"
