# BJT DC Bias Web App

Flask Web Application สำหรับคำนวณ **DC Operating Point** ของวงจร BJT Common-Emitter ได้ 3 แบบ
รายวิชา **ENG29 2121 Computer Programming for Electrical Engineers** — Lab 03 (2/2569)

ต่อยอดจาก Lab 02 (Voltage Divider Bias เดิม) โดยเพิ่ม **Fixed Bias** และ **Emitter Bias แบบแหล่งจ่ายเดียว**
ผลของ Voltage Divider เมื่อกรอกค่าเดิมยังเหมือนเดิมทุกประการ

> **สถานะ: Lab 3 พร้อมใช้งาน + Lab 4 เพิ่มแล้ว** — 65 tests ผ่าน (`unittest`) และตรวจผลจริงผ่าน OpenCode Browser / Chrome headless ตามตาราง A1–A5 และ B1–B8 (ดู `docs/validation.md`)

- GitHub: <https://github.com/B6809720Pakpoom/BJT-DC-Bias-Web-App>
- Commit SHA ของ Lab 3: *(เจ้าของโปรเจกต์กรอกหลัง commit ผ่าน GitHub Desktop)*
- Commit SHA ของ Lab 4 (push แล้ว): `6c0881a157a41f0ef8684568a3ab7a8a5e29ed5d` — <https://github.com/B6809720Pakpoom/BJT-DC-Bias-Web-App/commit/6c0881a157a41f0ef8684568a3ab7a8a5e29ed5d>

## Lab 4 — BJT CE Amplifier Simulator (ngspice)

ต่อยอดจาก Lab 3 โดยเพิ่มการจำลองวงจร **CE Voltage Divider อ้างอิง 1 วงจร** ด้วย ngspice จริง
(default ของ Analysis Mode ยังเป็น `Analytical DC Bias (Lab 3)` → พฤติกรรม Lab 3 ไม่เปลี่ยน)

| Analysis | ปุ่ม | ผลที่ได้ |
|---|---|---|
| `SPICE DC · .op` | Run DC Simulation | VB, VE, VC, VCE, IC แบบปัดตามหน่วย |
| `SPICE AC · .ac` | Run AC Simulation | กราฟ Gain (dB) และ **Phase (degree)** เทียบ frequency (Hz, log), peak gain/phase, cutoff −3 dB |
| `SPICE Transient · .tran` | Run Transient Simulation | Vout/Vin (V) เทียบเวลา (ms), gain, **phase Vout vs Vin** และการกลับเฟส |

- ทุกผลมาจาก `ngspice_con.exe` → ไฟล์ `run.raw` → `spice_engine.py` **ไม่มี mock data และไม่ hard-code กราฟ**
- แสดง **Engine status** (`success`), **Engine version**, **BJT model**, **netlist ที่ส่งจริง** และ **Reference/วิธีอ่านผล** เสมอ
- ถ้าไม่มีจุดตัด −3 dB ในช่วง sweep จะโชว์ `not determined in sweep range` (ไม่แต่งตัวเลข fL/fH)
- ตาราง SPICE กับตาราง Analytical อยู่คนละหัวข้อ ไม่นำผลมาปนกัน
- ถ้า engine หรืออินพุตผิด จะแจ้ง error และ **ไม่แสดง**ผล/กราฟเก่า
- ภาพหลักฐานจริงอยู่ใน `captures/` (`b4_ac_desktop.png`, `b5_tran_desktop.png`, `b8_desktop.png`, `b8_mobile.png`)

### ติดตั้ง ngspice (Windows)

`winget` ไม่มี package นี้ → โหลด `ngspice-47_64.7z` จาก <https://ngspice.sourceforge.io/download.html>
แล้วแตกด้วย 7-Zip แล้วเพิ่ม `...\ngspice-47\Spice64\bin` ลง `PATH` ของ user

```powershell
ngspice_con.exe --version   # ต้องเห็น ** ngspice-47
```

> **หมายเหตุสำคัญ:** ไม่มี Starter Kit จากอาจารย์ จึงใช้ model
> `.model QNPN NPN(IS=2e-15 BF=100 VAF=0 CJE=10p CJC=5p TF=0.3n)`
> (เจ้าของโปรเจกต์อนุมัติแล้ว) — แสดงอยู่ในหน้าเว็บและใน `docs/validation.md` ข้อ 19

Playwright MCP และ Impeccable ไม่พร้อมใน session นี้ (ไม่มี MCP/skill และไม่มี `node`/`npx`) จึงใช้ OpenCode Browser + Chrome headless (เฉพาะ screenshot) + CSS แทน และบันทึก `NOT RUN` ไว้ใน `docs/validation.md` ข้อ 20

## ขอบเขตของ Lab 3

