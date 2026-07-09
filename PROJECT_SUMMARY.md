# ===============================================
# สรุปโครงสร้างโปรเจค: ระบบทำนายราคาทองคำด้วย SMA & EMA
# ===============================================
# ผู้จัดทำ: BAM_ORGAN_KHWANKAW
# ภาษา: Python 3.11
# Framework: Flask (Web), Pandas/NumPy (คำนวณ), Chart.js (กราฟ), Bootstrap 5 (UI)
# ===============================================

## โครงสร้างไฟล์ทั้งหมด

`
F:\PJ\
├── app.py                      # Flask Web Application (ตัวหลัก)
├── sma_analysis.py             # ฟังก์ชันคำนวณ SMA, EMA, RMSE
├── gold_fetcher.py             # ดึงราคาทองออนไลน์ (Yahoo Finance, Exchange Rate)
├── run_analysis.py             # รันจาก Command Line (เมนูโต้ตอบ)
├── requirements.txt            # รายการ packages ที่ใช้
├── Procfile                    # คำสั่งรันบน Render (deploy)
├── .python-version             # กำหนด Python version (3.11.9)
├── .gitignore                  # ไฟล์ที่ไม่ push ขึ้น git
├── README.md                   # คำอธิบายโปรเจค
├── data/
│   └── gold_ema_database.json  # ฐานข้อมูล EMA (158 วัน, 1ม.ค.-4ก.ค.69)
└── templates/
    └── index.html              # หน้าเว็บ (HTML + CSS + JavaScript)
`

---

## 1. app.py — Flask Web Application

**ภาษา:** Python
**หน้าที่:** เป็น Web Server หลัก รับ-ส่งข้อมูลระหว่างหน้าเว็บกับระบบคำนวณ

### Routes (เส้นทาง URL):

| Route | Method | หน้าที่ |
|-------|--------|---------|
| / | GET | แสดงหน้าเว็บหลัก |
| /upload | POST | อัปโหลดไฟล์ Excel/CSV แล้ววิเคราะห์ RMSE |
| /predict | POST | รับราคาที่กรอก แล้วทำนายราคาวันถัดไป |
| /online | GET | ดึงราคาออนไลน์ + คำนวณ SMA/EMA/RMSE |

### ฟังก์ชันสำคัญ:

- lookup_ema_from_db(prices_list, ema_type) — ค้นหาราคาในฐานข้อมูล ถ้าตรงจะดึง EMA ที่คำนวณไว้แล้ว
- calculate_ema3_manual(prices_3days) — คำนวณ EMA3 ด้วยสูตร (กรณีไม่พบในฐานข้อมูล)

---

## 2. sma_analysis.py — ฟังก์ชันคำนวณหลัก

**ภาษา:** Python
**หน้าที่:** คำนวณ SMA, EMA, RMSE ทั้งหมด

### ฟังก์ชัน:

| ฟังก์ชัน | หน้าที่ | สูตร |
|---------|---------|------|
| load_data(filepath) | โหลดไฟล์ Excel/CSV | - |
| calculate_sma(prices, window) | คำนวณ SMA | (P1+P2+...+Pn) / n |
| calculate_ema(prices, span) | คำนวณ EMA | EMA = Price×α + EMA_prev×(1-α) โดย α = 2/(n+1) |
| calculate_rmse(actual, predicted) | คำนวณค่าความคลาดเคลื่อน | √(Σ(actual-predicted)²/n) |
| nalyze_gold_price(filepath) | วิเคราะห์ครบทั้ง 6 แบบจำลอง | SMA3,5,10 + EMA3,5,10 |
| predict_next_price(prices, window) | ทำนายด้วย SMA | avg ของ n วันสุดท้าย |
| predict_next_price_ema(prices, span) | ทำนายด้วย EMA | EMA สุดท้าย = ราคาทำนาย |

### ค่า Alpha (ตัวคูณ EMA):
- **EMA3:** α = 2/(3+1) = **0.5** (50%)
- **EMA5:** α = 2/(5+1) = **0.3333** (33.33%)
- **EMA10:** α = 2/(10+1) = **0.1818** (18.18%)

### วิธีคำนวณ EMA:
1. ค่าเริ่มต้น = SMA ของ n วันแรก
2. EMA(t) = ราคาปิด(t) × α + EMA(t-1) × (1-α)

---

## 3. gold_fetcher.py — ดึงราคาออนไลน์

**ภาษา:** Python
**หน้าที่:** ดึงราคาทองจากเว็บชั้นนำ แปลงเป็นราคาทองไทย

### แหล่งข้อมูล:
- **Yahoo Finance** — Gold Futures (GC=F) ราคา USD/oz
- **Open Exchange Rates** — อัตราแลกเปลี่ยน USD/THB
- **GoldPriceZ.com** — ราคาย้อนหลัง

### ฟังก์ชัน:
| ฟังก์ชัน | หน้าที่ |
|---------|---------|
| etch_yahoo_gold(days) | ดึงราคา Gold Futures จาก Yahoo |
| etch_exchange_rate() | ดึง USD/THB |
| etch_goldpricez_history() | ดึงราคาย้อนหลัง |
| usd_to_thai_baht_gold(price, rate) | แปลง USD/oz → บาท/บาททองคำ |
| etch_all_online_data() | รวมทุกอย่าง + แปลงราคา |

