from flask import Flask, render_template, request, jsonify
import os
import numpy as np
import pandas as pd
from sma_analysis import analyze_gold_price, predict_next_price, load_data, calculate_sma, calculate_rmse
from gold_fetcher import fetch_all_online_data, get_online_prices_for_sma

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'data'

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
            'rmse3': round(results['rmse3'], 4) if results['rmse3'] else None,
            'rmse5': round(results['rmse5'], 4) if results['rmse5'] else None,
            'rmse10': round(results['rmse10'], 4) if results['rmse10'] else None,
            'best_model': results['best_model'][0],
            'best_rmse': round(results['best_model'][1], 4),
            'data_count': len(results['prices']),
            'prices': results['prices'].tolist()[-30:],
            'sma3': [x if not np.isnan(x) else None for x in results['sma3'].tolist()[-30:]],
            'sma5': [x if not np.isnan(x) else None for x in results['sma5'].tolist()[-30:]],
            'sma10': [x if not np.isnan(x) else None for x in results['sma10'].tolist()[-30:]],
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
    if len(prices) >= 3:
        results['sma3'] = round(predict_next_price(prices, 3), 2)
    if len(prices) >= 5:
        results['sma5'] = round(predict_next_price(prices, 5), 2)
    if len(prices) >= 10:
        results['sma10'] = round(predict_next_price(prices, 10), 2)
    
    if not results:
        return jsonify({'error': 'ต้องมีข้อมูลอย่างน้อย 3 วัน'}), 400
    
    return jsonify({'success': True, 'predictions': results})

@app.route('/online', methods=['GET'])
def online_prices():
    """ดึงราคาทองออนไลน์จากเว็บชั้นนำ พร้อมคำนวณ SMA และ RMSE"""
    try:
        online_data = fetch_all_online_data()
        
        if online_data['status'] != 'success':
            return jsonify({'error': 'ไม่สามารถดึงข้อมูลออนไลน์ได้'}), 400
        
        prices = [item['price_thb_baht'] for item in online_data['history']]
        dates = [item['date'] for item in online_data['history']]
        
        if len(prices) < 10:
            return jsonify({'error': f'ข้อมูลไม่เพียงพอ (ได้ {len(prices)} วัน, ต้องการ 10+)'}), 400
        
        # คำนวณ SMA
        prices_series = pd.Series(prices)
        sma3 = prices_series.rolling(window=3).mean()
        sma5 = prices_series.rolling(window=5).mean()
        sma10 = prices_series.rolling(window=10).mean()
        
        # คำนวณ RMSE (เปรียบเทียบ SMA วันก่อนหน้ากับราคาจริงวันนี้)
        pred_sma3 = sma3.shift(1)
        pred_sma5 = sma5.shift(1)
        pred_sma10 = sma10.shift(1)
        
        rmse3 = calculate_rmse(prices_series, pred_sma3)
        rmse5 = calculate_rmse(prices_series, pred_sma5)
        rmse10 = calculate_rmse(prices_series, pred_sma10)
        
        best = min([('SMA3', rmse3), ('SMA5', rmse5), ('SMA10', rmse10)],
                   key=lambda x: x[1] if x[1] else float('inf'))
        
        # ทำนายราคาวันถัดไป
        pred_tomorrow = {
            'sma3': round(float(np.mean(prices[-3:])), 2),
            'sma5': round(float(np.mean(prices[-5:])), 2),
            'sma10': round(float(np.mean(prices[-10:])), 2),
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
            'rmse3': round(rmse3, 4) if rmse3 else None,
            'rmse5': round(rmse5, 4) if rmse5 else None,
            'rmse10': round(rmse10, 4) if rmse10 else None,
            'best_model': best[0],
            'best_rmse': round(best[1], 4) if best[1] else None,
            'prediction_tomorrow': pred_tomorrow
        }
        
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    print("=" * 60)
    print("  ระบบทำนายราคาทองคำด้วย SMA")
    print("  + ดึงข้อมูลออนไลน์จาก Yahoo Finance & GoldPriceZ")
    print("  เปิดเบราว์เซอร์ไปที่: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, port=5000)