- เลือกโหมดได้ 3 แบบ: `divider`, `fixed`, `emitter`
- รับเฉพาะอินพุตที่วงจรที่เลือกใช้:
  - Fixed: `VCC`, `RB`, `RC`, `β`, `VBE`
  - Emitter: `VCC`, `RB`, `RE`, `RC`, `β`, `VBE`
  - Divider: `VCC`, `R1`, `R2`, `RE`, `RC`, `β`, `VBE`
- คำนวณด้วย Python Backend: `IB`, `IC`, `IE`, `VB`, `VE`, `VC`, `VCE` และ region
- ตรวจอินพุตผิด/ไม่ครบ/โหมดไม่รู้จัก และแสดงข้อความเป็นภาษาไทย
- ไม่โชว์ผลรอบก่อนเป็นผลของรอบที่กรอกผิด
- **ขอบเขต Lab 3 เดิม ไม่รวม** AC, Transient, Signal Generator, SPICE Solver หรือ Circuit Editor (Lab 4 เพิ่ม `.op/.ac/.tran` แล้ว — ดูหัวข้อก่อนหน้า)

## ความต้องการของระบบ

- Python 3.10 ขึ้นไป (ทดสอบบน Python 3.15.2)
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

ผลที่ต้องได้: `Ran 65 tests ... OK` (33 เดิมของ Lab 2 + 19 ของ Lab 3 + 13 ใหม่ของ Lab 4)

> 13 tests ใหม่ของ Lab 4 แบ่งเป็น `tests/test_spice_engine.py` 10 tests
> (5 netlist/validation + 5 เรียก ngspice จริง) และ `tests/test_web.py::SpicePages` 3 tests
> (จะข้ามอัตโนมัติถ้าเครื่องไม่มี ngspice)

> คำสั่งนี้ใช้ได้ทั้งแบบมีและไม่มี `-t .` (ใบงานใช้ `discover -s tests -v` ก็ผ่าน)
> แต่ถ้าเจอ ImportError ให้เติม `-t .` เพราะ `tests/` เป็น package

## โครงสร้างโปรเจกต์

```
.
├── app.py                  # Flask route, เลือกโหมด, แปลงหน่วย, จัดการ error
├── dc_bias.py              # สมการทั้ง 3 โหมด (บริสุทธิ์ ไม่รู้จัก HTTP/kΩ)
├── templates/
│   └── index.html          # dropdown โหมด + input form + ผลลัพธ์ (Jinja)
├── static/
│   └── style.css           # responsive layout
├── tests/
│   ├── __init__.py
│   ├── test_dc_bias.py     # unit tests เดิมของ Divider
│   ├── test_bias_modes.py  # unit tests ของ Fixed/Emitter (ใหม่ Lab 3)
│   └── test_web.py         # Flask HTTP route tests + A1–A5
├── tools/
│   └── independent_reference.py  # ค่าอ้างอิงอิสระ Decimal 50 หลัก
├── docs/
│   ├── design-note.md
│   ├── validation.md       # ตาราง A1–A5 + หลักฐาน browser
│   ├── submission.md       # สรุปสิ่งที่ส่ง + วิธี commit/push
│   ├── evidence/
│   │   └── A2-fixed-bias.png
│   └── reflection.md
├── requirements.txt
├── AGENTS.md
└── README.md
```

## แบบจำลองทางไฟฟ้า

Forward-Active Approximation (β คงที่, VBE คงที่):

```
Fixed:    IB = (VCC − VBE) / RB
Emitter:  IB = (VCC − VBE) / [RB + (β + 1)·RE]
Divider:  VTH = VCC·R2/(R1+R2),  RTH = R1·R2/(R1+R2)
          IB  = (VTH − VBE) / [RTH + (β + 1)·RE]

ใช้ร่วมกัน: IC = β·IB,  IE = (β+1)·IB
          VE = IE·RE (Fixed ใช้ VE = 0),  VB = VE + VBE
          VC = VCC − IC·RC,  VCE = VC − VE
```

การแปลง kΩ → Ω เกิดที่ `app.py` ใน `parse_form()` จุดเดียว (1 MΩ = 1000 kΩ = 1,000,000 Ω)

### ข้อมูลทดลองอ้างอิง

ค่าที่ใช้ร่วมกัน: `VCC = 12 V, RC = 2.2 kΩ, β = 100, VBE = 0.70 V`

| กรณี | อินพุตเพิ่ม | IC | VCE |
|---|---|---|---|
| A1 Divider | R1=100 kΩ, R2=22 kΩ, RE=1 kΩ | 1.230 mA | 8.052 V |
| A2 Fixed | RB=1000 kΩ | 1.130 mA | 9.514 V |
| A3 Emitter | RB=1000 kΩ, RE=1 kΩ | 1.026 mA | 8.705 V |
| A4 Emitter | RB=1000 kΩ, RE=2 kΩ | 0.940 mA | 8.033 V |
| A5 Fixed | RB=0 | ต้องแจ้งข้อผิดพลาด | — |

