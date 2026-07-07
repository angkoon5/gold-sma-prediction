from flask import Flask, render_template, request, jsonify
import os
import json
import numpy as np
import pandas as pd
from sma_analysis import (analyze_gold_price, predict_next_price, predict_next_price_ema,
                           load_data, calculate_sma, calculate_ema, calculate_rmse)
from gold_fetcher import fetch_all_online_data

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'data'

# โหลดฐานข้อมูล EMA3 (1 ม.ค. 69 - 4 ก.ค. 69)
EMA_DB = []
ema_db_path = os.path.join('data', 'gold_ema_database.json')
if os.path.exists(ema_db_path):
    with open(ema_db_path, 'r', encoding='utf-8') as f:
        EMA_DB = json.load(f)

def lookup_ema3_from_db(prices_3days):
    """ตรวจว่าราคา 3 วันตรงกับลำดับในฐานข้อมูลหรือไม่
    ถ้าตรง ดึงค่า EMA3 ของวันสุดท้ายมาเลย
    """
    if len(EMA_DB) < 3:
        return None
    
    p1, p2, p3 = int(prices_3days[0]), int(prices_3days[1]), int(prices_3days[2])
    
    for i in range(len(EMA_DB) - 2):
        if (EMA_DB[i]['price'] == p1 and 
            EMA_DB[i+1]['price'] == p2 and 
            EMA_DB[i+2]['price'] == p3):
            # พบ! ดึง EMA3 ของวันสุดท้าย
            return EMA_DB[i+2]['ema3']
    
    return None

