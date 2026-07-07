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
    """คำนวณ Simple Moving Average"""
    sma = prices.rolling(window=window).mean()
    return sma

def calculate_rmse(actual, predicted):
    """คำนวณ Root Mean Square Error"""
    # ตัดค่า NaN ออก
    mask = ~(actual.isna() | predicted.isna())
    actual_clean = actual[mask]
    predicted_clean = predicted[mask]
    
    if len(actual_clean) == 0:
        return None
    
    rmse = np.sqrt(np.mean((actual_clean - predicted_clean) ** 2))
    return rmse

def analyze_gold_price(filepath):
    """วิเคราะห์ราคาทองคำด้วย SMA3, SMA5, SMA10 และเปรียบเทียบ RMSE"""
    df = load_data(filepath)
    
    # หาคอลัมน์ราคา (รองรับชื่อคอลัมน์ภาษาไทยและอังกฤษ)
    price_col = None
    possible_names = ['price', 'Price', 'ราคา', 'ราคาปิด', 'Close', 'close', 
                      'Adj Close', 'adj close', 'ราคาขาย', 'ราคาซื้อ']
    for col in df.columns:
        if col in possible_names:
            price_col = col
            break
    
    if price_col is None:
        # ถ้าหาไม่เจอ ใช้คอลัมน์ตัวเลขคอลัมน์แรก
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
    
    # SMA ที่คำนวณได้คือ "ราคาทำนาย" ของวันนั้น
    # เปรียบเทียบกับราคาจริงของวันถัดไป (shift SMA ไป 1 วัน)
    predicted_sma3 = sma3.shift(1)
    predicted_sma5 = sma5.shift(1)
    predicted_sma10 = sma10.shift(1)
    
    # คำนวณ RMSE
    rmse3 = calculate_rmse(prices, predicted_sma3)
    rmse5 = calculate_rmse(prices, predicted_sma5)
    rmse10 = calculate_rmse(prices, predicted_sma10)
    
    results = {
        'prices': prices,
        'sma3': sma3,
        'sma5': sma5,
        'sma10': sma10,
        'predicted_sma3': predicted_sma3,
        'predicted_sma5': predicted_sma5,
        'predicted_sma10': predicted_sma10,
        'rmse3': rmse3,
        'rmse5': rmse5,
        'rmse10': rmse10,
        'best_model': min([('SMA3', rmse3), ('SMA5', rmse5), ('SMA10', rmse10)], 
                         key=lambda x: x[1] if x[1] is not None else float('inf'))
    }
    
    return results

def predict_next_price(prices_list, window):
    """ทำนายราคาวันถัดไปจากราคาย้อนหลัง"""
    if len(prices_list) < window:
        return None
    return np.mean(prices_list[-window:])
