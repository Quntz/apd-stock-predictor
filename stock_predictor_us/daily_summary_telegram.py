#!/usr/bin/env python3
"""
Daily Wall Street News Summary → Telegram Delivery
Sends morning briefing directly to your Telegram chat

Setup:
1. Get Telegram Bot Token from @BotFather
2. Set environment variable: export TELEGRAM_BOT_TOKEN="your-token"
3. Get your Chat ID: https://api.telegram.org/bot<TOKEN>/getUpdates
4. Export TELEGRAM_CHAT_ID="your-id"
5. Run: python3 daily_summary_telegram.py
"""

import sqlite3
import os
import requests
from datetime import datetime
from pathlib import Path
import sys


def get_data():
    """Read topics from social_topics.db"""
    db_path = Path("social_topics.db")
    
    if not db_path.exists():
        return None
    
    try:
        conn = sqlite3.connect("social_topics.db")
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM topics WHERE topic IS NOT NULL AND topic != ''")
        total = cur.fetchone()[0]
        
        cur.execute("""
            SELECT topic, heat_score, platform 
            FROM topics 
            ORDER BY heat_score DESC 
            LIMIT 50
        """)
        topics = cur.fetchall()
        
        conn.close()
        return {'total': total, 'topics': topics}
        
    except Exception as e:
        print(f"Error reading DB: {e}")
        return None


def extract_stocks(topics):
    """Extract stock tickers from topics"""
    major_tickers = {
        'AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'META', 'TSLA', 'AMD', 'NFLX', 'INTC',
        'JPM', 'BAC', 'GS', 'V', 'MA', 'UNH', 'LLY', 'JNJ', 'PFE', 'XOM', 'CVX', 'BA',
        'WMT', 'COST', 'DIS', 'KO', 'MCD', 'QCOM', 'AVGO'
    }
    
    stock_counts = {}
    for topic, heat, _ in topics:
        words = topic.upper().split()
        for word in words:
            if word in major_tickers:
                stock_counts[word] = stock_counts.get(word, 0) + 1
    
    return sorted(stock_counts.items(), key=lambda x: x[1], reverse=True)


def categorize_sectors(stocks):
    """Categorize stocks by sector"""
    sectors = {
        '💻 Tech': ['AAPL', 'MSFT', 'NVDA', 'INTC', 'AMD', 'QCOM', 'NFLX', 'META', 'GOOGL'],
        '💰 Finance': ['JPM', 'BAC', 'GS', 'V', 'MA', 'WFC', 'PNC'],
        '🏥 Healthcare': ['UNH', 'LLY', 'JNJ', 'PFE', 'MRK'],
        '🛢️ Energy': ['XOM', 'CVX', 'COP', 'MPC'],
        '🚗 Industrial': ['BA', 'CAT', 'GE', 'UBER'],
        '🛒 Consumer': ['WMT', 'COST', 'TJX', 'DIS', 'KO', 'MCD'],
        '🚀 Growth': ['TSLA', 'AMZN', 'AVGO'],
    }
    
    sector_activity = {}
    for sector, tickers in sectors.items():
        stocks_in_sector = [s for s in stocks if s[0] in tickers]
        if stocks_in_sector:
            sector_activity[sector] = stocks_in_sector
    
    return sector_activity


def format_summary(data):
    """Format as Telegram-friendly morning briefing"""
    
    if not data or data['total'] == 0:
        return "⏳ *Scraper running...*\n\nCheck back in a few minutes.\n(Need 50+ topics for full brief)"
    
    topics = data['topics']
    stocks = extract_stocks(topics)
    sectors = categorize_sectors(stocks)
    
    now = datetime.now().strftime('%a %b %d, %H:%M')
    
    # Build message
    msg = []
    msg.append("📊 *WALL STREET MORNING BRIEF*")
    msg.append(f"`{now} GMT+8`\n")
    
    # Headline
    if data['total'] >= 50:
        msg.append(f"✅ {data['total']} topics scraped • Normal activity")
    else:
        msg.append(f"⏳ {data['total']} topics (need 50+) • Data loading")
    msg.append("")
    
    # Sector breakdown
    msg.append("*SECTOR ACTIVITY*")
    
    for sector, stocks_list in sorted(sectors.items()):
        ticker_str = " | ".join([f"{s[0]}({s[1]})" for s in stocks_list[:3]])
        msg.append(f"{sector} {ticker_str}")
    
    msg.append("")
    
    # Top 5 stocks
    msg.append("*TOP 5 STOCKS TO WATCH*")
    
    for i, (ticker, count) in enumerate(stocks[:5], 1):
        msg.append(f"{i}\\. `{ticker:<8}` {count:>2} mentions")
    
    msg.append("")
    
    # Key themes
    msg.append("*KEY THEMES*")
    
    themes_seen = set()
    theme_count = 0
    for topic, heat, platform in topics[:20]:
        theme = topic[:55]
        if theme not in themes_seen and theme_count < 4:
            themes_seen.add(theme)
            heat_emoji = "🔴" if heat > 35 else "🟡" if heat > 25 else "🟢"
            msg.append(f"{heat_emoji} _{theme}_")
            theme_count += 1
    
    msg.append("")
    
    # Signals
    msg.append("*TRADING SIGNALS*")
    
    tech_count = sum(s[1] for s in stocks if s[0] in ['AAPL', 'MSFT', 'NVDA', 'INTC', 'AMD'])
    fin_count = sum(s[1] for s in stocks if s[0] in ['JPM', 'BAC', 'GS', 'V', 'MA'])
    
    if tech_count > fin_count:
        msg.append("💡 Tech leading (growth bullish)")
    elif fin_count > tech_count:
        msg.append("💡 Finance leading (rate outlook)")
    else:
        msg.append("💡 Balanced sector activity")
    
    msg.append("")
    msg.append("*WATCH LIST*")
    msg.append("• Fed policy expectations")
    msg.append("• Tech earnings (AAPL, MSFT, NVDA)")
    msg.append("• Options activity picking up")
    
    return "\n".join(msg)


def send_telegram(message, bot_token=None, chat_id=None):
    """Send message to Telegram"""
    
    bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ Missing Telegram credentials")
        print("   Set: export TELEGRAM_BOT_TOKEN='your-token'")
        print("   Set: export TELEGRAM_CHAT_ID='your-chat-id'")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("✅ Message sent to Telegram")
            return True
        else:
            print(f"❌ Telegram error: {response.status_code}")
            print(f"   {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending Telegram: {e}")
        return False


def main():
    """Run scraper summary and send to Telegram"""
    
    print("Generating Wall Street morning brief...")
    
    data = get_data()
    summary = format_summary(data)
    
    # Print to console
    print("\n" + summary)
    print("\n")
    
    # Send to Telegram
    if send_telegram(summary):
        print("Daily brief sent! ✅")
        return 0
    else:
        print("Failed to send. Try setting credentials manually.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
