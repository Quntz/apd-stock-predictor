# Telegram Daily Briefing Setup

## Quick Start (3 minutes)

### Step 1: Create Telegram Bot
1. Open Telegram, search for `@BotFather`
2. Send: `/start`
3. Send: `/newbot`
4. Follow prompts (name, username)
5. Copy the **API Token** (looks like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### Step 2: Get Your Chat ID
1. Open Telegram, search for `@userinfobot`
2. Send: `/start`
3. Bot replies with your ID (looks like: `7016643189`)

### Step 3: Set Environment Variables

**On Mac/Linux:**
```bash
export TELEGRAM_BOT_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
export TELEGRAM_CHAT_ID="7016643189"
```

**Add to ~/.bashrc or ~/.zshrc for persistence:**
```bash
echo 'export TELEGRAM_BOT_TOKEN="YOUR-TOKEN"' >> ~/.zshrc
echo 'export TELEGRAM_CHAT_ID="YOUR-ID"' >> ~/.zshrc
source ~/.zshrc
```

### Step 4: Test It
```bash
cd Scrape.AI
python3 daily_summary_telegram.py
```

Expected output:
```
Generating Wall Street morning brief...

📊 WALL STREET MORNING BRIEF
...
✅ Message sent to Telegram
```

---

## Automated Daily Delivery

### Option A: Cron Job (Recommended)
```bash
# Edit crontab
crontab -e

# Add this line (9 AM daily)
0 9 * * * cd /path/to/Scrape.AI && python3 scraper.py && python3 analyze.py && python3 daily_summary_telegram.py

# Or run every 6 hours
0 */6 * * * cd /path/to/Scrape.AI && python3 scraper.py && python3 analyze.py && python3 daily_summary_telegram.py
```

### Option B: Systemd Timer (Advanced)
Create `/etc/systemd/system/wall-street-brief.service`:
```ini
[Unit]
Description=Wall Street Daily Brief
After=network.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'cd /path/to/Scrape.AI && python3 scraper.py && python3 analyze.py && python3 daily_summary_telegram.py'
User=your-username
Environment="TELEGRAM_BOT_TOKEN=YOUR-TOKEN"
Environment="TELEGRAM_CHAT_ID=YOUR-ID"
```

Create `/etc/systemd/system/wall-street-brief.timer`:
```ini
[Unit]
Description=Wall Street Brief Timer
Requires=wall-street-brief.service

[Timer]
OnCalendar=daily
OnCalendar=*-*-* 09:00:00

[Install]
WantedBy=timers.target
```

Enable:
```bash
systemctl enable wall-street-brief.timer
systemctl start wall-street-brief.timer
systemctl status wall-street-brief.timer
```

---

## Message Format

You'll receive messages like:

```
📊 WALL STREET MORNING BRIEF
Mon Feb 11, 09:00 GMT+8

✅ 156 topics scraped • Normal activity

SECTOR ACTIVITY
💻 Tech AAPL(12) | MSFT(10) | NVDA(15)
💰 Finance JPM(8) | BAC(6) | GS(4)
🏥 Healthcare UNH(7) | LLY(6) | JNJ(5)

TOP 5 STOCKS TO WATCH
1. NVDA 15 mentions
2. AAPL 12 mentions
3. MSFT 10 mentions
4. JPM 8 mentions
5. UNH 7 mentions

KEY THEMES
🔴 AI chip demand surge amid ChatGPT expansion
🟡 Microsoft cloud growth accelerates Q1
🟡 Fed signals potential rate cut in 2026
🟢 Tesla Cybertruck production scaled up

TRADING SIGNALS
💡 Tech leading (growth bullish)

WATCH LIST
• Fed policy expectations
• Tech earnings (AAPL, MSFT, NVDA)
• Options activity picking up
```

---

## Troubleshooting

### "Missing Telegram credentials"
```bash
# Check variables are set
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID

# If empty, set them again
export TELEGRAM_BOT_TOKEN="your-token"
export TELEGRAM_CHAT_ID="your-id"
```

### "Telegram error: 401"
- Invalid bot token
- Double-check @BotFather token

### "Telegram error: 403"
- Invalid chat ID
- Double-check @userinfobot chat ID
- Bot might be blocked

### "Database error: no such table"
- Run scraper.py first to create database
```bash
python3 scraper.py  # 2-3 minutes
python3 analyze.py  # 30 seconds
python3 daily_summary_telegram.py  # Sends message
```

---

## Manual Testing

Test without cron:
```bash
cd /path/to/Scrape.AI

# Full pipeline
python3 scraper.py
python3 analyze.py
python3 daily_summary_telegram.py

# Or just send existing data
python3 daily_summary_telegram.py
```

---

## What Gets Sent

✅ **Sent to Telegram:**
- Current market themes
- Top trending stocks
- Sector rotation signals
- Risk watch list
- Trading signal summary

❌ **NOT Sent:**
- Raw scraped data
- Detailed URLs
- Individual articles
- Sentiment analysis (optional)

---

## Next Steps

1. Get bot token from @BotFather
2. Get chat ID from @userinfobot
3. Set environment variables
4. Test: `python3 daily_summary_telegram.py`
5. Set up cron: `crontab -e`
6. Start receiving daily briefs! 📊

---

## Questions?

If it breaks, check:
1. Scraper.py runs successfully (creates social_topics.db)
2. analyze.py runs successfully (populates database)
3. Telegram credentials are correct
4. Network connection works

Run with debug:
```bash
python3 -u daily_summary_telegram.py 2>&1 | tee debug.log
```
