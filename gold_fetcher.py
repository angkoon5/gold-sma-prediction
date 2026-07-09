"""
ดึงราคาทองคำออนไลน์จากแหล่งชั้นนำ
แหล่งที่ใช้:
1. Yahoo Finance (Gold Futures GC=F) - ราคาทองสากล real-time
2. Open Exchange Rate API - อัตราแลกเปลี่ยน USD/THB
3. GoldPriceZ.com - ราคาย้อนหลัง 30 วัน (THB)
คำนวณเป็นราคาทองไทยต่อ 1 บาททองคำ (15.244 กรัม, 96.5%)
"""
import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta
import numpy as np

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Constants
TROY_OZ_GRAMS = 31.1035
BAHT_WEIGHT_GRAMS = 15.244
GOLD_PURITY_965 = 0.965

def fetch_yahoo_gold(days=30):
    """ดึงราคาทอง Gold Futures จาก Yahoo Finance"""
    try:
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval=1d&range={days}d'
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        
        data = resp.json()
        result = data['chart']['result'][0]
        timestamps = result['timestamp'] 
        closes = result['indicators']['quote'][0]['close']
        
        prices = []
        for t, c in zip(timestamps, closes):
            if c is not None:
                dt = datetime.fromtimestamp(t)
                prices.append({
                    'date': dt.strftime('%Y-%m-%d'),
                    'price_usd': round(c, 2)
                })
        
        return {
            'source': 'Yahoo Finance (Gold Futures GC=F)',
            'source_url': 'https://finance.yahoo.com/quote/GC=F/',
            'status': 'success',
            'data': prices,
            'latest_usd': prices[-1]['price_usd'] if prices else None
        }
    except Exception as e:
        return {
            'source': 'Yahoo Finance',
            'status': 'error',
            'error': str(e)
        }

def fetch_exchange_rate():
    """ดึงอัตราแลกเปลี่ยน USD/THB"""
    try:
        resp = requests.get('https://open.er-api.com/v6/latest/USD', headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return {
            'status': 'success',
            'usd_thb': data['rates']['THB'],
            'source': 'Open Exchange Rates API'
        }
    except Exception as e:
        return {'status': 'error', 'error': str(e), 'usd_thb': 33.30}

def fetch_goldpricez_history():
    """ดึงราคาย้อนหลังจาก GoldPriceZ.com"""
    try:
        url = "https://goldpricez.com/gold/history/thb/days-30"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, 'lxml')
        history = []
        
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    try:
                        date_text = cells[0].get_text(strip=True)
                        price_text = cells[1].get_text(strip=True)
                        price_clean = re.sub(r'[^\d.]', '', price_text)
                        if price_clean and float(price_clean) > 100:
                            history.append({
                                'date': date_text,
                                'price_thb_per_gram': float(price_clean)
                            })
                    except (ValueError, IndexError):
                        continue
        
        return {
            'source': 'GoldPriceZ.com',
            'source_url': 'https://goldpricez.com/gold/history/thb/days-30',
            'status': 'success' if history else 'no_data',
            'data': history
        }
    except Exception as e:
        return {
            'source': 'GoldPriceZ.com',
            'status': 'error',
            'error': str(e)
        }

def usd_to_thai_baht_gold(price_usd_per_oz, usd_thb_rate):
    """แปลงราคาทอง USD/oz เป็นราคาทองไทย บาท/บาททองคำ (96.5%)"""
    # 1 troy oz = 31.1035 g
    # 1 บาททองคำ = 15.244 g
    # ทองคำแท่ง 96.5%
    price_thb_per_oz = price_usd_per_oz * usd_thb_rate
    price_thb_per_gram = price_thb_per_oz / TROY_OZ_GRAMS
    price_per_baht_weight = price_thb_per_gram * BAHT_WEIGHT_GRAMS * GOLD_PURITY_965
    return round(price_per_baht_weight, 2)

def fetch_all_online_data():
    """ดึงข้อมูลทั้งหมดจากออนไลน์ พร้อมแปลงเป็นราคาทองไทย"""
    # 1. ดึงราคาทอง USD
    yahoo_data = fetch_yahoo_gold(60)
    
    # 2. ดึงอัตราแลกเปลี่ยน
    fx_data = fetch_exchange_rate()
    usd_thb = fx_data.get('usd_thb', 33.30)
    
    # 3. ดึงราคาย้อนหลังจาก goldpricez
    gpz_data = fetch_goldpricez_history()
    
    # 4. แปลงราคา USD เป็น THB/บาททองคำ
    thai_prices = []
    if yahoo_data.get('status') == 'success':
        for item in yahoo_data['data']:
            thai_price = usd_to_thai_baht_gold(item['price_usd'], usd_thb)
            thai_prices.append({
                'date': item['date'],
                'price_usd_oz': item['price_usd'],
                'price_thb_baht': thai_price
            })
    
    # 5. ราคาล่าสุด
    latest = None
    if thai_prices:
        latest = {
            'price_thb': thai_prices[-1]['price_thb_baht'],
            'price_usd': thai_prices[-1]['price_usd_oz'],
            'date': thai_prices[-1]['date'],
            'usd_thb': usd_thb
        }
    
    return {
        'status': 'success' if thai_prices else 'error',
        'latest': latest,
        'history': thai_prices,
        'sources': {
            'yahoo': yahoo_data.get('source', 'Yahoo Finance'),
            'yahoo_url': yahoo_data.get('source_url', ''),
            'exchange_rate': fx_data.get('source', ''),
            'goldpricez': gpz_data.get('source', ''),
            'goldpricez_url': gpz_data.get('source_url', '')
        },
        'usd_thb': usd_thb,
        'note': 'ราคาคำนวณจาก Gold Futures (USD) x อัตราแลกเปลี่ยน แปลงเป็นราคาต่อ 1 บาททองคำ 96.5%'
    }

def get_online_prices_for_sma():
    """ดึงราคาออนไลน์สำหรับคำนวณ SMA และเปรียบเทียบ"""
    data = fetch_all_online_data()
    if data['status'] != 'success':
        return None
    
    prices = [item['price_thb_baht'] for item in data['history']]
    dates = [item['date'] for item in data['history']]
    
    return {
        'prices': prices,
        'dates': dates,
        'latest': data['latest'],
        'sources': data['sources'],
        'usd_thb': data['usd_thb']
    }

if __name__ == '__main__':
    print("=" * 60)
    print("  ทดสอบดึงราคาทองออนไลน์ + แปลงเป็นราคาทองไทย")
    print("=" * 60)
    
    result = fetch_all_online_data()
    
    if result['status'] == 'success':
        print(f"\nสถานะ: สำเร็จ")
        print(f"แหล่งข้อมูล: {result['sources']['yahoo']}")
        print(f"อัตราแลกเปลี่ยน: 1 USD = {result['usd_thb']:.2f} THB")
        print(f"\nราคาล่าสุด:")
        print(f"  Gold Spot:  USD/oz")
        print(f"  ราคาทองไทย: {result['latest']['price_thb']:,.2f} บาท/บาททองคำ")
        print(f"  วันที่: {result['latest']['date']}")
        print(f"\nข้อมูลย้อนหลัง: {len(result['history'])} วัน")
        print(f"\nตัวอย่าง 5 วันล่าสุด:")
        for item in result['history'][-5:]:
            print(f"  {item['date']}:  -> {item['price_thb_baht']:,.2f} บาท")
    else:
        print(f"\nError: ไม่สามารถดึงข้อมูลได้")
