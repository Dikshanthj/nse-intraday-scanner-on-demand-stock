import streamlit as st
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator

st.set_page_config(page_title="NSE Momentum Scanner", layout="wide")

st.title("📈 NSE AI Momentum Scanner")
st.write("Automatically scans NSE stocks and finds short-term momentum opportunities.")

@st.cache_data
def get_nse_symbols():
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    df = pd.read_csv(url)
    symbols = df["SYMBOL"].tolist()
    symbols = [symbol + ".NS" for symbol in symbols]
    return symbols

if st.button("Scan NSE Market"):

    symbols = get_nse_symbols()

    # Limit scan size initially for speed
    symbols = symbols[:200]

    results = []

    progress = st.progress(0)

    for idx, symbol in enumerate(symbols):

        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="3mo")

            if hist.empty or len(hist) < 50:
                continue

            hist["SMA20"] = hist["Close"].rolling(20).mean()
            hist["SMA50"] = hist["Close"].rolling(50).mean()

            hist["RSI"] = RSIIndicator(hist["Close"]).rsi()

            latest = hist.iloc[-1]

            price = round(latest["Close"], 2)
            sma20 = round(latest["SMA20"], 2)
            sma50 = round(latest["SMA50"], 2)
            rsi = round(latest["RSI"], 2)

            latest_volume = latest["Volume"]
            avg_volume = hist["Volume"].rolling(20).mean().iloc[-1]

            signal = "HOLD"

            if (
                sma20 > sma50 and
                price > sma20 and
                latest_volume > avg_volume and
                55 < rsi < 70
            ):
                signal = "STRONG BUY"

            elif (
                sma20 > sma50 and
                price > sma20
            ):
                signal = "BUY"

            if signal in ["BUY", "STRONG BUY"]:

                score = 0

                if sma20 > sma50:
                    score += 1

                if price > sma20:
                    score += 1

                if latest_volume > avg_volume:
                    score += 1

                if 55 < rsi < 70:
                    score += 1

                if score >= 4:
                    confidence = "High"
                elif score >= 3:
                    confidence = "Medium"
                else:
                    confidence = "Low"

                target = round(price * 1.06, 2)
                stoploss = round(price * 0.96, 2)

                momentum_strength = abs(sma20 - sma50)

                if momentum_strength > 20:
                    expected_days = "2-3 Days"
                elif momentum_strength > 10:
                    expected_days = "3-5 Days"
                else:
                    expected_days = "5-7 Days"

                results.append({
                    "Stock": symbol,
                    "Current Price": price,
                    "RSI": rsi,
                    "Signal": signal,
                    "Target": target,
                    "Stoploss": stoploss,
                    "Expected Time": expected_days,
                    "Confidence": confidence,
                    "Score": score
                })

        except Exception:
            continue

        progress.progress((idx + 1) / len(symbols))

    if results:

        df = pd.DataFrame(results)

        df = df.sort_values(by="Score", ascending=False)

        st.success(f"Found {len(df)} momentum opportunities")

        st.dataframe(df, use_container_width=True)

        st.subheader("📊 Top Momentum Charts")

        top_stocks = df.head(5)["Stock"].tolist()

        for stock_symbol in top_stocks:

            try:
                stock = yf.Ticker(stock_symbol)
                hist = stock.history(period="6mo")

                st.write(f"### {stock_symbol}")
                st.line_chart(hist["Close"])

            except:
                pass

    else:
        st.warning("No strong momentum setups found today.")

st.markdown("---")
st.caption("Educational use only. Not financial advice.")
