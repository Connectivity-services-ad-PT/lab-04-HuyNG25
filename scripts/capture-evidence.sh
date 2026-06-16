#!/usr/bin/env bash
# scripts/capture-evidence.sh
# Capture health check output and save to docs/evidence/
set -euo pipefail

EVIDENCE_DIR="docs/evidence"
mkdir -p "$EVIDENCE_DIR"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H-%M-%SZ")
HEALTH_LOG="$EVIDENCE_DIR/health-check-$TIMESTAMP.log"

echo "=== FIT4110 Lab 04 – Health Check Evidence ===" > "$HEALTH_LOG"
echo "Timestamp: $TIMESTAMP" >> "$HEALTH_LOG"
echo "Service: notification-service (B7)" >> "$HEALTH_LOG"
echo "Team: team-notify" >> "$HEALTH_LOG"
echo "" >> "$HEALTH_LOG"
echo "--- curl http://localhost:8000/health ---" >> "$HEALTH_LOG"
curl -s http://localhost:8000/health | python3 -m json.tool >> "$HEALTH_LOG" 2>&1
echo "" >> "$HEALTH_LOG"
echo "--- docker ps ---" >> "$HEALTH_LOG"
docker ps --filter "name=fit4110-notify-lab04" --format "table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" >> "$HEALTH_LOG" 2>&1

echo "Evidence saved to: $HEALTH_LOG"
cat "$HEALTH_LOG"
