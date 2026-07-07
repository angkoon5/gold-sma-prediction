import pandas as pd
import numpy as np
import os

def load_data(filepath):
    """โหลดข้อมูลราคาทองคำจากไฟล์ Excel หรือ CSV"""
    ext = os.path.splitext(filepath)[1].lower()
    if ext in ['.xlsx', '.xls']:
        df = pd.read_excel(filepath)
    elif ext == '.csv':
        df = pd.read_csv(filepath)
    else:
        raise ValueError("รองรับเฉพาะไฟล์ .xlsx, .xls, .csv")
    return df

def calculate_sma(prices, window):
    """คำนวณ Simple Moving Average (ค่าเฉลี่ยเคลื่อนที่อย่างง่าย)
    
    สูตร: SMA(n) = (P1 + P2 + ... + Pn) / n
    - ทุกวันมีน้ำหนักเท่ากัน (1/n)
    - เริ่มคำนวณได้เมื่อมีข้อมูลครบ n วัน
    """
    sma = prices.rolling(window=window).mean()
    return sma

def calculate_ema(prices, span):
    """คำนวณ Exponential Moving Average (ค่าเฉลี่ยเคลื่อนที่แบบถ่วงน้ำหนัก)
    
    วิธีคำนวณ (ตามเอกสารอ้างอิง):
    1. ค่า EMA แรก = SMA ของ span วันแรก
    2. EMA(t) = Price(t) * alpha + EMA(t-1) * (1 - alpha)
    
    ค่า alpha (smoothing factor):
    - EMA3:  alpha = 2/(3+1)  = 0.5    → วันล่าสุดมีน้ำหนัก 50%
    - EMA5:  alpha = 2/(5+1)  = 0.333  → วันล่าสุดมีน้ำหนัก 33.3%
    - EMA10: alpha = 2/(10+1) = 0.182  → วันล่าสุดมีน้ำหนัก 18.2%
    """
    alpha = 2.0 / (span + 1)
    ema_values = [np.nan] * len(prices)
    
    # เริ่มต้น EMA ด้วย SMA ของ span วันแรก (ตามวิธีใน Excel อ้างอิง)
    if len(prices) >= span:
        first_sma = prices.iloc[:span].mean()
        ema_values[span - 1] = first_sma
        
        # คำนวณ EMA ตั้งแต่วันที่ span เป็นต้นไป
        for i in range(span, len(prices)):
            ema_values[i] = prices.iloc[i] * alpha + ema_values[i-1] * (1 - alpha)
    
    return pd.Series(ema_values, index=prices.index)

def calculate_rmse(actual, predicted):
    """คำนวณ Root Mean Square Error (ค่ารากที่สองของค่าเฉลี่ยกำลังสองของความคลาดเคลื่อน)
    
    สูตร: RMSE = sqrt( sum((actual_i - predicted_i)^2) / n )
    - ยิ่งค่าต่ำ = ยิ่งแม่นยำ
    """
    mask = ~(actual.isna() | predicted.isna())
    actual_clean = actual[mask]
    predicted_clean = predicted[mask]
    
    if len(actual_clean) == 0:
        return None
    
    rmse = np.sqrt(np.mean((actual_clean - predicted_clean) ** 2))
    return rmse

def analyze_gold_price(filepath):
    """วิเคราะห์ราคาทองคำด้วย SMA3, SMA5, SMA10, EMA3, EMA5, EMA10"""
    df = load_data(filepath)
    
    price_col = None
    possible_names = ['price', 'Price', 'ราคา', 'ราคาปิด', 'Close', 'close', 
                      'Adj Close', 'adj close', 'ราคาขาย', 'ราคาซื้อ']
    for col in df.columns:
        if col in possible_names:
            price_col = col
            break
    
    if price_col is None:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            price_col = numeric_cols[0]
        else:
            raise ValueError("ไม่พบคอลัมน์ราคาในไฟล์")
    
    prices = df[price_col].astype(float)
    
    # คำนวณ SMA
    sma3 = calculate_sma(prices, 3)
    sma5 = calculate_sma(prices, 5)
    sma10 = calculate_sma(prices, 10)
    
    # คำนวณ EMA
    ema3 = calculate_ema(prices, 3)
    ema5 = calculate_ema(prices, 5)
    ema10 = calculate_ema(prices, 10)
    
    # ราคาทำนาย = ค่า EMA/SMA ของวันก่อนหน้า
    predicted_sma3 = sma3.shift(1)
    predicted_sma5 = sma5.shift(1)
    predicted_sma10 = sma10.shift(1)
    predicted_ema3 = ema3.shift(1)
    predicted_ema5 = ema5.shift(1)
    predicted_ema10 = ema10.shift(1)
    
    # คำนวณ RMSE
    rmse_sma3 = calculate_rmse(prices, predicted_sma3)
    rmse_sma5 = calculate_rmse(prices, predicted_sma5)
    rmse_sma10 = calculate_rmse(prices, predicted_sma10)
    rmse_ema3 = calculate_rmse(prices, predicted_ema3)
    rmse_ema5 = calculate_rmse(prices, predicted_ema5)
    rmse_ema10 = calculate_rmse(prices, predicted_ema10)
    
    all_models = [
        ('SMA3', rmse_sma3), ('SMA5', rmse_sma5), ('SMA10', rmse_sma10),
        ('EMA3', rmse_ema3), ('EMA5', rmse_ema5), ('EMA10', rmse_ema10)
    ]
    best_model = min(all_models, key=lambda x: x[1] if x[1] is not None else float('inf'))
    
    results = {
        'prices': prices,
        'sma3': sma3, 'sma5': sma5, 'sma10': sma10,
        'ema3': ema3, 'ema5': ema5, 'ema10': ema10,
        'rmse_sma3': rmse_sma3, 'rmse_sma5': rmse_sma5, 'rmse_sma10': rmse_sma10,
        'rmse_ema3': rmse_ema3, 'rmse_ema5': rmse_ema5, 'rmse_ema10': rmse_ema10,
        'best_model': best_model
    }
    
    return results

def predict_next_price(prices_list, window):
    """ทำนายราคาวันถัดไปด้วย SMA
    = ค่าเฉลี่ยของราคา window วันล่าสุด
    """
    if len(prices_list) < window:
        return None
    return np.mean(prices_list[-window:])

def predict_next_price_ema(prices_list, span):
    """ทำนายราคาวันถัดไปด้วย EMA
    ใช้ค่า EMA ล่าสุดเป็นราคาทำนาย
    EMA(next) = Price(today) * alpha + EMA(yesterday) * (1-alpha)
    """
    if len(prices_list) < span:
        return None
    series = pd.Series(prices_list)
    ema = calculate_ema(series, span)
    # หาค่า EMA ล่าสุดที่ไม่เป็น NaN
    valid = ema.dropna()
    if len(valid) == 0:
        return None
    return float(valid.iloc[-1])
