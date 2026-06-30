#!/bin/bash

# Sovereign Watchdog - Self-Healing Monitor
# Target: agent-api container
# Action: Restart container if health check fails

SVR_NAME="agent-api"
HEALTH_URL="http://localhost:8000/health"
LOG_FILE="/var/log/sovereign_watchdog.log"

echo "🕒 $(date): Sovereign Watchdog Started. Monitoring $SVR_NAME..." >> $LOG_FILE

while true; do
    # Check if the API responds with a 200 OK
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

    if [ "$STATUS" != "200" ]; then
        echo "🚨 $(date): $SVR_NAME is UNHEALTHY (Status: $STATUS). Restarting..." >> $LOG_FILE
        docker restart $SVR_NAME
        # Wait for service to come back up
        sleep 30
    fi
    
    # Check every 60 seconds
    sleep 60
done
