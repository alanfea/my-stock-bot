import os
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests

from datetime import datetime
from zoneinfo import ZoneInfo


# =========================================================
# 1. Discord Webhook
# =========================================================
# GitHub Actions 建議使用 Secrets
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

if not DISCORD_WEBHOOK_URL:
    raise ValueError("找不到 DISCORD_WEBHOOK_URL")


# =========================================================
# 2. 股票清單
# =========================================================
PORTFOLIO = [
    "0050.TW",    # 元大台灣50
    "2327.TW",    # 國巨
    "3532.TW",    # 台勝科
    "5347.TWO",   # 世界先進
    "8299.TWO"    # 群聯
]


# =========================================================
# 3. 台北時間
# =========================================================
taipei_time = datetime.now(
    ZoneInfo("Asia/Taipei")
)

print("=" * 60)
print("📊 AI 持股技術面雷達")
print(
    "執行時間：",
    taipei_time.strftime("%Y-%m-%d %H:%M:%S")
)
print("=" * 60)


# =========================================================
# 4. 一次下載全部股票
# =========================================================
print("📡 正在批次取得 Yahoo Finance 資料...")

try:

    data = yf.download(
        tickers=PORTFOLIO,
        period="60d",
        interval="1d",
        auto_adjust=False,
        group_by="ticker",
        threads=True,
        progress=False
    )

except Exception as e:

    raise RuntimeError(
        f"Yahoo Finance 資料下載失敗：{e}"
    )


if data.empty:
    raise RuntimeError("Yahoo Finance 沒有回傳資料")


print("✅ Yahoo Finance 資料取得完成")


# =========================================================
# 5. 建立 Discord 訊息
# =========================================================
discord_message = (
    "📊 **【AI 持股技術面雷達】**\n"
    f"🕐 執行時間："
    f"{taipei_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    "────────────────────────────\n\n"
)


# =========================================================
# 6. 分析每一檔股票
# =========================================================
for ticker in PORTFOLIO:

    print(f"🔍 分析 {ticker}...")

    try:

        # -------------------------------------------------
        # 取得單一股票資料
        # -------------------------------------------------
        df = data[ticker].copy()

        df = df.dropna(
            subset=["Close"]
        )

        if df.empty:
            raise ValueError("沒有有效資料")


        # -------------------------------------------------
        # RSI(14)
        # -------------------------------------------------
        df["RSI"] = ta.rsi(
            df["Close"],
            length=14
        )


        # -------------------------------------------------
        # Bollinger Bands (20, 2)
        # -------------------------------------------------
        bb = ta.bbands(
            df["Close"],
            length=20,
            std=2
        )

        df["BB_lower"] = bb.iloc[:, 0]
        df["BB_middle"] = bb.iloc[:, 1]
        df["BB_upper"] = bb.iloc[:, 2]


        # -------------------------------------------------
        # MA20
        # -------------------------------------------------
        df["MA20"] = ta.sma(
            df["Close"],
            length=20
        )


        # -------------------------------------------------
        # 最新資料
        # -------------------------------------------------
        latest = df.iloc[-1]

        current_price = float(
            latest["Close"]
        )

        rsi_value = float(
            latest["RSI"]
        )

        bb_lower = float(
            latest["BB_lower"]
        )

        bb_upper = float(
            latest["BB_upper"]
        )

        ma20 = float(
            latest["MA20"]
        )


        # -------------------------------------------------
        # 訊號判斷
        # -------------------------------------------------
        status = "🟢 正常波動中"

        if (
            current_price < bb_lower
            and rsi_value < 35
        ):

            status = (
                "🚨 **市場超跌｜"
                "注意加碼機會**"
            )

        elif (
            current_price > bb_upper
            and rsi_value > 75
        ):

            status = (
                "💰 **波段過熱｜"
                "注意獲利了結**"
            )


        # -------------------------------------------------
        # Discord 訊息
        # -------------------------------------------------
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


        print(
            f"   價格 {current_price:.2f} | "
            f"RSI {rsi_value:.1f} | "
            f"{status}"
        )


    except Exception as e:

        print(
            f"❌ {ticker} 分析失敗：{e}"
        )

        discord_message += (
            f"⚠️ **`{ticker}` 分析失敗**\n"
            f"錯誤：{e}\n\n"
        )


# =========================================================
# 7. 一次發送 Discord
# =========================================================
print("📤 正在發送 Discord...")

try:

    response = requests.post(
        DISCORD_WEBHOOK_URL,
        json={
            "content": discord_message
        },
        timeout=10
    )

    if response.status_code == 204:

        print("✅ Discord 發送成功！")

    else:

        print(
            f"❌ Discord 發送失敗："
            f"{response.status_code}"
        )

        print(response.text)

except requests.RequestException as e:

    print(
        f"❌ Discord 網路連線失敗：{e}"
    )


print("=" * 60)
print("🏁 程式執行完成")
print("=" * 60)
