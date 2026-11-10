# Design: BJT DC Bias Web App (Lab 02)

วันที่: 2026-11-10
รายวิชา: ENG29 2121 — Lab 02 (2/2569)
สถานะ: รออนุมัติจากเจ้าของโครงงาน

## 1. Intent (ทำไมต้องมีงานนี้)

นักศึกษาต้องส่ง Flask Web Application ที่คำนวณ DC Operating Point ของวงจร BJT
Common-Emitter แบบ Voltage-Divider Bias ได้จริงภายในคาบเรียน 3 ชั่วโมง
งานนี้เป็น "vertical slice" แรกของระบบ Virtual Transistor Lab ปลายภาค
จึงต้องพิสูจน์ให้ได้ว่า: ฟอร์มในเบราว์เซอร์ → Flask → Python คำนวณ → แสดงผล
ทำงานครบวงจร พร้อม tests และประวัติ Git ที่ตรวจสอบได้

## 2. Goals

- G1: เปิด `http://127.0.0.1:5000/` แล้วเห็นฟอร์มกรอกค่าได้ (HTTP 200)
- G2: POST แล้ว **Python คำนวณจริง** (ไม่ใช่ค่าคงที่ใน HTML) และแสดง VB, VE, VC, VCE, IC
  พร้อม IB, IE และหน่วยกำกับทุกค่า
- G3: ผลตรงกับการคำนวณอิสระภายใต้แบบจำลองเดียวกัน (tolerance 0.1%)
- G4: อินพุตผิด (R≤0, β≤0, VCC≤0, ไม่ใช่ตัวเลข, ว่าง) → ข้อความ error ที่อ่านเข้าใจ ไม่ crash
- G5: นอก Forward-Active (cutoff / saturation) → warning ชัดเจน ไม่รายงานว่าแบบจำลองใช้ได้
- G6: Automated tests: ≥3 tests ของ engineering logic + ≥1 test ผ่าน Flask test client
- G7: `git clone` → `pip install -r requirements.txt` → รันเว็บ → รัน tests ได้ตาม README

## 3. Non-goals

- ไม่ทำ AC small-signal, gain, Bode plot
- ไม่ทำ transient / signal generator / animation
- ไม่ทำ bias template อื่น (Fixed, Emitter bias) — สัปดาห์ถัดไป
- ไม่ทำ SPICE/ngspice solver
- ไม่ทำ circuit editor หรือ interactive schematic
- ไม่รองรับ FET
- ไม่มี database, ไม่มี user login, ไม่มี deployment ขึ้น cloud

## 4. Anti-goals (ทำงานได้แต่ถือว่าล้มเหลว)

- A1: ตัวเลขผลลัพธ์ถูก hardcode หรือคำนวณด้วย JavaScript ฝั่ง client
- A2: `index.html` ฝังสมการฟิสิกส์ไว้ (สมการต้องอยู่ใน `dc_bias.py` เท่านั้น)
- A3: แสดงผลโดยไม่มีหน่วย หรือหน่วยปนกัน (kΩ/Ω) จนตีความไม่ได้
- A4: อินพุตผิดแล้วได้ HTTP 500 หรือ stack trace บนหน้าเว็บ
- A5: แสดงผลนอก active region โดยไม่มี warning
- A6: เปิดด้วย `file://` แล้วยังทำงาน (แปลว่า logic อยู่ฝั่ง client — ผิดเจตนา)

## 5. Constraints

- Python 3.15.2 (ติดตั้งอยู่), ใช้เฉพาะ standard library + Flask
- Flask 3.1.3 (ทดสอบแล้วว่าติดตั้งได้บนเครื่องนี้)
- ใช้ `unittest` จาก stdlib (ไม่ใช้ pytest — ลดความเสี่ยง wheel บน Python 3.15)
- เวลารวมของ Lab 2 = 180 นาที (เหลือราว 100 นาทีสำหรับ build + test)
- Commit ผ่าน GitHub Desktop โดยเจ้าของโครงงาน (agent ไม่ commit แทน)
- repo: `https://github.com/B6809720Pakpoom/BJT-DC-Bias-Web-App` (public)