### สูตรแปลงราคา:
`
ราคาทองไทย = (ราคา USD/oz) × (อัตรา THB) × (15.244g / 31.1035g) × 0.965
`
- 1 troy oz = 31.1035 กรัม
- 1 บาททองคำ = 15.244 กรัม
- ทองคำแท่ง 96.5%

---

## 4. data/gold_ema_database.json — ฐานข้อมูล EMA

**รูปแบบ:** JSON Array
**จำนวน:** 158 รายการ (1 ม.ค. 69 - 4 ก.ค. 69)

### โครงสร้างแต่ละรายการ:
`json
{
  "date": "2026-01-01",
  "price": 64450,
  "ema3": 64817,
  "ema5": 65160,
  "ema10": 65845
}
`

### วิธีใช้:
- เมื่อผู้ใช้กรอกราคา ระบบจะค้นหาว่าลำดับราคาตรงกับฐานข้อมูลหรือไม่
- ถ้าตรง → ดึง EMA จากฐาน (แม่นยำ เพราะคำนวณต่อเนื่อง 158 วัน)
- ถ้าไม่ตรง → คำนวณ EMA ใหม่จากข้อมูลที่กรอก

---

## 5. templates/index.html — หน้าเว็บ

**ภาษา:** HTML + CSS + JavaScript
**Libraries (CDN ออนไลน์):**
- **Bootstrap 5.3** — Layout, Grid, Responsive
- **Font Awesome 6** — Icons
- **Google Fonts (Noto Sans Thai)** — ฟอนต์ภาษาไทย
- **Chart.js 4** — กราฟเส้น

### ส่วนประกอบหน้าเว็บ:
1. **ดึงราคาออนไลน์** — กดปุ่มดึงจาก Yahoo Finance + วิเคราะห์
2. **กรอกราคาย้อนหลัง** — กรอก 3-10 วัน แล้วทำนาย
3. **อัปโหลดไฟล์** — ใส่ Excel/CSV วิเคราะห์ RMSE
4. **กราฟเปรียบเทียบ** — Chart.js แสดงราคาจริง vs SMA/EMA
5. **ตาราง RMSE** — เปรียบเทียบ 6 แบบจำลอง
6. **คำอธิบายวิธีคำนวณ** — สูตร SMA, EMA, RMSE

### JavaScript Functions:
| ฟังก์ชัน | หน้าที่ |
|---------|---------|
| etchOnline() | เรียก API /online แล้วแสดงผล |
| uploadFile() | ส่งไฟล์ไป /upload แล้วแสดงผล |
| predictPrice() | ส่งราคาไป /predict แล้วแสดงผล |
| showChart(data) | วาดกราฟ Chart.js |

---

## 6. run_analysis.py — รันจาก Command Line

**ภาษา:** Python
**หน้าที่:** เมนูโต้ตอบสำหรับรันโดยไม่ต้องเปิดเว็บ

### เมนู:
1. วิเคราะห์จากไฟล์ (ใส่ path)
2. กรอกราคาทำนายเอง
3. เปิด Web Server

---

## 7. ไฟล์ Deploy (Render.com)

| ไฟล์ | หน้าที่ |
|------|---------|
| Procfile | คำสั่งรัน: web: gunicorn app:app |
| .python-version | กำหนด Python 3.11.9 |
| equirements.txt | packages ที่ต้องติดตั้ง |

---

## สรุปแบบจำลองที่เปรียบเทียบ (6 แบบ)

| แบบจำลอง | ประเภท | n วัน | ตัวคูณ α | ลักษณะ |
|----------|--------|-------|---------|--------|
| SMA3 | Simple | 3 | - | เฉลี่ยเท่ากัน ไวต่อราคาล่าสุด |
| SMA5 | Simple | 5 | - | เฉลี่ยเท่ากัน ปานกลาง |
| SMA10 | Simple | 10 | - | เฉลี่ยเท่ากัน เรียบ ตอบสนองช้า |
| EMA3 | Exponential | 3 | 0.5 | ถ่วงน้ำหนัก วันล่าสุด 50% |
| EMA5 | Exponential | 5 | 0.333 | ถ่วงน้ำหนัก วันล่าสุด 33% |
| EMA10 | Exponential | 10 | 0.182 | ถ่วงน้ำหนัก วันล่าสุด 18% |

### วิธีเปรียบเทียบ:
1. ใช้ SMA/EMA ของวันก่อนหน้าเป็น "ราคาทำนาย" สำหรับวันนี้
2. คำนวณ RMSE = √(Σ(ราคาจริง - ราคาทำนาย)²/n)
3. RMSE ต่ำสุด = แบบจำลองที่แม่นยำที่สุด

---

## วิธีรัน

### บนเครื่อง:
`ash
pip install -r requirements.txt
python app.py
# เปิด http://127.0.0.1:5000
`

### Deploy บน Render:
- Push ขึ้น GitHub
- สร้าง Web Service บน Render เชื่อม repo
- URL: https://gold-sma-prediction.onrender.com

---
By BAM_ORGAN_KHWANKAW
