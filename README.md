# ระบบทำนายราคาทองคำด้วย SMA (Simple Moving Average)

เปรียบเทียบแบบจำลอง SMA3, SMA5, SMA10 พร้อมคำนวณค่า RMSE

## วิธีติดตั้ง

`ash
pip install -r requirements.txt
`

## วิธีใช้งาน

### แบบที่ 1: Web Interface (แนะนำ)
`ash
python app.py
`
จากนั้นเปิดเบราว์เซอร์ไปที่ http://127.0.0.1:5000

### แบบที่ 2: Command Line
`ash
python run_analysis.py
`

## ฟีเจอร์

1. **อัปโหลดไฟล์ข้อมูล** - รองรับ .xlsx, .xls, .csv
2. **คำนวณ SMA3, SMA5, SMA10** - ค่าเฉลี่ยเคลื่อนที่ 3, 5, 10 วัน
3. **คำนวณ RMSE** - วัดความคลาดเคลื่อนของแต่ละแบบจำลอง
4. **เปรียบเทียบ** - แบบจำลองไหน RMSE ต่ำสุด = แม่นยำสุด
5. **ทำนายราคา** - กรอกราคาย้อนหลังเพื่อทำนายวันถัดไป

## ข้อมูลตัวอย่าง

สร้างข้อมูลจำลองด้วย:
`ash
python create_sample_data.py
`
ไฟล์จะอยู่ที่ data/sample_gold_prices.xlsx

## โครงสร้างไฟล์

`
F:\PJ\
├── app.py                  # Flask Web Server
├── sma_analysis.py         # Logic คำนวณ SMA และ RMSE
├── run_analysis.py         # Command Line Interface
├── create_sample_data.py   # สร้างข้อมูลตัวอย่าง
├── requirements.txt        # Dependencies
├── templates/
│   └── index.html          # หน้าเว็บ
├── data/
│   ├── sample_gold_prices.xlsx
│   └── sample_gold_prices.csv
└── README.md
`

## สูตรที่ใช้

- **SMA(n)** = (P1 + P2 + ... + Pn) / n
- **RMSE** = sqrt( Σ(actual - predicted)² / n )

RMSE ต่ำ = ทำนายแม่นยำ