## 6. Approaches ที่พิจารณา

### 6.1 สถาปัตยกรรม

| ทางเลือก | ข้อดี | ข้อเสีย | คำตัดสิน |
|---|---|---|---|
| Flask + Jinja + โมดูล Python แยก | ตรงตามใบงาน, backend คำนวณจริง, test ง่าย | ต้องมี server | **เลือก** |
| HTML + JavaScript ล้วน | ไม่ต้องติดตั้งอะไร | ผิดเกณฑ์ A2/A6 (Python ต้องคำนวณ) | ตัดทิ้ง |
| FastAPI + React | ทันสมัย | เพิ่ม dependency + build step โดยไม่ได้คะแนน | ตัดทิ้ง |
| Flask + คำนวณใน route เดียว (ไม่แยกโมดูล) | โค้ดน้อยกว่า | ผิดข้อกำหนด "engineering module ไม่รู้จัก HTML" และ test ยาก | ตัดทิ้ง |

### 6.2 หน่วยของตัวต้านทาน (เจ้าของโครงงานเลือกเอง)

| ทางเลือก | หน้าตา | คำตัดสิน |
|---|---|---|
| **A: รับ kΩ** | `R1 (kΩ) [100]` → แปลง ×1000 ในชั้น HTTP | **เลือก** |
| B: รับ Ω | `R1 (Ω) [100000]` | ไม่เลือก |
| C: dropdown หน่วยต่อช่อง | เพิ่ม UI/logic/test | ไม่เลือก (เกินเวลา) |

**เหตุผล:** ข้อมูลทดลองในใบงานเป็น kΩ ทั้งชุด (100k, 22k, 2.2k, 1k) และใบงานเตือนให้
"แปลง kΩ เป็น Ω ให้สอดคล้องก่อนคำนวณ" — ทางเลือก A ทำให้การแปลงนั้นชัดเจนและมีเทสต์กำกับ
**ขอบเขตของการแปลง:** `dc_bias.py` รับ **Ω เท่านั้น** (ไม่รู้จัก kΩ) การแปลงเกิดใน `app.py`
ที่เดียว ทำให้สลับกลับไปทางเลือก B ภายหลังได้โดยแก้จุดเดียว

### 6.3 รูปแบบ route

เลือก **`GET /` แสดงฟอร์ม + `POST /` ประมวลผล** (ไม่แยก `/calculate`)
เพราะใบงานอนุญาตทั้งสองแบบ และลดจำนวน endpoint ที่ต้องดูแล/ทดสอบ

## 7. Design

### 7.1 โครงสร้างไฟล์

```
app.py                  Flask app, routes, parse form, แปลงหน่วย, เรียก dc_bias
dc_bias.py              สมการบริสุทธิ์ (SI units), dataclass ผลลัพธ์, validation วิศวกรรม
templates/index.html    ฟอร์ม + ผลลัพธ์ + error + warning (Jinja)
static/style.css        layout, สี, responsive
tests/test_dc_bias.py   unit tests ของสมการและ region
tests/test_web.py       HTTP tests ผ่าน Flask test client
requirements.txt        Flask==3.1.3
README.md               วิธีติดตั้ง/รัน/ทดสอบ (มีอยู่แล้ว, จะอัปเดตภายหลัง)
AGENTS.md               กติกาโค้ดสำหรับ AI agent
docs/design-note.md     สรุปการตัดสินใจออกแบบ
docs/validation.md      หลักฐานตรวจสอบกับค่าอ้างอิง
docs/reflection.md      สิ่งที่เรียนรู้/ข้อจำกัด
```

### 7.2 API ของ `dc_bias.py`

