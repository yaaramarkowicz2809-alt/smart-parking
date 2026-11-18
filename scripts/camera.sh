#!/usr/bin/env bash
# IoT camera simulator - sends HTTP POST requests to the API, like the real camera.
# Usage:
#   ./scripts/camera.sh               -> sends 5 random plates
#   ./scripts/camera.sh 12-345-67     -> sends one specific plate
#   N=12 ./scripts/camera.sh          -> sends 12 random plates (try it to trigger FULL CAPACITY)

API_URL="${API_URL:-http://localhost:5000/api/entry}"

send() {
  echo "📷 Camera detected plate: $1"
  curl -s -X POST "$API_URL" -H "Content-Type: application/json" -d "{\"plate\":\"$1\"}"
  echo; echo
}

if [ -n "$1" ]; then
  send "$1"
else
  for i in $(seq 1 "${N:-5}"); do
    send "$(printf '%02d-%03d-%02d' $((RANDOM % 100)) $((RANDOM % 1000)) $((RANDOM % 100)))"
    sleep 1
  done
fi
