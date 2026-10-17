#!/bin/bash
# Sample deploy script: reads REDIS_URL which is NOT in .env.example (MISSING)
echo "Connecting to ${REDIS_URL}"
echo "API key starts with ${API_KEY:0:4}"
redis-cli -u "$REDIS_URL" ping