ค่าอ้างอิงอิสระ (ยังไม่ปัดเศษ, `Decimal` 50 หลัก) และตาราง A1–A5 อยู่ใน `docs/validation.md`

## ตัวอย่างการใช้งาน

1. เปิด <http://127.0.0.1:5000/>
2. เลือก **โหมดวงจร** จาก dropdown (ค่าเริ่มต้นคือ Voltage Divider Bias)
3. กรอกค่าตามหน่วยบนฟอร์ม (ตัวต้านทานเป็น **kΩ** — ใต้ช่องจะแสดงค่าที่แปลงเป็น Ω ให้ตรวจ)
   - ช่อง `RB` จะโผล่เฉพาะโหมด Fixed/Emitter; `R1`/`R2` โผล่เฉพาะ Divider
4. กด **Calculate DC Bias**

ผลของ A1 (Divider ค่าเดิม):

```
Active
VTH  2.164 V      RTH 18.03 kΩ
IB  12.299 µA     IC  1.230 mA     IE  1.242 mA
VB   1.942 V      VE  1.242 V      VC  9.294 V      VCE 8.052 V
```

ผลของ A2 (Fixed, RB=1000 kΩ):

```
Fixed Bias
IB  11.300 µA     IC  1.130 mA     IE  1.141 mA
VB   0.700 V      VE  0.000 V      VC  9.514 V      VCE 9.514 V
```

### การจัดการข้อผิดพลาดและ warning

| สถานการณ์ | สิ่งที่เกิดขึ้น |
|---|---|
| กรอกค่าที่ไม่ใช่ตัวเลข (เช่น `abc`, `12,0`) | หน้าเดิม + ข้อความ `ช่องต่อไปนี้ไม่ใช่ตัวเลข…` (HTTP 200 ไม่ crash) |
| ความต้านทาน ≤ 0 | `ค่าความต้านทานต้องมากกว่า 0 Ω (พบ RB = 0 Ω)` (มี prefix `[Fixed Bias]`) |
| โหมดไม่รู้จัก | `โหมดไม่รู้จัก … — เลือก Voltage Divider, Fixed หรือ Emitter Bias` (ไม่เดาเป็น Divider) |
| กรอกไม่ครบตามโหมดที่เลือก | `กรุณากรอกตัวเลขให้ครบทุกช่อง: …` |
| `VTH ≤ VBE` หรือ IB ≤ 0 | badge `Cutoff`, กระแสทุกตัวเป็น 0, พร้อม warning |
| `VCE ≤ 0.3 V` | badge `Saturation`, พร้อม warning ว่า VCE ไม่น่าเชื่อถือ |

ข้อผิดพลาดจะแสดงในกล่องแจ้งเตือน **โดยไม่มีตารางผลลัพธ์/region badge ค้างจากรอบก่อน**

## เอกสารเพิ่มเติม

| ไฟล์ | เนื้อหา |
|---|---|
| `docs/design-note.md` | เหตุผลเบื้องหลังการออกแบบแต่ละจุด (รวม mode dispatch) |
| `docs/validation.md` | หลักฐานว่าผลตรงกับค่าอิสระ + ตาราง A1–A5 จาก browser จริง |
| `docs/submission.md` | สรุปสิ่งที่ส่ง (URL, SHA, ตาราง A1–A5, ค่าอิสระ, วิธี push) |
| `docs/reflection.md` | สิ่งที่เรียนรู้ ข้อจำกัด และคำตอบคำถามปิด Lab |
| `AGENTS.md` | กติกาการแก้โค้ด (สำหรับ AI agent และผู้ร่วมงาน) |

## ข้อจำกัด

- ผลลัพธ์ใช้ได้เฉพาะเมื่อ transistor อยู่ใน Forward-Active Region
- ถ้า IB ≤ 0 (cutoff) หรือ VCE ต่ำจนใกล้ saturation แอปต้องแสดง warning และไม่รายงานว่าแบบจำลองใช้ได้
- เกณฑ์เตือน saturation ใช้ margin 0.3 V แบบเดิมของ Lab 2 (เข้มงวดกว่า 0.2 V ที่ใบงานกล่าวถึง จึงยังเตือนในกรณีที่ใบงานต้องการ)
- ไม่ใช่ ngspice และไม่ใช่ผลจำลองเชิงพาณิชย์

## ผู้จัดทำ

B6809720 Pakpoom — ENG29 2121 (2/2569)
