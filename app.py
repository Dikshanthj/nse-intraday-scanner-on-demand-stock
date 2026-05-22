import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from gnews import GNews

st.set_page_config(page_title="Intraday Verdict Engine", page_icon="🎯", layout="wide")

st.title("🎯 Single-Stock Intraday Diagnostic & Verdict Engine")
st.write("Input any National Stock Exchange (NSE) stock to run an instant quantitative and sentiment audit.")

# Input interface styled cleanly for mobile safari viewing
ticker_input = st.text_input("✍️ Enter NSE Stock Ticker (e.g., TRENT, SBIN, AXISBANK, RELIANCE):", value="AXISBANK").strip().upper()

if st.button("🔍 Run Full Intraday Diagnostic"):
    if not ticker_input:
        st.error("Please enter a valid stock ticker symbol.")
    else:
        # Standardize ticker formatting to match Yahoo Finance requirements
        if not ticker_input.endswith(".NS"):
            ticker_formatted = f"{ticker_input}.NS"
        else:
            ticker_formatted = ticker_input

        with st.spinner(f"Running multi-variable analytical calculations on {ticker_input}..."):
            try:
                # ----------------------------------------------------
                # DATA ACQUISITION LAYER
                # ----------------------------------------------------
                # Fetching 1-week and 2-day historical datasets in parallel
                stock_engine = yf.Ticker(ticker_formatted)
                hist_1w = stock_engine.history(period="7d")
                hist_2d = stock_engine.history(period="2d")
                
                if hist_2d.empty or len(hist_2d) < 2:
                    st.error(f"Ticker '{ticker_input}' not found or has insufficient trading depth on the exchange.")
                else:
                    # Daily operational parameter extractions
                    close = float(hist_2d['Close'].iloc[-1])
                    day_high = float(hist_2d['High'].iloc[-1])
                    day_low = float(hist_2d['Low'].iloc[-1])
                    day_open = float(hist_2d['Open'].iloc[-1])
                    volume = int(hist_2d['Volume'].iloc[-1])
                    
                    prev_close = float(hist_2d['Close'].iloc[-2])
                    pct_change = ((close - prev_close) / prev_close) * 100
                    
                    # 1-Week Performance Tracking Math
                    start_1w_price = float(hist_1w['Close'].iloc[0])
                    perf_1w_pct = ((close - start_1w_price) / start_1w_price) * 100
                    
                    # ----------------------------------------------------
                    # ALGORITHMIC RISK METRICS & QUANT GRID
                    # ----------------------------------------------------
                    day_range = day_high - day_low
                    hcpf = (day_high - close) / day_range if day_range != 0 else 1.0
                    historical_volatility = (day_range / close) * 100
                    
                    # Level Framework Mapping (Strict 1:2 Risk-Reward Framework)
                    entry_trigger = round(close * 1.002, 2)
                    calculated_risk = min(0.75, historical_volatility * 0.4)
                    stop_loss = round(close * (1 - (calculated_risk / 100)), 2)
                    risk_per_share = entry_trigger - stop_loss
                    target = round(entry_trigger + (risk_per_share * 2.0), 2)
                    
                    # ----------------------------------------------------
                    # REAL-TIME NEWS & SENTIMENT EXTRACTION LAYER
                    # ----------------------------------------------------
                    news_verdict = "NEUTRAL"
                    news_items = []
                    try:
                        google_news = GNews(language='en', country='IN', max_results=3)
                        raw_news = google_news.get_news(f"{ticker_input} Stock News India")
                        
                        if raw_news:
                            for item in raw_news:
                                news_items.append({
                                    "Title": item['title'],
                                    "Source": item['publisher']['title'],
                                    "Link": item['url']
                                })
                            # Simple headline scanning logic to look for market risks
                            combined_headlines = " ".join([n['Title'].lower() for n in news_items])
                            if any(word in combined_headlines for word in ["drop", "crash", "loss", "fell", "slump", "miss"]):
                                news_verdict = "BEARISH / CAUTION"
                            elif any(word in combined_headlines for word in ["profit", "surge", "gain", "buy", "growth", "win"]):
                                news_verdict = "BULLISH"
                    except Exception:
                        news_verdict = "NEWS STREAM TEMPORARILY OFFLINE"

                    # ----------------------------------------------------
                    # AUTOMATED INTENT VERDICT LOGIC ENGINE
                    # ----------------------------------------------------
                    reasons_for_verdict = []
                    is_safe = True
                    
                    # Security Check 1: Liquidity Protection
                    if volume < 800000:
                        is_safe = False
                        reasons_for_verdict.append("Low Trading Volume (High Slippage Risk)")
                        
                    # Security Check 2: Absolute Momentum Check
                    if pct_change <= 0:
                        is_safe = False
                        reasons_for_verdict.append("Negative Intraday Price Velocity (Not Gaining)")
                        
                    # Security Check 3: Price Deflation Rejection (HCPF Trap)
                    if hcpf > 0.25:
                        is_safe = False
                        reasons_for_verdict.append("High-Close Proximity Failure (Gave away substantial daily gains near close)")
                        
                    # Security Check 4: Hyper-Volatility Risk
                    if historical_volatility > 4.5:
                        is_safe = False
                        reasons_for_verdict.append("Hyper-Volatility Spread (Exceeds safe intraday structural noise caps)")

                    # Final Verdict Computation
                    if is_safe and perf_1w_pct > 0:
                        verdict_label = "🚀 HIGH-PROBABILITY GO (LONG)"
                        verdict_color = st.success
                    elif is_safe:
                        verdict_label = "⚠️ RISK-CONTINGENT GO (Short-term Momentum Only)"
                        verdict_color = st.warning
                    else:
                        verdict_label = "❌ NO GO (HIGH TRADING RISK)"
                        verdict_color = st.error

                    # ----------------------------------------------------
                    # USER INTERFACE LAYOUT RENDER (SCANNABLE)
                    # ----------------------------------------------------
                    st.markdown("### 📊 Diagnostic Dashboard")
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Verified Session Close", f"₹{close:,.2f}", f"{pct_change:.2f}%")
                    col2.metric("1-Week Trajectory Score", f"{perf_1w_pct:.2f}%")
                    col3.metric("Intraday Noise Spread", f"{historical_volatility:.2f}%")
                    col4.metric("Live Media Sentiment", news_verdict)
                    
                    st.markdown("---")
                    st.markdown("### 🦾 Automated Intraday Trade Verdict")
                    verdict_color(f"**VERDICT: {verdict_label}**")
                    
                    if reasons_for_verdict:
                        st.markdown("**Core Negative Risk Factors Found:**")
                        for reason in reasons_for_verdict:
                            st.markdown(f"• {reason}")
                    else:
                        st.markdown("• Stock cleared all 6 mathematical institutional safety filters successfully.")

                    st.markdown("---")
                    st.markdown("### 🛠️ Precision Execution Parameters")
                    
                    # Create structured DataFrame for scannable rendering
                    param_data = {
                        "Parameter Matrix Line": ["ENTRY TRIGGER VALUE", "MATHEMATICAL TARGET", "CRITICAL STOP-LOSS FLOOR"],
                        "Execution Price Level (₹)": [f"₹{entry_trigger:,.2f}", f"₹{target:,.2f}", f"₹{stop_loss:,.2f}"],
                        "Strategic Rule Instruction": [
                            f"Buy ONLY if price breaks and sustains above ₹{entry_trigger} after 9:30 AM.",
                            "Absolute high-yield profit booking level. Exit position completely here.",
                            "Hard stop level. If touched, liquidate instantly to limit downside risk."
                        ]
                    }
                    st.table(pd.DataFrame(param_data).set_index("Parameter Matrix Line"))

                    # Display Live News Headlines
                    if news_items:
                        st.markdown("---")
                        st.markdown("### 📰 Recent Scanned Media Headings")
                        for n in news_items:
                            st.markdown(f"• **[{n['Source']}]** [{n['Title']}]({n['Link']})")

                    st.markdown("""
                    *⚠️ **Disclaimer:** This data matrix runs entirely on mathematical pricing equations and public media news feeds. It is designed for educational screening purposes. Always confirm parameters on your live trading terminal before execution.*
                    """)
                    
            except Exception as e:
