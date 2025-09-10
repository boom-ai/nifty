import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

def get_nifty50_symbols():
    return [
        'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'BHARTIARTL.NS', 'ICICIBANK.NS',
        'INFOSYS.NS', 'SBIN.NS', 'HINDUNILVR.NS', 'ITC.NS', 'KOTAKBANK.NS',
        'LT.NS', 'HCLTECH.NS', 'AXISBANK.NS', 'ASIANPAINT.NS', 'MARUTI.NS',
        'SUNPHARMA.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS', 'NESTLEIND.NS',
        'POWERGRID.NS', 'NTPC.NS', 'TECHM.NS', 'ONGC.NS', 'TATAMOTORS.NS',
        'BAJFINANCE.NS', 'M&M.NS', 'TATASTEEL.NS', 'COALINDIA.NS', 'INDUSINDBK.NS',
        'ADANIPORTS.NS', 'DRREDDY.NS', 'GRASIM.NS', 'JSWSTEEL.NS', 'CIPLA.NS',
        'TATACONSUM.NS', 'BPCL.NS', 'EICHERMOT.NS', 'BRITANNIA.NS', 'HEROMOTOCO.NS',
        'UPL.NS', 'APOLLOHOSP.NS', 'DIVISLAB.NS', 'HINDALCO.NS', 'SBILIFE.NS',
        'BAJAJFINSV.NS', 'HDFCLIFE.NS', 'SHREECEM.NS', 'IOC.NS', 'ADANIENT.NS'
    ]

def get_stock_info(symbol):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="30d")
        if len(hist) < 20:
            return None
        price = hist['Close'].iloc[-1]
        ma20 = hist['Close'].rolling(window=20).mean().iloc[-1]
        dev = ((price - ma20) / ma20) * 100
        vol_avg = hist['Volume'].rolling(window=10).mean().iloc[-1]
        vol = hist['Volume'].iloc[-1]
        vol_ratio = vol / vol_avg if vol_avg else 0
        volatility = hist['Close'].pct_change().std() * np.sqrt(252) * 100
        return {
            'Stock': symbol.replace('.NS', ''),
            'Price': round(price,2),
            'MA-20': round(ma20,2),
            'Dev%': round(dev,2),
            'Vol Ratio': round(vol_ratio,2),
            'Volatility': round(volatility,1)
        }
    except:
        return None

def run_nifty_screening(capital, dev_max, vol_ratio_min, volatility_max):
    symbols = get_nifty50_symbols()
    candidates = []
    for symbol in symbols:
        info = get_stock_info(symbol)
        if info and info['Price'] < info['MA-20'] and info['Dev%'] > dev_max and info['Vol Ratio'] > vol_ratio_min and info['Volatility'] < volatility_max:
            candidates.append(info)
    candidates.sort(key=lambda x: x['Dev%'])
    picks = candidates[:5]
    position_size = capital * 0.20
    for p in picks:
        p['Qty'] = int(position_size // p['Price'])
        p['Amount'] = p['Qty'] * p['Price']
    return candidates, picks

st.set_page_config(page_title="NIFTY", page_icon=":chart_with_upwards_trend:")

st.sidebar.title("NIFTY")
capital = st.sidebar.number_input("Capital for investment (INR)", min_value=10000, max_value=5000000, value=100000, step=10000)
st.sidebar.header("Screening Parameters")
dev_max = st.sidebar.slider("Max Deviation %", -20, 0, -10)
vol_ratio_min = st.sidebar.slider("Min Volume Ratio", 0.5, 2.0, 0.8)
volatility_max = st.sidebar.slider("Max Volatility", 20, 80, 50)
run = st.sidebar.button('Run NIFTY Screening')

st.header("💰 NIFTY Stock Screener")
st.info("This app screens the NIFTY 50 stocks based on a set of technical indicators. You can customize the screening criteria from the sidebar and find the top 5 recommendations for your investment.")


if run:
    with st.spinner("Analyzing NIFTY 50..."):
        allc, recs = run_nifty_screening(capital, dev_max, vol_ratio_min, volatility_max)
    st.write(f"### {len(recs)} Recommendations for ₹{capital:,}")
    if recs and len(recs) > 0:
        df = pd.DataFrame(recs)[['Stock','Price','MA-20','Dev%','Vol Ratio','Volatility','Qty','Amount']]
        st.dataframe(df.style.format({'Price':'₹{:.2f}', 'MA-20':'₹{:.2f}', 'Amount':'₹{:,.2f}'}).applymap(lambda x: 'color: red' if x < 0 else 'color: green', subset=['Dev%']))

        st.header("Historical Price Charts")
        selected_stocks = st.multiselect("Select stocks to view charts", options=df['Stock'].tolist())
        if selected_stocks:
            for stock_symbol in selected_stocks:
                try:
                    stock_data = yf.Ticker(f"{stock_symbol}.NS").history(period="6mo")
                    st.line_chart(stock_data['Close'])
                except Exception as e:
                    st.warning(f"Could not fetch chart for {stock_symbol}. Error: {e}")
    else:
        st.warning("No NIFTY stocks meet today's criteria. Try again later.")
    st.write(f"Analyzed {len(allc)} stocks that passed MA/volume/volatility rules.")
