import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests

from datetime import datetime
from zoneinfo import ZoneInfo


# =========================================================
# 1. Discord Webhook
# =========================================================
# ⚠️ 請把這裡換成「重新產生的新 Webhook」
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1547996479287984218/VSA3tm2_e1C7BErWp4Gs-aPmFsChNo9wxgV6cjjOO8iIuNi-DejBsSHX8fAkc6Gf0WAU"


# =========================================================
# 2. 我的持股
# =========================================================
my_portfolio = [
    "0050.TW",   # 元大台灣50
    "2327.TW",   # 國巨
    "3532.TW",   # 台勝科
    "5347.TWO",  # 世界先進（上櫃）
    "8299.TWO"   # 群聯（上櫃）
]


# =========================================================
# 3. 取得台北時間
# =========================================================
taipei_time = datetime.now(ZoneInfo("Asia/Taipei"))

print("=" * 60)
print("📊 AI 持股技術面雷達")
print("執行時間：", taipei_time.strftime("%Y-%m-%d %H:%M:%S"))
print("=" * 60)


# =========================================================
# 4. Discord 訊息開頭
# =========================================================
discord_message = (
    "📊 **【AI 持股技術面雷達】**\n"
    f"🕐 執行時間：{taipei_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    "────────────────────────────\n\n"
)


# =========================================================
# 5. 開始分析每一檔股票
# =========================================================
for ticker in my_portfolio:

    print(f"正在分析 {ticker}...")

    try:

        # -------------------------------------------------
        # 下載過去 60 天日 K
        # -------------------------------------------------
        df = yf.download(
            ticker,
            period="60d",
            interval="1d",
            auto_adjust=False,
            progress=False
        )

        if df.empty:
            print(f"⚠️ {ticker} 沒有取得資料")
            continue


        # -------------------------------------------------
        # 處理 yfinance MultiIndex
        # -------------------------------------------------
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)


        # -------------------------------------------------
        # RSI(14)
        # -------------------------------------------------
        df["RSI"] = ta.rsi(
            df["Close"],
            length=14
        )


        # -------------------------------------------------
        # 布林通道 (20, 2)
        # -------------------------------------------------
        bbands = ta.bbands(
            df["Close"],
            length=20,
            std=2
        )

        df["BB_lower"] = bbands.iloc[:, 0]
        df["BB_middle"] = bbands.iloc[:, 1]
        df["BB_upper"] = bbands.iloc[:, 2]


        # -------------------------------------------------
        # MA20
        # -------------------------------------------------
        df["MA20"] = ta.sma(
            df["Close"],
            length=20
        )


        # -------------------------------------------------
        # 取得最新一筆資料
        # -------------------------------------------------
        latest = df.iloc[-1]

        current_price = float(latest["Close"])
        rsi_value = float(latest["RSI"])
        bb_lower = float(latest["BB_lower"])
        bb_upper = float(latest["BB_upper"])
        ma20 = float(latest["MA20"])


        # -------------------------------------------------
        # 嘗試取得目前價格
        # -------------------------------------------------
        try:

            stock = yf.Ticker(ticker)

            live_price = stock.fast_info.get("last_price")

            if live_price is not None:
                current_price = float(live_price)

        except Exception:

            print(f"⚠️ {ticker} 無法取得目前價格，使用最近收盤價")


        # =================================================
        # 6. 訊號判斷
        # =================================================

        status = "🟢 正常波動中"

        if current_price < bb_lower and rsi_value < 35:

            status = "🚨 **市場超跌｜注意加碼機會**"

        elif current_price > bb_upper and rsi_value > 75:

            status = "💰 **波段過熱｜注意獲利了結**"


        # =================================================
        # 7. 終端機顯示
        # =================================================

        print(
            f"{ticker} | "
            f"價格：{current_price:.2f} | "
            f"RSI：{rsi_value:.1f} | "
            f"MA20：{ma20:.2f} | "
            f"{status}"
        )


        # =================================================
        # 8. 組合 Discord 訊息
        # =================================================

        discord_message += (
            f"**`{ticker}`**\n"
            f"💰 目前價格：**{current_price:.2f}**\n"
            f"📈 RSI(14)：**{rsi_value:.1f}**\n"
            f"📊 MA20：**{ma20:.2f}**\n"
            f"🔽 布林下軌：{bb_lower:.2f}\n"
            f"🔼 布林上軌：{bb_upper:.2f}\n"
            f"📌 狀態：{status}\n"
            "────────────────────────────\n\n"
        )


    except Exception as e:

        print(f"❌ {ticker} 分析失敗：{e}")

        discord_message += (
            f"⚠️ **`{ticker}` 資料取得失敗**\n"
            f"錯誤：{e}\n\n"
        )


# =========================================================
# 9. 發送 Discord
# =========================================================

try:

    payload = {
        "content": discord_message
    }

    response = requests.post(
        DISCORD_WEBHOOK_URL,
        json=payload,
        timeout=10
    )


    if response.status_code == 204:

        print("\n✅ Discord 發送成功！")

    else:

        print(
            f"\n❌ Discord 發送失敗！"
            f"HTTP 狀態碼：{response.status_code}"
        )

        print(response.text)


except Exception as e:

    print(f"\n❌ Discord 連線失敗：{e}")


print("\n程式執行完畢。")
