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
    
    # 1. 데이터 수집
    data = {
        'Assets': fred.get_series('WALCL'),
        'TGA': fred.get_series('WTREGEN'),
        'RRP': fred.get_series('RRPONTSYD'),
        'SP500': fred.get_series('SP500')
    }
    df = pd.concat(data, axis=1).ffill().dropna()
    df['Net_Liquidity'] = (df['Assets'] - df['TGA'] - df['RRP']) / 1000
    recent_df = df.tail(252).copy()

    # 2. 시각화 (두 개의 서브플롯 생성)
    fig, (ax1, ax3) = plt.subplots(2, 1, figsize=(12, 10))
    plt.subplots_adjust(hspace=0.4)

    # 상단: 절대치 (유동성 vs S&P 500)
    color_liq, color_sp = 'dodgerblue', 'crimson'
    ax1.plot(recent_df.index, recent_df['Net_Liquidity'], color=color_liq, lw=2, label='Net Liquidity')
    ax1.set_title('1. Net Liquidity vs S&P 500 (Magnified)', fontsize=12, fontweight='bold')
    ax2 = ax1.twinx()
    ax2.plot(recent_df.index, recent_df['SP500'], color=color_sp, lw=1.5, label='S&P 500')
    
    # 하단: 변화율 (%)
    liq_pct = (recent_df['Net_Liquidity'] / recent_df['Net_Liquidity'].iloc[0] - 1) * 100
    sp_pct = (recent_df['SP500'] / recent_df['SP500'].iloc[0] - 1) * 100
    ax3.plot(recent_df.index, liq_pct, color=color_liq, label='Net Liquidity (%)')
    ax3.plot(recent_df.index, sp_pct, color=color_sp, label='S&P 500 (%)')
    ax3.axhline(0, color='black', ls='--')
    ax3.set_title('2. Relative Performance (%)', fontsize=12, fontweight='bold')
    ax3.legend()
    
    plt.savefig('liquidity_report.png')

    # 3. 상세 변동 분석 텍스트 작성
    curr = recent_df.iloc[-1]
    prev = recent_df.iloc[-6] # 약 1주일 전

    d_assets = (curr['Assets'] - prev['Assets']) / 1000
    d_tga = (curr['TGA'] - prev['TGA']) / 1000
    d_rrp = (curr['RRP'] - prev['RRP']) / 1000
    d_liq = curr['Net_Liquidity'] - prev['Net_Liquidity']

    def fmt(val): return f"{'▲' if val > 0 else '▼'} ${abs(val):.2f}B"
    def impact(val, inv=False):
        if (val > 0 and not inv) or (val < 0 and inv): return "호재"
        return "악재"

    report = (
        f"📡 [유동성 주간 리포트]\n"
        f"기준일: {recent_df.index[-1].date()}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"1. 연준 자산: ${curr['Assets']/1000:,.1f}B ({fmt(d_assets)} / {impact(d_assets)})\n"
        f"2. 재무부 TGA: ${curr['TGA']/1000:,.1f}B ({fmt(d_tga)} / {impact(d_tga, True)})\n"
        f"3. 역레포 RRP: ${curr['RRP']/1000:,.1f}B ({fmt(d_rrp)} / {impact(d_rrp, True)})\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 순 유동성 합계: ${curr['Net_Liquidity']:,.2f}B\n"
        f"주간 변동: {fmt(d_liq)}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🚨 변곡점 알람:\n"
        f"{'▶ 급격한 유동성 변동! 대응 필요' if abs(d_liq) > 50 else '▶ 유동성 흐름 안정적'}\n"
        f"\n📘 마스터 노트:\n"
        f"- TGA/역레포 감소(▼) = 시장 호재\n"
        f"- 주가(빨간선) 과열 여부 체크!"
    )

    # 4. 텔레그램 전송
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open('liquidity_report.png', 'rb') as f:
        requests.post(url, data={'chat_id': CHAT_ID, 'caption': report}, files={'photo': f})

if __name__ == "__main__":
    run_analysis()
