"""
ระบบวิเคราะห์และทำนายราคาทองคำด้วย SMA
รันจาก Command Line: python run_analysis.py
"""
import os
import sys
import numpy as np
import pandas as pd
from sma_analysis import analyze_gold_price, predict_next_price

def print_header():
    print("=" * 60)
    print("   ระบบเปรียบเทียบแบบจำลอง SMA สำหรับทำนายราคาทองคำ")
    print("   (SMA3 vs SMA5 vs SMA10)")
    print("=" * 60)

def run_file_analysis():
    """วิเคราะห์จากไฟล์"""
    print("\n--- วิเคราะห์จากไฟล์ข้อมูล ---")
    filepath = input("กรอก path ไฟล์ (xlsx/csv): ").strip()
    
    if not os.path.exists(filepath):
        print(f"ไม่พบไฟล์: {filepath}")
        return
    
    try:
        results = analyze_gold_price(filepath)
        
        print(f"\nจำนวนข้อมูล: {len(results['prices'])} รายการ")
        print("\n" + "-" * 40)
        print(f"{'แบบจำลอง':<12} {'RMSE':<15} {'สถานะ'}")
        print("-" * 40)
        
        models = [
            ('SMA3', results['rmse3']),
            ('SMA5', results['rmse5']),
            ('SMA10', results['rmse10']),
        ]
        
        for name, rmse in models:
            status = "★ แม่นยำที่สุด" if name == results['best_model'][0] else ""
            print(f"{name:<12} {rmse:<15.4f} {status}")
        
        print("-" * 40)
        print(f"\n✓ สรุป: {results['best_model'][0]} มี RMSE ต่ำที่สุด ({results['best_model'][1]:.4f})")
        print(f"  จึงเป็นแบบจำลองที่เหมาะสมที่สุดสำหรับข้อมูลชุดนี้")
        
    except Exception as e:
        print(f"Error: {e}")

def run_manual_predict():
    """ทำนายจากการกรอกราคาเอง"""
    print("\n--- ทำนายราคาวันถัดไป ---")
    print("กรอกราคาย้อนหลัง (อย่างน้อย 3 วัน, สูงสุด 10 วัน)")
    print("กรอกเสร็จแล้วกด Enter โดยไม่พิมพ์อะไร\n")
    
    prices = []
    for i in range(10):
        val = input(f"  ราคาวันที่ {i+1}: ").strip()
        if not val:
            break
        try:
            prices.append(float(val))
        except ValueError:
            print("  กรุณากรอกตัวเลขเท่านั้น")
            continue
    
    if len(prices) < 3:
        print("ต้องมีข้อมูลอย่างน้อย 3 วัน")
        return
    
    print(f"\nข้อมูลที่กรอก: {prices}")
    print("\n" + "-" * 40)
    print(f"{'แบบจำลอง':<12} {'ราคาทำนาย'}")
    print("-" * 40)
    
    if len(prices) >= 3:
        pred3 = predict_next_price(prices, 3)
        print(f"{'SMA3':<12} {pred3:,.2f} บาท")
    if len(prices) >= 5:
        pred5 = predict_next_price(prices, 5)
        print(f"{'SMA5':<12} {pred5:,.2f} บาท")
    if len(prices) >= 10:
        pred10 = predict_next_price(prices, 10)
        print(f"{'SMA10':<12} {pred10:,.2f} บาท")
    
    print("-" * 40)

def main():
    print_header()
    
    while True:
        print("\n--- เมนูหลัก ---")
        print("1. วิเคราะห์ข้อมูลจากไฟล์ (เปรียบเทียบ RMSE)")
        print("2. ทำนายราคาจากการกรอกข้อมูลเอง")
        print("3. เปิดเว็บ (Web Interface)")
        print("0. ออก")
        
        choice = input("\nเลือก: ").strip()
        
        if choice == '1':
            run_file_analysis()
        elif choice == '2':
            run_manual_predict()
        elif choice == '3':
            print("\nกำลังเปิด Web Server...")
            print("เปิดเบราว์เซอร์ไปที่: http://127.0.0.1:5000")
            os.system("python app.py")
        elif choice == '0':
            print("\nขอบคุณที่ใช้งาน!")
            break
        else:
            print("กรุณาเลือก 0-3")

if __name__ == '__main__':
    main()