def calculate_ema3_manual(prices_3days):
    """คำนวณ EMA3 เองกรณีไม่มีในฐานข้อมูล
    สูตร (alpha = 0.5):
    1. Initial EMA = ค่าเฉลี่ย 3 วัน
    2. EMA1 = 0.5 * ราคาวันที่ 1 + 0.5 * Initial EMA
    3. EMA2 = 0.5 * ราคาวันที่ 2 + 0.5 * EMA1
    4. EMA3 = 0.5 * ราคาวันที่ 3 + 0.5 * EMA2
    ค่า EMA3 = ราคาทำนายวันถัดไป
    """
    alpha = 0.5
    initial_ema = sum(prices_3days) / 3
    ema1 = alpha * prices_3days[0] + (1 - alpha) * initial_ema
    ema2 = alpha * prices_3days[1] + (1 - alpha) * ema1
    ema3 = alpha * prices_3days[2] + (1 - alpha) * ema2
    return round(ema3, 2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'ไม่พบไฟล์'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'ไม่ได้เลือกไฟล์'}), 400
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)
    try:
        results = analyze_gold_price(filepath)
        response = {
            'success': True,
            'rmse_sma3': round(results['rmse_sma3'], 4) if results['rmse_sma3'] else None,
            'rmse_sma5': round(results['rmse_sma5'], 4) if results['rmse_sma5'] else None,
            'rmse_sma10': round(results['rmse_sma10'], 4) if results['rmse_sma10'] else None,
            'rmse_ema3': round(results['rmse_ema3'], 4) if results['rmse_ema3'] else None,
            'rmse_ema5': round(results['rmse_ema5'], 4) if results['rmse_ema5'] else None,
            'rmse_ema10': round(results['rmse_ema10'], 4) if results['rmse_ema10'] else None,
            'best_model': results['best_model'][0],
            'best_rmse': round(results['best_model'][1], 4),
            'data_count': len(results['prices']),
            'prices': results['prices'].tolist()[-30:],
            'sma3': [x if not np.isnan(x) else None for x in results['sma3'].tolist()[-30:]],
            'sma5': [x if not np.isnan(x) else None for x in results['sma5'].tolist()[-30:]],
            'sma10': [x if not np.isnan(x) else None for x in results['sma10'].tolist()[-30:]],
            'ema3': [x if not pd.isna(x) else None for x in results['ema3'].tolist()[-30:]],
            'ema5': [x if not pd.isna(x) else None for x in results['ema5'].tolist()[-30:]],
            'ema10': [x if not pd.isna(x) else None for x in results['ema10'].tolist()[-30:]],
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    prices = data.get('prices', [])
    try:
        prices = [float(p) for p in prices if p]
    except ValueError:
        return jsonify({'error': 'กรุณากรอกตัวเลขเท่านั้น'}), 400
    
    results = {}
    ema3_source = None
    
    if len(prices) >= 3:
        results['sma3'] = round(predict_next_price(prices, 3), 2)
        
        # EMA3: ลองดึงจากฐานข้อมูลก่อน
        last_3 = prices[-3:]
        db_ema3 = lookup_ema3_from_db(last_3)
        if db_ema3 is not None:
            results['ema3'] = db_ema3
            ema3_source = 'database'
        else:
            results['ema3'] = calculate_ema3_manual(last_3)
            ema3_source = 'calculated'
    
    if len(prices) >= 5:
        results['sma5'] = round(predict_next_price(prices, 5), 2)
        results['ema5'] = round(predict_next_price_ema(prices, 5), 2)
    if len(prices) >= 10:
        results['sma10'] = round(predict_next_price(prices, 10), 2)
        results['ema10'] = round(predict_next_price_ema(prices, 10), 2)
    
    if not results:
        return jsonify({'error': 'ต้องมีข้อมูลอย่างน้อย 3 วัน'}), 400
    
    return jsonify({
        'success': True, 
        'predictions': results,
        'ema3_source': ema3_source
    })

@app.route('/online', methods=['GET'])
def online_prices():
    try:
        online_data = fetch_all_online_data()
        if online_data['status'] != 'success':
            return jsonify({'error': 'ไม่สามารถดึงข้อมูลออนไลน์ได้'}), 400
        prices = [item['price_thb_baht'] for item in online_data['history']]
        dates = [item['date'] for item in online_data['history']]
        if len(prices) < 10:
            return jsonify({'error': f'ข้อมูลไม่เพียงพอ (ได้ {len(prices)} วัน, ต้องการ 10+)'}), 400
        
        prices_series = pd.Series(prices)
        sma3 = prices_series.rolling(window=3).mean()
        sma5 = prices_series.rolling(window=5).mean()
        sma10 = prices_series.rolling(window=10).mean()
        ema3 = calculate_ema(prices_series, 3)
        ema5 = calculate_ema(prices_series, 5)
        ema10 = calculate_ema(prices_series, 10)
        
        rmse_sma3 = calculate_rmse(prices_series, sma3.shift(1))
        rmse_sma5 = calculate_rmse(prices_series, sma5.shift(1))
        rmse_sma10 = calculate_rmse(prices_series, sma10.shift(1))
        rmse_ema3 = calculate_rmse(prices_series, ema3.shift(1))
        rmse_ema5 = calculate_rmse(prices_series, ema5.shift(1))
        rmse_ema10 = calculate_rmse(prices_series, ema10.shift(1))
        
        all_models = [
            ('SMA3', rmse_sma3), ('SMA5', rmse_sma5), ('SMA10', rmse_sma10),
            ('EMA3', rmse_ema3), ('EMA5', rmse_ema5), ('EMA10', rmse_ema10)
        ]
        best = min(all_models, key=lambda x: x[1] if x[1] else float('inf'))
        
        # EMA3 prediction: ใช้ค่า EMA ล่าสุด
        ema3_valid = ema3.dropna()
        ema5_valid = ema5.dropna()
        ema10_valid = ema10.dropna()
        
        pred_tomorrow = {
            'sma3': round(float(np.mean(prices[-3:])), 2),
            'sma5': round(float(np.mean(prices[-5:])), 2),
            'sma10': round(float(np.mean(prices[-10:])), 2),
            'ema3': round(float(ema3_valid.iloc[-1]), 2) if len(ema3_valid) > 0 else None,
            'ema5': round(float(ema5_valid.iloc[-1]), 2) if len(ema5_valid) > 0 else None,
            'ema10': round(float(ema10_valid.iloc[-1]), 2) if len(ema10_valid) > 0 else None,
        }
        
        response = {
            'success': True,
            'latest': online_data['latest'],
            'sources': online_data['sources'],
            'usd_thb': online_data['usd_thb'],
            'note': online_data['note'],
            'data_count': len(prices),
            'dates': dates[-30:],
            'prices': [round(p, 2) for p in prices[-30:]],
            'sma3': [round(x, 2) if not np.isnan(x) else None for x in sma3.tolist()[-30:]],
            'sma5': [round(x, 2) if not np.isnan(x) else None for x in sma5.tolist()[-30:]],
            'sma10': [round(x, 2) if not np.isnan(x) else None for x in sma10.tolist()[-30:]],
            'ema3': [round(x, 2) if not pd.isna(x) else None for x in ema3.tolist()[-30:]],
            'ema5': [round(x, 2) if not pd.isna(x) else None for x in ema5.tolist()[-30:]],
            'ema10': [round(x, 2) if not pd.isna(x) else None for x in ema10.tolist()[-30:]],
            'rmse_sma3': round(rmse_sma3, 4) if rmse_sma3 else None,
            'rmse_sma5': round(rmse_sma5, 4) if rmse_sma5 else None,
            'rmse_sma10': round(rmse_sma10, 4) if rmse_sma10 else None,
            'rmse_ema3': round(rmse_ema3, 4) if rmse_ema3 else None,
            'rmse_ema5': round(rmse_ema5, 4) if rmse_ema5 else None,
            'rmse_ema10': round(rmse_ema10, 4) if rmse_ema10 else None,
            'best_model': best[0],
            'best_rmse': round(best[1], 4) if best[1] else None,
            'prediction_tomorrow': pred_tomorrow
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    print(f"EMA Database loaded: {len(EMA_DB)} records")
    print("=" * 60)
    print("  ระบบทำนายราคาทองคำด้วย SMA + EMA")
    print("  เปิดเบราว์เซอร์ไปที่: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, port=5000)
