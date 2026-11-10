# BJT DC Bias Web App

Flask Web Application สำหรับคำนวณ **DC Operating Point** ของวงจร BJT Common-Emitter แบบ Voltage-Divider Bias
รายวิชา **ENG29 2121 Computer Programming for Electrical Engineers** — Lab 02 (2/2569)

> **สถานะ: พร้อมใช้งาน** — ผ่านการทดสอบ 33 tests (`unittest`) และตรวจผลกับค่าอ้างอิงอิสระแล้ว
> (ดู `docs/validation.md`)

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
python -m unittest discover -s tests -t . -v
```

ผลที่ต้องได้: `Ran 33 tests ... OK` (21 tests ของสมการ + 12 tests ของ HTTP)

> คำสั่งนี้ใช้ได้ทั้งแบบมีและไม่มี `-t .` (ใบงานใช้ `discover -s tests -v` ก็ผ่าน)
> แต่ถ้าเจอ ImportError ให้เติม `-t .` เพราะ `tests/` เป็น package

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
│   ├── __init__.py         # ทำให้ discover -s tests -t . ทำงานได้
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

## ตัวอย่างการใช้งาน

1. เปิด <http://127.0.0.1:5000/>
2. กรอกค่าตามตารางด้านบน (ตัวต้านทานเป็น **kΩ** — ใต้ช่องจะแสดงค่าที่แปลงเป็น Ω ให้ตรวจ)
3. กด **Calculate DC Bias**

ผลที่ได้:

```
Active
VTH  2.164 V      RTH 18.03 kΩ
IB  12.299 µA     IC  1.230 mA     IE  1.242 mA
VB   1.942 V      VE  1.242 V      VC  9.294 V      VCE 8.052 V
```

### การจัดการข้อผิดพลาดและ warning

| สถานการณ์ | สิ่งที่เกิดขึ้น |
|---|---|
| กรอกค่าที่ไม่ใช่ตัวเลข (เช่น `abc`, `12,0`) | หน้าเดิม + ข้อความ `กรุณากรอกตัวเลข…` (HTTP 200 ไม่ crash) |
| ความต้านทาน ≤ 0 | ข้อความ `ค่าความต้านทานต้องมากกว่า 0 Ω (พบ R1 = 0 Ω)` |
| `VTH ≤ VBE` | badge `Cutoff`, กระแสทุกตัวเป็น 0, พร้อม warning |
| `VCE ≤ 0.3 V` | badge `Saturation`, พร้อม warning ว่า VCE ไม่น่าเชื่อถือ |

## เอกสารเพิ่มเติม

| ไฟล์ | เนื้อหา |
|---|---|
| `docs/design-note.md` | เหตุผลเบื้องหลังการออกแบบแต่ละจุด |
| `docs/validation.md` | หลักฐานว่าผลตรงกับค่าที่คำนวณอิสระ (50 หลัก) |
| `docs/reflection.md` | สิ่งที่เรียนรู้และข้อจำกัดของแบบจำลอง |
| `AGENTS.md` | กติกาการแก้โค้ด (สำหรับ AI agent และผู้ร่วมงาน) |


## ข้อจำกัด

- ผลลัพธ์ใช้ได้เฉพาะเมื่อ transistor อยู่ใน Forward-Active Region
- ถ้า `VTH ≤ VBE` (cutoff) หรือ `VCE` ต่ำจนใกล้ saturation แอปต้องแสดง warning และไม่รายงานว่าแบบจำลองใช้ได้
- ไม่ใช่ ngspice และไม่ใช่ผลจำลองเชิงพาณิชย์

## ผู้จัดทำ

B6809720 Pakpoom — ENG29 2121 (2/2569)
