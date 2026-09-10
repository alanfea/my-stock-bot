import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
from datetime import datetime

# 填入你專屬的 Discord Webhook 網址
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1547538132822401126/tQWRp96vQ1_7LJu-HWYNcSfb9XO84z_Faa0jM4Mum_wCwew2nrtv-X1ZhDi0z1e-6r65"

my_portfolio = ["0050.TW", "2327.TW", "3532.TW", "5347.TWO", "8299.TWO"]

discord_message = f"📊 **【AI 持股即時驗證雷達】** 執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
discord_message += "--------------------------------------------------------\n"

for ticker in my_portfolio:
    df = yf.download(ticker, period="60d", progress=False)
    if df.empty: 
        continue
        
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    try:
        t_obj = yf.Ticker(ticker)
        live_price = t_obj.fast_info['last_price']
        today_str = datetime.now().strftime('%Y-%m-%d')
        df.loc[pd.to_datetime(today_str)] = [live_price, live_price, live_price, live_price, live_price, 0]
    except Exception:
        pass

    df['RSI'] = ta.rsi(df['Close'], length=14)
    bbands = ta.bbands(df['Close'], length=20, std=2)
    
    df['BB_lower'] = bbands.iloc[:, 0]
    df['BB_upper'] = bbands.iloc[:, 2]
    
    latest_data = df.iloc[-1]
    current_price = float(latest_data['Close'])
    rsi_val = float(latest_data['RSI'])
    bb_low = float(latest_data['BB_lower'])
    bb_up = float(latest_data['BB_upper'])
    
    status = "正常波動中"
    if current_price < bb_low and rsi_val < 35:
        status = "🚨 **【市場超跌】即時觸發加碼訊號！**"
    elif current_price > bb_up and rsi_val > 75:
        status = "💰 **【波段過熱】即時觸發獲利了結！**"
        
    line_text = f"`{ticker:8}` | 即時價: **{current_price:7.2f}** | RSI: {rsi_val:5.1f} | 狀態: {status}\n"
    discord_message += line_text

try:
    payload = {"content": discord_message}
    requests.post(DISCORD_WEBHOOK_URL, json=payload)
except Exception as e:
    print(f"發送失敗: {e}")