```python
@dataclass(frozen=True)
class DcBiasResult:
    vth: float      # V
    rth: float      # ohm
    ib: float       # A
    ic: float       # A
    ie: float       # A
    vb: float       # V
    ve: float       # V
    vc: float       # V
    vce: float      # V
    region: str            # "active" | "cutoff" | "saturation"
    warnings: tuple[str, ...]

def calculate_dc_bias(vcc, r1, r2, rc, re, beta, vbe) -> DcBiasResult:
    """รับค่าอินพุต SI (V, ohm) คืนค่า DC operating point
    raises ValueError ถ้าค่าอยู่นอกขอบเขตที่คำนวณได้"""
```

- ไม่ import Flask, ไม่รู้จัก HTML/HTTP, ไม่มี side effect
- หน่วยอินพุต: V, Ω, อัตราส่วน (β), V

### 7.3 Validation (ใน `dc_bias.py` → `ValueError`)

| เงื่อนไข | ข้อความ |
|---|---|
| `vcc <= 0` | VCC ต้องมากกว่า 0 V |
| `r1 <= 0 or r2 <= 0 or rc <= 0 or re <= 0` | ค่าความต้านทานต้องมากกว่า 0 Ω |
| `beta <= 0` | β ต้องมากกว่า 0 |
| `vbe < 0 or vbe >= vcc` | VBE ต้องอยู่ระหว่าง 0 และ VCC |
| ค่าไม่ใช่ตัวเลข / ว่าง | แจ้งที่ชั้น `app.py`: "กรุณากรอกตัวเลขให้ครบทุกช่อง" |

`app.py` แปลงข้อความเป็น float ด้วย `request.form.get(name, "").strip()` →
ถ้าแปลงไม่ได้หรือว่าง ให้รวบรวมชื่อช่องที่ผิดแล้วแสดงเป็นรายการ error (HTTP 200)

### 7.4 กติกา Region และ Warning

```
VTH = VCC·R2/(R1+R2)
RTH = R1·R2/(R1+R2)

ถ้า VTH <= VBE:                        # ลำดับที่ 1 — ชนะทุกกรณี (if)
    region = "cutoff"
    IB = IC = IE = 0
    VE = 0 ,  VB = VTH ,  VC = VCC ,  VCE = VCC - VTH
    warning: "VTH (… V) ≤ VBE (… V) → ทรานซิสเตอร์อยู่ใน cutoff
              แบบจำลอง forward-active ใช้ไม่ได้ กระแสทุกตัวเป็นศูนย์"

ถ้าไม่ใช่ cutoff:                       # ลำดับที่ 2 (elif)
    IB  = (VTH - VBE) / (RTH + (β+1)·RE)
    IC  = β·IB ,  IE = (β+1)·IB
    VE  = IE·RE ,  VB = VE + VBE ,  VC = VCC - IC·RC ,  VCE = VC - VE

    ถ้า VCE <= 0.3 V:
        region = "saturation"
        warning: "VCE (… V) ≤ 0.3 V → ใกล้/อยู่ใน saturation
                  ค่า VCE ที่คำนวณได้ไม่น่าเชื่อถือ"
    ไม่อย่างนั้น:
        region = "active"
```

- **Precedence:** cutoff ถูกตรวจก่อนและเป็น `if` / saturation เป็น `elif`
  → สอง warning ไม่เกิดพร้อมกัน, region มีค่าเดียวเสมอ
- **ค่าใน cutoff ถูก clamp ที่ศูนย์** ไม่แสดงกระแสติดลบหรือ VC > VCC
  เพราะค่าติดลบเป็นผลของสมการ forward-active ที่ไม่ควรใช้ ไม่ใช่ฟิสิกส์จริง
- **ค่าใน saturation แสดงค่าที่คำนวณได้ตามจริง** (อาจติดลบได้) พร้อม warning
  เพราะกระแสยังไหลจริงและตัวเลขติดลบคืออาการที่บอกว่าแบบจำลองเพี้ยน
- ทุกกรณีที่ region != "active" ต้องมี warning อย่างน้อย 1 ข้อความ
- Warning ต้องไม่รายงานว่า "ผลจำลองแม่นยำ"

### 7.5 การแสดงผล

