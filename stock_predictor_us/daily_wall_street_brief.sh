#!/bin/bash
# Daily Wall Street Brief Generator
# Add to crontab: 0 9 * * * /path/to/daily_wall_street_brief.sh

set -e

# Paths
SCRAPE_AI_DIR="/tmp/Scrape.AI"
BRIEF_SCRIPT="$HOME/.openclaw/workspace/stock_predictor_us/wall_street_brief_telegram.py"
LOG_FILE="/tmp/wall_street_brief.log"

# Timestamp
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Wall Street Brief generation..." >> "$LOG_FILE"

# Step 1: Run scraper
if [ -d "$SCRAPE_AI_DIR" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running scraper..." >> "$LOG_FILE"
    cd "$SCRAPE_AI_DIR"
    python3 scraper.py 2>&1 | tail -20 >> "$LOG_FILE"
    
    # Step 2: Run analyzer
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running analyzer..." >> "$LOG_FILE"
    python3 analyze.py 2>&1 | tail -10 >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Scrape.AI not found at $SCRAPE_AI_DIR" >> "$LOG_FILE"
    exit 1
fi

# Step 3: Generate briefing
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Generating briefing..." >> "$LOG_FILE"

if [ -f "$BRIEF_SCRIPT" ]; then
    BRIEFING=$(python3 "$BRIEF_SCRIPT" 2>&1)
    
    # Save to file for reference
    echo "$BRIEFING" > "/tmp/wall_street_brief_latest.txt"
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Briefing generated successfully" >> "$LOG_FILE"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $(echo "$BRIEFING" | wc -l) lines" >> "$LOG_FILE"
    
    # TODO: Send via OpenClaw message tool
    # (Requires OpenClaw daemon context)
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Ready for delivery" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Brief script not found at $BRIEF_SCRIPT" >> "$LOG_FILE"
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Complete" >> "$LOG_FILE"
