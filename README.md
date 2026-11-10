# BJT DC Bias Web App

Flask Web Application สำหรับคำนวณ **DC Operating Point** ของวงจร BJT Common-Emitter แบบ Voltage-Divider Bias
รายวิชา **ENG29 2121 Computer Programming for Electrical Engineers** — Lab 02 (2/2569)

> **สถานะ: อยู่ระหว่างพัฒนา (Week 2)** — โครงสร้างโปรเจกต์และคำอธิบายด้านล่างคือเป้าหมายของ Lab 02
> หัวข้อที่ยังไม่สร้างจะถูกเพิ่มตามลำดับงานใน Implementation Plan

## ขอบเขตของ Lab 2

- รับค่าอินพุต: `VCC`, `R1`, `R2`, `RC`, `RE`, `β`, `VBE`
- คำนวณด้วย Python Backend: `VB`, `VE`, `VC`, `VCE`, `IC` (แสดง `IB`, `IE` ด้วย)
- ตรวจสอบอินพุตและแสดง warning เมื่ออยู่นอกช่วง Forward-Active
- มี automated tests ทั้งระดับ engineering logic และ HTTP route
- **ไม่รวม** AC, Transient, Signal Generator, SPICE Solver หรือ Circuit Editor

## ความต้องการของระบบ

- Python 3.10 ขึ้นไป (ทดสอบบน Python 3.15)
- Flask (ดู `requirements.txt`)

## การติดตั้งและรัน

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux / macOS
# source .venv/bin/activate

python -m pip install -r requirements.txt
python -m flask --app app run --debug
```

เปิดเบราว์เซอร์ที่ <http://127.0.0.1:5000/>

> ต้องเปิดผ่าน Flask Development Server เท่านั้น การเปิดไฟล์ `templates/index.html` ด้วย `file://`
> จะไม่มีการคำนวณจาก Python Backend

## การรัน Tests

```bash
python -m unittest discover -s tests -v
```

## โครงสร้างโปรเจกต์

```
.
├── app.py                  # Flask application & HTTP routes
├── dc_bias.py              # engineering calculations (ไม่รู้จัก HTML/HTTP)
├── templates/
│   └── index.html          # input form + DC results (Jinja)
├── static/
│   └── style.css           # responsive layout
├── tests/
│   ├── test_dc_bias.py     # unit tests for engineering logic
│   └── test_web.py         # Flask HTTP route tests
├── docs/
│   ├── design-note.md
│   ├── validation.md
│   └── reflection.md
├── requirements.txt
├── AGENTS.md
└── README.md
```

## แบบจำลองทางไฟฟ้า

Forward-Active Approximation (β คงที่, VBE คงที่):

```
VTH = VCC · R2 / (R1 + R2)
RTH = R1 · R2 / (R1 + R2)
IB  = (VTH − VBE) / (RTH + (β + 1)·RE)
IC  = β · IB
IE  = (β + 1) · IB
VE  = IE · RE
VB  = VE + VBE
VC  = VCC − IC · RC
VCE = VC − VE
```

### ข้อมูลทดลองอ้างอิง

`VCC = 12 V, R1 = 100 kΩ, R2 = 22 kΩ, RC = 2.2 kΩ, RE = 1 kΩ, β = 100, VBE = 0.70 V`

| VTH | RTH | IB | IC | IE | VE | VB | VC | VCE |
|---|---|---|---|---|---|---|---|---|
| 2.164 V | 18.03 kΩ | 12.30 µA | 1.230 mA | 1.242 mA | 1.242 V | 1.942 V | 9.294 V | 8.052 V |

ใช้ค่าชุดนี้ตรวจสอบผลลัพธ์ของเว็บ (Acceptance test A3)

## ข้อจำกัด

- ผลลัพธ์ใช้ได้เฉพาะเมื่อ transistor อยู่ใน Forward-Active Region
- ถ้า `VTH ≤ VBE` (cutoff) หรือ `VCE` ต่ำจนใกล้ saturation แอปต้องแสดง warning และไม่รายงานว่าแบบจำลองใช้ได้
- ไม่ใช่ ngspice และไม่ใช่ผลจำลองเชิงพาณิชย์

## ผู้จัดทำ

B6809720 Pakpoom — ENG29 2121 (2/2569)
