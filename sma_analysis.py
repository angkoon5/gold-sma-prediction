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

def calculate_ema(prices, span):
    """คำนวณ Exponential Moving Average"""
    ema = prices.ewm(span=span, adjust=False).mean()
    return ema

def calculate_rmse(actual, predicted):
    """คำนวณ Root Mean Square Error"""
    mask = ~(actual.isna() | predicted.isna())
    actual_clean = actual[mask]
    predicted_clean = predicted[mask]
    
    if len(actual_clean) == 0:
        return None
    
    rmse = np.sqrt(np.mean((actual_clean - predicted_clean) ** 2))
    return rmse

def analyze_gold_price(filepath):
    """วิเคราะห์ราคาทองคำด้วย SMA3, SMA5, SMA10, EMA3 และเปรียบเทียบ RMSE"""
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
    
    # คำนวณ EMA3
    ema3 = calculate_ema(prices, 3)
    
    # เปรียบเทียบกับราคาจริงของวันถัดไป (shift ไป 1 วัน)
    predicted_sma3 = sma3.shift(1)
    predicted_sma5 = sma5.shift(1)
    predicted_sma10 = sma10.shift(1)
    predicted_ema3 = ema3.shift(1)
    
    # คำนวณ RMSE
    rmse3 = calculate_rmse(prices, predicted_sma3)
    rmse5 = calculate_rmse(prices, predicted_sma5)
    rmse10 = calculate_rmse(prices, predicted_sma10)
    rmse_ema3 = calculate_rmse(prices, predicted_ema3)
    
    all_models = [('SMA3', rmse3), ('SMA5', rmse5), ('SMA10', rmse10), ('EMA3', rmse_ema3)]
    best_model = min(all_models, key=lambda x: x[1] if x[1] is not None else float('inf'))
    
    results = {
        'prices': prices,
        'sma3': sma3,
        'sma5': sma5,
        'sma10': sma10,
        'ema3': ema3,
        'predicted_sma3': predicted_sma3,
        'predicted_sma5': predicted_sma5,
        'predicted_sma10': predicted_sma10,
        'predicted_ema3': predicted_ema3,
        'rmse3': rmse3,
        'rmse5': rmse5,
        'rmse10': rmse10,
        'rmse_ema3': rmse_ema3,
        'best_model': best_model
    }
    
    return results

def predict_next_price(prices_list, window):
    """ทำนายราคาวันถัดไปจากราคาย้อนหลัง (SMA)"""
    if len(prices_list) < window:
        return None
    return np.mean(prices_list[-window:])

def predict_next_price_ema(prices_list, span):
    """ทำนายราคาวันถัดไปด้วย EMA"""
    if len(prices_list) < span:
        return None
    series = pd.Series(prices_list)
    ema = series.ewm(span=span, adjust=False).mean()
    return float(ema.iloc[-1])
