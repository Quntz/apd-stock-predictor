#!/usr/bin/env python3
"""
Daily Wall Street Brief → Telegram via OpenClaw

Reads from Scrape.AI database and sends formatted morning brief
Uses OpenClaw's message delivery (no separate bot needed)

Run: python3 wall_street_brief_telegram.py
"""

import sqlite3
import json
import sys
from datetime import datetime
from pathlib import Path


def get_data(db_path="/tmp/Scrape.AI/social_topics.db"):
    """Read topics from social_topics.db"""
    
    if not Path(db_path).exists():
        return None
    
    try:
        conn = sqlite3.connect(db_path)
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
        msg.append("💡 Tech leading \\(growth bullish\\)")
    elif fin_count > tech_count:
        msg.append("💡 Finance leading \\(rate outlook\\)")
    else:
        msg.append("💡 Balanced sector activity")
    
    msg.append("")
    msg.append("*WATCH LIST*")
    msg.append("• Fed policy expectations")
    msg.append("• Tech earnings \\(AAPL, MSFT, NVDA\\)")
    msg.append("• Options activity picking up")
    
    return "\n".join(msg)


def print_for_openclaw(message):
    """
    Output formatted for OpenClaw integration
    
    OpenClaw will read stdout and send via message tool
    Just print the message and OpenClaw handles delivery
    """
    print(message)
    return message


def main():
    """Generate and output Wall Street morning brief"""
    
    # Check if running from Scrape.AI directory
    if not Path("/tmp/Scrape.AI/social_topics.db").exists():
        print("Note: Database not found in /tmp/Scrape.AI")
        print("Make sure scraper.py has run first")
        print("If using different path, modify db_path in this script")
    
    data = get_data()
    summary = format_summary(data)
    
    # Output for OpenClaw delivery
    print_for_openclaw(summary)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