- ค่าคงที่ภายในใช้ float เต็มความละเอียด **ปัดเฉพาะตอนแสดงผล** ตามหน่วยต่อปริมาณ:
  - แรงดัน (VTH, VB, VE, VC, VCE): 3 ตำแหน่งทศนิยม หน่วย **V**
  - IC, IE: 3 ตำแหน่งทศนิยม หน่วย **mA**
  - IB: 3 ตำแหน่งทศนิยม หน่วย **µA** (เพราะ IB ~ 12 µA ถ้าออกเป็น mA จะได้ 0.012 ซึ่งอ่านยากและไม่ตรงตารางใบงาน)
  - RTH: 2 ตำแหน่งทศนิยม หน่วย **kΩ**
  - ไม่ใช้ auto-scaling ตามขนาด — ตรึงหน่วยต่อปริมาณเพื่อให้เทียบกับใบงานได้ตรง
- ฟอร์ม: `VCC (V)`, `R1 (kΩ)`, `R2 (kΩ)`, `RC (kΩ)`, `RE (kΩ)`, `β`, `VBE (V)`
- ค่าเริ่มต้นในฟอร์ม = ข้อมูลทดลองของใบงาน (12, 100, 22, 2.2, 1, 100, 0.70)
- ใต้ช่องตัวต้านทานแสดงค่าที่แปลงแล้ว เช่น `= 100,000 Ω` เพื่อให้ตรวจสอบได้
- แสดง region เป็น badge: Active (เขียว) / Cutoff (เทา) / Saturation (ส้ม)
- ผลลัพธ์แสดงเป็นตาราง: VTH, RTH, IB, IC, IE, VB, VE, VC, VCE

### 7.6 Tests

`tests/test_dc_bias.py` (อย่างน้อย 6 tests)
1. กรณีอ้างอิงใบงาน → VTH, RTH, IB, IC, IE, VB, VE, VC, VCE ตรงค่าความละเอียดเต็ม
   (tolerance relative 1e-9) — ตัวเลข oracle มาจากการคำนวณมือ+สคริปต์อิสระ ไม่ใช่ตาราง §8 ที่ปัดแล้ว
2. กรณี cutoff (VTH ≤ VBE) → region == "cutoff", IB==IC==IE==0, VC==VCC, VCE==VCC−VTH และมี warning
3. กรณี saturation (RC สูงมากจน VCE ≤ 0.3) → region == "saturation" และมี warning
4. `beta <= 0` → `ValueError`
5. `r1 <= 0` → `ValueError`
6. `vcc <= 0` → `ValueError`

`tests/test_web.py` (อย่างน้อย 4 tests)
1. `GET /` → 200 และมี `name="vcc"` ในหน้า
2. `POST /` ด้วยค่าอ้างอิง → 200 และหน้าผลลัพธ์มี `8.052` (VCE)
3. `POST /` ด้วย `r1=0` → 200, มีข้อความ error, ไม่มี stack trace
4. `POST /` ด้วย `vcc=abc` → 200, มีข้อความ error

### 7.7 ลำดับการทำงาน (vertical slices)

1. `dc_bias.py` + `tests/test_dc_bias.py` → รัน tests เขียว
2. `app.py` (GET/POST) + `templates/index.html` แบบเรียบ → เปิด browser เห็นผล
3. `static/style.css` → ตกแต่ง
4. `tests/test_web.py` → รัน tests เขียว
5. `docs/*.md` + อัปเดต README + `requirements.txt` + `AGENTS.md`

## 8. ค่าอ้างอิงสำหรับตรวจสอบ (A3)

`VCC=12 V, R1=100 kΩ, R2=22 kΩ, RC=2.2 kΩ, RE=1 kΩ, β=100, VBE=0.70 V`

| VTH | RTH | IB | IC | IE | VE | VB | VC | VCE |
|---|---|---|---|---|---|---|---|---|
| 2.164 V | 18.03 kΩ | 12.30 µA | 1.230 mA | 1.242 mA | 1.242 V | 1.942 V | 9.294 V | 8.052 V |

