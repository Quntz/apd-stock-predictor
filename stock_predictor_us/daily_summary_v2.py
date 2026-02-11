#!/usr/bin/env python3
"""
Daily Wall Street News Summary - Better Format
Telegram-friendly, scannable, actionable

Output format:
- Headline summary (1 line)
- Market sectors (emojis + key movers)
- Top 5 stocks to watch
- Key themes (3-5 narratives)
- Risk alerts
- Action items
"""

import sqlite3
from datetime import datetime
from pathlib import Path

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
        print(f"Error: {e}")
        return None


def extract_stocks(topics):
    """Extract stock tickers from topics"""
    major_tickers = {
        'AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'META', 'TSLA', 'AMD', 'NFLX', 'INTC',
        'JPM', 'BAC', 'GS', 'V', 'MA', 'UNH', 'LLY', 'JNJ', 'PFE', 'XOM', 'CVX', 'BA',
        'WMT', 'COST', 'DIS', 'KO', 'MCD', 'NVDA', 'QCOM', 'AVGO'
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


def format_telegram_summary(data):
    """Format as Telegram-friendly morning briefing"""
    
    if not data or data['total'] == 0:
        return "⏳ Scraper running... Check back in a few minutes.\n\n(Need 50+ topics for full brief)"
    
    topics = data['topics']
    stocks = extract_stocks(topics)
    sectors = categorize_sectors(stocks)
    
    now = datetime.now().strftime('%a %b %d, %H:%M')
    
    # Build message
    msg = []
    msg.append("📊 WALL STREET MORNING BRIEF")
    msg.append(f"{now} GMT+8\n")
    
    # Headline
    if data['total'] >= 50:
        msg.append(f"✅ {data['total']} topics scraped • Normal market activity")
    else:
        msg.append(f"⏳ {data['total']} topics (need 50+) • Data still loading")
    msg.append("")
    
    # Sector breakdown
    msg.append("═══════════════════════════════════════════")
    msg.append("SECTOR ACTIVITY")
    msg.append("═══════════════════════════════════════════")
    
    for sector, stocks_list in sorted(sectors.items()):
        ticker_str = " | ".join([f"{s[0]}({s[1]})" for s in stocks_list[:3]])
        msg.append(f"{sector} {ticker_str}")
    
    msg.append("")
    
    # Top 5 stocks to watch
    msg.append("═══════════════════════════════════════════")
    msg.append("TOP 5 STOCKS TO WATCH")
    msg.append("═══════════════════════════════════════════")
    
    for i, (ticker, count) in enumerate(stocks[:5], 1):
        msg.append(f"{i}. {ticker:<8} {count:>2} mentions")
    
    msg.append("")
    
    # Key themes (from top topics)
    msg.append("═══════════════════════════════════════════")
    msg.append("KEY THEMES")
    msg.append("═══════════════════════════════════════════")
    
    themes_seen = set()
    theme_count = 0
    for topic, heat, platform in topics[:20]:
        # Extract main theme (first 50 chars)
        theme = topic[:60]
        if theme not in themes_seen and theme_count < 5:
            themes_seen.add(theme)
            heat_emoji = "🔴" if heat > 35 else "🟡" if heat > 25 else "🟢"
            msg.append(f"{heat_emoji} {theme}")
            msg.append(f"   Heat: {heat:.1f}")
            theme_count += 1
    
    msg.append("")
    
    # Trading signals
    msg.append("═══════════════════════════════════════════")
    msg.append("TRADING SIGNALS")
    msg.append("═══════════════════════════════════════════")
    
    tech_count = sum(s[1] for s in stocks if s[0] in ['AAPL', 'MSFT', 'NVDA', 'INTC', 'AMD'])
    fin_count = sum(s[1] for s in stocks if s[0] in ['JPM', 'BAC', 'GS', 'V', 'MA'])
    healthcare_count = sum(s[1] for s in stocks if s[0] in ['UNH', 'LLY', 'JNJ', 'PFE'])
    
    msg.append("💡 Sector Rotation Alert:")
    if tech_count > fin_count:
        msg.append("   → Tech leading (growth bullish)")
    elif fin_count > tech_count:
        msg.append("   → Finance leading (rate outlook)")
    else:
        msg.append("   → Balanced sector activity")
    
    msg.append(f"💡 Volume Alert:")
    if data['total'] > 100:
        msg.append("   → High chatter volume (good signal)")
    else:
        msg.append("   → Medium activity (normal)")
    
    msg.append("")
    
    # Risk alerts
    msg.append("═══════════════════════════════════════════")
    msg.append("⚠️  WATCH LIST")
    msg.append("═══════════════════════════════════════════")
    msg.append("• Macro: Fed policy expectations")
    msg.append("• Earnings: Tech mega-caps (AAPL, MSFT, NVDA)")
    msg.append("• Volatility: Options activity picking up")
    msg.append("")
    
    # Footer
    msg.append("═══════════════════════════════════════════")
    msg.append("Next update: 24 hours")
    msg.append("Data: Finviz + Yahoo Finance RSS")
    
    return "\n".join(msg)


if __name__ == "__main__":
    data = get_data()
    summary = format_telegram_summary(data)
    print(summary)
