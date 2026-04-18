import pandas as pd
import matplotlib.pyplot as plt
from fredapi import Fred
import requests
import os

# GitHub Secrets에서 정보 가져오기
FRED_API_KEY = os.environ.get('FRED_API_KEY')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def run_analysis():
    fred = Fred(api_key=FRED_API_KEY)
    # 데이터 수집 (우리가 만든 로직)
    data = {
        'Assets': fred.get_series('WALCL'),
        'TGA': fred.get_series('WTREGEN'),
        'RRP': fred.get_series('RRPONTSYD'),
        'SP500': fred.get_series('SP500')
    }
    df = pd.concat(data, axis=1).ffill().dropna()
    df['Net_Liquidity'] = (df['Assets'] - df['TGA'] - df['RRP']) / 1000
    recent = df.tail(252)

    # 그래프 생성 및 저장
    plt.figure(figsize=(10, 6))
    plt.plot(recent.index, recent['Net_Liquidity'], color='dodgerblue', label='Net Liquidity')
    plt.title(f"Liquidity Report ({recent.index[-1].date()})")
    plt.grid(True, alpha=0.3)
    plt.savefig('liquidity_plot.png')

    # 리포트 텍스트
    curr, prev = df.iloc[-1], df.iloc[-6]
    diff = curr['Net_Liquidity'] - prev['Net_Liquidity']
    report = f"📡 유동성 업데이트: ${curr['Net_Liquidity']:,.2f}B ({'▲' if diff>0 else '▼'} ${abs(diff):.2f}B)"

    # 텔레그램 전송
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open('liquidity_plot.png', 'rb') as f:
        requests.post(url, data={'chat_id': CHAT_ID, 'caption': report}, files={'photo': f})

if __name__ == "__main__":
    run_analysis()