> ตารางนี้ **ปัดเพื่อการแสดงผล** ใช้ตรวจด้วยตา ไม่ใช่ oracle ของเทสต์
> oracle ที่ความละเอียดเต็มอยู่ในหัวข้อ 10.3

## 9. สิ่งที่เหลือให้ผู้สร้างตัดสินใจเอง

- ภาษาของข้อความ UI (ไทย/อังกฤษ/ผสม) และถ้อยคำของ warning
- โทนสี/ฟอนต์/ระยะห่างของ CSS
- จะแยก helper `parse_form()` ใน `app.py` หรือเขียนใน route ตรง ๆ
- จะแสดง IB/IE ในตารางเดียวกับค่าหลัก หรือแยกส่วน "Secondary values"
- ชื่อ commit และการแบ่งจำนวน commit

## 10. การตัดสินใจที่ปิดช่องว่างหลัง builder check

ผู้ตรวจ (builder check) ทัก 4 จุดที่กำกวม จุดละการตัดสินใจและเหตุผล:

### 10.1 ค่าใน cutoff: clamp ที่ศูนย์ (ไม่ใช่ค่าติดลบจากสมการ)

ถ้าใช้สมการ forward-active ต่อใน cutoff จะได้ IB, IC, IE ติดลบ, VE ติดลบ,
VB < VBE และ VC > VCC ซึ่งไม่มีความหมายทางฟิสิกส์ — เป็นอาการว่าแบบจำลองถูกใช้นอกขอบเขต
จึงรายงาน **IB = IC = IE = 0, VE = 0, VB = VTH, VC = VCC, VCE = VCC − VTH**
พร้อม warning ระบุว่าเป็น cutoff และแบบจำลองใช้ไม่ได้
ส่วน **saturation ยังรายงานค่าที่คำนวณได้ตามจริง** เพราะกระแสยังไหลและตัวเลขคือหลักฐานว่าแบบจำลองเพี้ยน

### 10.2 หน่วยต่อปริมาณ (ไม่ใช้ mA กับทุกกระแส)

IB อยู่ในระดับ µA ถ้าบังคับหน่วย mA จะได้ `0.012 mA` ซึ่งอ่านยากและไม่ตรงตารางใบงาน
จึงตรึงหน่วย: **IB = µA, IC/IE = mA, แรงดัน = V, RTH = kΩ** ทศนิยม 3 ตำแหน่ง (RTH 2 ตำแหน่ง)

### 10.3 Oracle และ tolerance ของเทสต์

- oracle = ค่าความละเอียดเต็มที่คำนวณแยกอิสระ (มือ + สคริปต์) ไม่ใช่ตารางที่ปัดแล้ว
- tolerance = relative **1e-9** (เข้มกว่าที่ต้องการมาก แต่กันการเผลอใช้ค่าปัด)
- การแสดงผลตรวจแยกใน `test_web.py` ด้วยสตริงที่ปัดแล้ว เช่น `8.052`, `1.230`, `12.299`

ค่าอ้างอิงความละเอียดเต็ม (VCC=12, R1=100k, R2=22k, RC=2.2k, RE=1k, β=100, VBE=0.70):

```
VTH = 2.1639344262295084 V      RTH = 18032.786885245903 ohm
IB  = 1.2298581462608458e-05 A  IC  = 0.0012298581462608458 A
IE  = 0.0012421567277234543 A   VE  = 1.2421567277234544 V
VB  = 1.9421567277234544 V      VC  = 9.29431207822614 V
VCE = 8.052155350502685 V
```

### 10.4 ลำดับการตรวจ region

cutoff เป็น `if` ตัวแรก, saturation เป็น `elif` → ไม่มีกรณีที่ติดทั้งสองป้าย
และ region มีค่าเดียวเสมอ (กรณี VCC ต่ำมากถูกจับเป็น cutoff ก่อน ซึ่งถูกต้องทางกายภาพ)
