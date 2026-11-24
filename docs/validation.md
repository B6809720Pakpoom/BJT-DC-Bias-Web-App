# Validation — BJT DC Bias Web App

เอกสารนี้บันทึกหลักฐานว่าผลคำนวณของโปรแกรมตรงกับค่าที่คำนวณได้อย่างอิสระ (Acceptance A3)

## 1. อินพุตอ้างอิง

| พารามิเตอร์ | ค่า |
|---|---|
| VCC | 12 V |
| R1 | 100 kΩ (100 000 Ω) |
| R2 | 22 kΩ (22 000 Ω) |
| RC | 2.2 kΩ (2 200 Ω) |
| RE | 1 kΩ (1 000 Ω) |
| β (hFE) | 100 |
| VBE | 0.70 V |

## 2. วิธีคำนวณอิสระ

### 2.1 คำนวณมือ (Thevenin + KVL)

```
VTH = 12 × 22 / (100 + 22)            = 264 / 122      = 2.163934426 V
RTH = (100 × 22) / (100 + 22) kΩ      = 2200 / 122 kΩ  = 18.032786885 kΩ
IB  = (2.163934426 − 0.70) / (18 032.786885 + 101 × 1 000)
    = 1.463934426 / 119 032.786885    = 1.229858146e−5 A
IC  = 100 × IB                        = 1.229858146e−3 A
IE  = 101 × IB                        = 1.242156728e−3 A
VE  = 1.242156728e−3 × 1 000          = 1.242156728 V
VB  = 1.242156728 + 0.70              = 1.942156728 V
VC  = 12 − 1.229858146e−3 × 2 200     = 9.294312078 V
VCE = 9.294312078 − 1.242156728       = 8.052155350 V
```

### 2.2 สคริปต์อิสระ (Decimal 50 หลัก, จัดสมการต่างจากโปรแกรม)

ใช้ `IE` เป็นตัวตั้งแทน `IB` เพื่อไม่ให้ซ้ำเส้นทางการคำนวณของ `dc_bias.py`:

```
IE  = (VTH − VBE) / (RTH / (β + 1) + RE)
IB  = IE / (β + 1)
IC  = β × IB
```

คำนวณด้วย `decimal.Decimal` ที่ `getcontext().prec = 50` (ไม่มีความคลาดเคลื่อน floating point)
แล้วเทียบกับผลของ `dc_bias.calculate_dc_bias()` ด้วย relative difference

## 3. ผลการเทียบ (ค่าความละเอียดเต็ม)

| ปริมาณ | อิสระ (50 หลัก) | `dc_bias.py` (float) | relative diff |
|---|---|---|---|
| VTH (V) | 2.1639344262295081967 | 2.1639344262295084 | 9.4e−17 |
| RTH (Ω) | 18032.786885245901639 | 18032.786885245903 | 7.5e−17 |
| IB (A) | 1.2298581462608456e−5 | 1.2298581462608458e−05 | 1.5e−16 |
| IC (A) | 1.2298581462608456e−3 | 0.0012298581462608458 | 1.5e−16 |
| IE (A) | 1.2421567277234541e−3 | 0.0012421567277234543 | 1.9e−16 |
| VE (V) | 1.2421567277234541 | 1.2421567277234544 | 2.7e−16 |
| VB (V) | 1.9421567277234541 | 1.9421567277234544 | 1.7e−16 |
| VC (V) | 9.2943120782261397 | 9.29431207822614 | 3.8e−17 |
| VCE (V) | 8.0521553505026856 | 8.052155350502685 | 7.2e−17 |

**สรุป:** relative difference สูงสุด = **2.659e−16** ซึ่งอยู่ในระดับ machine epsilon ของ IEEE-754 double
จึงสรุปได้ว่าตรงกับค่าอิสระภายใน **0.1 %** ตามที่กำหนด (จริง ๆ ตรงถึง ~1e−16)

## 4. ค่าที่หน้าเว็บแสดง (หลังปัดตามหน่วย)

| ปริมาณ | หน่วย | ค่าที่แสดง |
|---|---|---|
| VTH | V | 2.164 |
| RTH | kΩ | 18.03 |
| IB | µA | 12.299 |
| IC | mA | 1.230 |
| IE | mA | 1.242 |
| VB | V | 1.942 |
| VE | V | 1.242 |
| VC | V | 9.294 |
| VCE | V | 8.052 |
| region | — | Active |

ค่าปัดเหล่านี้ถูกตรวจใน `tests/test_web.py` (`8.052`, `1.230`, `12.299`, `Active`)

## 5. กรณีบอกข้อยกเว้น (นอก forward-active)

| กรณี | อินพุตที่เปลี่ยน | ผล |
|---|---|---|
| Cutoff | R2 = 5 kΩ → VTH = 0.571 V ≤ VBE | region = `cutoff`, IB = IC = IE = 0, VE = 0, VC = 12.000 V, VCE = 12.000 V, มี warning |
| Saturation | RC = 15 kΩ → VCE = −7.690 V ≤ 0.3 V | region = `saturation`, มี warning ว่า VCE ไม่น่าเชื่อถือ |

> ใน cutoff กระแสเป็นศูนย์ จึงไม่มีแรงดันตกคร่อม RC หรือ RE → VC = VCC และ VCE = VC − VE = VCC = 12.000 V
> (ตารางผลลัพธ์จึงสอดคล้องกันเอง: 12.000 − 0.000 = 12.000)

ข้อความ warning ที่โปรแกรมสร้างจริง:

```
VTH (0.571 V) ≤ VBE (0.700 V) → ทรานซิสเตอร์อยู่ใน cutoff แบบจำลอง forward-active ใช้ไม่ได้ กระแสทุกตัวเป็นศูนย์
VCE (-7.690 V) ≤ 0.3 V → ใกล้/อยู่ใน saturation ค่า VCE ที่คำนวณได้ไม่น่าเชื่อถือ
```

## 6. การตรวจสอบอินพุตผิด

| อินพุต | ผลที่หน้าเว็บ |
|---|---|
| R1 = 0 | `ค่าความต้านทานต้องมากกว่า 0 Ω (พบ R1 = 0 Ω)` (HTTP 200, ไม่มี traceback) |
| VCC = `abc` | `ช่องต่อไปนี้ไม่ใช่ตัวเลข: vcc ("abc")` |
| R1 = `12,0` | ข้อความเดิม (คอมมาไม่ถือเป็นจุดทศนิยม) |
| หลายช่องผิดพร้อมกัน | รายงาน **ทุกช่อง** ในข้อความเดียว |
| ช่องว่าง | `กรุณากรอกตัวเลขให้ครบทุกช่อง: <ชื่อช่อง>` |
| VCC = `nan` / β = `inf` | `ค่าต้องเป็นจำนวนจำกัด (finite): …` และ **ไม่แสดง** badge Active |
| R1 = `1e308` (ล้นเป็น `inf` หลัง ×1000) | `ค่าต้องเป็นจำนวนจำกัด (finite): r1 (1e308)` |
| อินพุตจำกัดแต่ผลลัพธ์ล้น | `ผลลัพธ์ล้นช่วงตัวเลข (…) — กรุณาลดขนาดค่าอินพุต` |

ทั้งสามกรณีแรกเป็น HTTP 200 พร้อมหน้าเว็บปกติ (ไม่มี 500, ไม่มี stack trace)

## 7. วิธีรันซ้ำ

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

ผลที่คาด: `Ran 33 tests ... OK` (tolerance ของเทสต์คือ relative 1e−9 เทียบกับค่าความละเอียดเต็ม)

## 8. หมายเหตุ: ตัวเลขในภาพตัวอย่างของใบงานไม่ตรงกับผลของโปรแกรม

ใบงาน §01B ระบุไว้เองว่า

> "ค่าตัวเลขบนหน้าจอเป็นค่าประกอบภาพ ไม่ใช่คำตอบอ้างอิงหรือผลการจำลองที่ตรวจสอบแล้ว"

ภาพตัวอย่างใช้ข้อมูลอินพุตชุดเดียวกับเรา (12 V, 100 kΩ, 22 kΩ, 2.2 kΩ, 1 kΩ, β=100, VBE=0.70)
แต่ตัวเลขไม่ตรงกัน ดังนี้

| ค่า | ภาพตัวอย่าง | โปรแกรมนี้ | คำนวณมือ (§06) |
|---|---|---|---|
| VB | 2.20 V | **1.942 V** | 1.942 V |
| VE | 1.50 V | **1.242 V** | 1.242 V |
| VC | 8.70 V | **9.294 V** | 9.294 V |
| VCE | 7.20 V | **8.052 V** | 8.052 V |
| IB | 15.1 µA | **12.299 µA** | 12.299 µA |
| IC | 1.50 mA | **1.230 mA** | 1.230 mA |
| IE | 1.51 mA | **1.242 mA** | 1.242 mA |

### สาเหตุของความต่าง

ภาพตัวอย่างคำนวณโดย **ตัด `RTH` ทิ้ง** (สมมติว่าตัวแบ่งแรงดัน stiff จนกระแสเบสไม่มีผล) และปัด `VTH` เป็น 2.2 V:

```
สูตรใบงาน §06:  IB = (VTH − VBE) / (RTH + (β+1)·RE)   → 12.299 µA   ← โปรแกรมนี้
สูตรที่ได้จากภาพ: IB = (VTH − VBE) / ((β+1)·RE)         → 14.851 µA   → IC ≈ 1.485 mA
```

`RTH = 18.03 kΩ` คิดเป็น **15 %** ของตัวส่วน `119.03 kΩ` การตัดทิ้งจึงทำให้ IB พองขึ้น 15 %
และลากค่าอื่นทั้งชุดตามไป (1.230 → ~1.45 mA) ตัวเลขในภาพยังสอดคล้องกันเอง
(8.70 − 1.50 = 7.20) แปลว่าคำนวณจากสมการคนละแบบ ไม่ใช่การพิมพ์ผิด

### ข้อสรุป

โปรแกรมนี้ยึดสมการตามใบงาน §06 ครบทุกพจน์ จึงให้ 1.230 mA และ VCE 8.052 V
ซึ่งตรงกับ `docs/validation.md` §2–§3 ที่คำนวณแยกอิสระสองวิธี (มือ + Decimal 50 หลัก)
การแก้ให้ตรงภาพจะทำให้ขัดกับสมการที่ใบงานกำหนด จึงไม่แก้

---

# Lab 03 — เพิ่ม Fixed Bias / Emitter Bias และตรวจผลผ่าน Browser

## 9. เครื่องมือที่ใช้ตรวจผลจริง

| รายการ | สถานะ | หลักฐาน |
|---|---|---|
| Playwright MCP | **NOT RUN** | ตรวจแล้วไม่มี `node`/`npx` ในเครื่อง, ไม่มี `opencode.json` หรือ `opencode.jsonc` ที่รากโปรเจกต์ และไม่มี MCP ชื่อ `playwright` เชื่อมต่อใน session นี้ จึงไม่สามารถรันตาม Section 05 ของใบงานได้ |
| OpenCode Browser (วิธีที่ใช้แทน) | **USED** | ใช้ `tools.browser.*` (`navigate`, `snapshot`, `select`, `fill`, `click`, `evaluate`, `screenshot`) เปิด `http://127.0.0.1:5000/` แล้วกรอก/กดปุ่มจริง ทุกกรณีเห็น HTTP `POST http://127.0.0.1:5000/` ใน network log |
| Manual (ทวนเอง) | **USED** | เปิดเว็บซ้ำกรณี A2 ด้วยตนเองอีก 1 รอบ ผลตรงเดิม |

เหตุผลที่เลือกใช้ OpenCode Browser ตามที่ใบงาน Section 05 อนุญาต: "ถ้าเครื่องของกลุ่มใช้ Playwright MCP ไม่ได้ภายในช่วงทดสอบ ให้บันทึก Playwright MCP เป็น `NOT RUN` พร้อมเหตุผล แล้วใช้ Browser Tool ที่มีใน OpenCode Desktop … ใช้กรณี A1–A5 และเกณฑ์ให้คะแนนเดียวกัน แต่ระบุวิธีจริง"

## 10. เครื่องมือและขั้นตอนที่ใช้ตรวจ (ชื่อจริง)

- `browser.navigate` เปิด URL, `browser.snapshot` อ่านโครงสร้างหน้า (ชื่อช่อง/ปุ่ม/ผล)
- `browser.select` เลือกโหมด, `browser.fill` กรอกค่า, `browser.click` กด **Calculate DC Bias**
- `browser.evaluate` อ่านข้อความที่ render จริงจาก DOM (ไม่ได้อ่านโค้ดหรือใช้ `curl` แทน)
- `browser.screenshot` เก็บภาพหน้าเว็บ → `docs/evidence/A2-fixed-bias.png`
- หลังส่งฟอร์มทุกครั้งอ่าน snapshot ใหม่เสมอ เพื่อไม่ให้ใช้ผลรอบก่อน

## 11. ค่าคาดหมายอิสระก่อนรัน (ห้ามใช้ผลจากโค้ดที่กำลังตรวจ)

ค่าที่ใช้ร่วมกันใน A1–A5: `VCC = 12 V, RC = 2.2 kΩ, β = 100, VBE = 0.70 V`
เกณฑ์: `|ΔIC| ≤ 0.01 mA`, `|ΔVCE| ≤ 0.02 V` เทียบกับค่าที่ **ยังไม่ปัดเศษ**

สคริปต์ `tools/independent_reference.py` ใช้ `decimal.Decimal` ความละเอียด 50 หลัก,
ตั้ง `IE` เป็นตัวตั้งแทน `IB` และ **ไม่ import `dc_bias`/`app`** จึงเป็นเส้นทางอิสระ:

```
A1 Divider  (R1=100k, R2=22k, RE=1k): IC = 1.229858146 mA, VCE = 8.052155351 V
A2 Fixed    (RB=1M):                  IC = 1.130000000 mA, VCE = 9.514000000 V
A3 Emitter  (RB=1M, RE=1k):           IC = 1.026339691 mA, VCE = 8.705449591 V
A4 Emitter  (RB=1M, RE=2k):           IC = 0.940099834 mA, VCE = 8.032778702 V
A5 Fixed    (RB=0):                   RB ต้อง > 0 Ω → ต้องแจ้งข้อผิดพลาด
```

รันซ้ำได้ด้วย `.\.venv\Scripts\python.exe tools\independent_reference.py`

## 12. ตารางผลจริง A1–A5

| กรณี | โหมด/อินพุตที่กรอกจริง | คาดหมายก่อนรัน | เห็นจริงบนหน้าเว็บ | วิธีตรวจ | สถานะ |
|---|---|---|---|---|---|
| **A1 · โหมดเดิม** | Divider · `R1=100, R2=22, RE=1` kΩ (VCC/RC/β/VBE ใช้ค่าร่วมกัน) | ตรงกับผลก่อนแก้ Lab 2 และค่าอิสระ `IC=1.229858146 mA, VCE=8.052155351 V` | `IC = 1.230 mA`, `VCE = 8.052 V`, `IB = 12.299 µA`, `VTH = 2.164 V`, `RTH = 18.03 kΩ`, badge **Active**, หัวข้อ "Voltage Divider Bias" | OpenCode Browser | **PASS** (ΔIC=0.000142 mA, ΔVCE=0.000155 V) |
| **A2 · Fixed** | Fixed · `RB=1000` kΩ (=1 MΩ); **ไม่กรอก RE/R1/R2** | ไม่ต้องใช้ RE → `IC=1.130000000 mA, VCE=9.514000000 V` | `IC = 1.130 mA`, `VCE = 9.514 V`, `IB = 11.300 µA`, `VE = 0.000 V`, `= 1,000,000 Ω`, หัวข้อ "Fixed Bias", ไม่มีแถว VTH/RTH | OpenCode Browser + ทวนซ้ำด้วย Manual | **PASS** (ΔIC=0, ΔVCE=0) |
| **A3 · Emitter** | Emitter · `RB=1000` kΩ, `RE=1` kΩ | มีช่อง RE และใช้ค่า RE → `IC=1.026339691 mA, VCE=8.705449591 V` | `IC = 1.026 mA`, `VCE = 8.705 V`, `IE = 1.037 mA`, `= 1,000 Ω`, หัวข้อ "Emitter Bias" | OpenCode Browser | **PASS** (ΔIC=0.000340 mA, ΔVCE=0.000450 V) |
| **A4 · เปลี่ยนค่าเดียว** | Emitter · เหมือน A3 ทุกอย่าง เปลี่ยน**เฉพาะ `RE` เป็น 2 kΩ** | ทำนายก่อนรัน: **IC ต้องลด** เพราะตัวส่วน `RB + (β+1)RE` เพิ่มขึ้น → คาด ~`0.940 mA` | `IC = 0.940 mA` (ลดจาก 1.026), `VCE = 8.033 V`, `= 2,000 Ω` ตรงอิสระ `0.940099834 mA / 8.032778702 V` | OpenCode Browser | **PASS** (ΔIC=0.000100 mA, ΔVCE=0.000221 V) |
| **A5 · อินพุตผิด** | Fixed · `RB=0` | มีข้อความให้แก้ RB, เว็บไม่ล่ม, ไม่โชว์ผลของ A4 เป็นผลรอบนี้ | ข้อความจริง: `ไม่สามารถคำนวณได้` / `[Fixed Bias] ค่าความต้านทานต้องมากกว่า 0 Ω (พบ RB = 0 Ω)`; ไม่มี `.results`, ไม่มี region badge; ฟอร์มยังเก็บ `RB=0`; HTTP 200 ไม่มี traceback | OpenCode Browser | **PASS** |

ข้อความ A5 มาจาก **Flask/backend** (prefix `[Fixed Bias]` จาก `MODE_LABELS` ใน `app.py`,
ข้อความจาก `_validate_resistors()` ใน `dc_bias.py`) ไม่ใช่การที่ HTML ปฏิเสธการส่งฟอร์ม
— network log มี `POST` จริง

## 13. หลักฐานจากหน้าเว็บ

ข้อความที่คัดจาก snapshot ของ A2 (รอบทวนซ้ำ):

```
ผลลัพธ์ DC Bias — Fixed Bias
IB 11.300 µA | IC 1.130 mA | IE 1.141 mA
VB 0.700 V   | VE 0.000 V  | VC 9.514 V | VCE 9.514 V
```

ภาพหน้าจอ full-page จาก OpenCode Browser: `docs/evidence/A2-fixed-bias.png`

## 14. ไล่เส้นทางข้อมูล A4 (RE → สมการ)

```
templates/index.html  <input name="re"> ค่า "2" (kΩ)
   ↓ POST
app.py                mode = "emitter" → MODE_FIELDS["emitter"] = COMMON + ("rb","re")
   ↓ parse_form()     re: 2 × 1000 = 2000.0 Ω   ← จุดแปลงหน่วยเดียว
   ↓ CALCULATORS["emitter"] = calculate_emitter_bias
dc_bias.py            ib = (12 − 0.70) / (1e6 + 101×2000)
                      ic = 100×ib, ve = 101×ib×2000, vc = 12 − ic×2200, vce = vc − ve
   ↓ describe()       ปัดเฉพาะตอนแสดง: IC 0.940 mA, VCE 8.033 V
templates/index.html  ตารางผล + ป้าย "Emitter Bias"
```

## 15. ผลการรันเทสต์ (TDD ตาม `AGENTS.md`)

- ก่อนแก้: `Ran 33 tests ... OK` (baseline Lab 2)
- เขียนเทสต์ใหม่แล้วรันก่อนแก้โค้ด (RED): `Ran 43 tests ... FAILED (failures=8, errors=1)`
- หลังแก้ (GREEN): `Ran 52 tests ... OK` (33 เดิม + 19 ใหม่)
- รอบสุดท้ายหลังอัปเดตเอกสาร: ดูผลใน Section 16

## 16. คำสั่งรันซ้ำและผลรอบสุดท้าย

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
.\.venv\Scripts\python.exe tools\independent_reference.py
```

ผลที่ได้จริงรอบสุดท้าย (หลังอัปเดตเอกสาร):

```
Ran 52 tests in 0.047s

OK
```

สคริปต์อิสระคืนค่าตาม Section 11 ทุกกรณี (A5 แจ้งว่า RB ต้อง > 0 Ω)

## 17. สิ่งที่ต้องส่งเพิ่มโดยเจ้าของโปรเจกต์

- Commit และ Push เองผ่าน GitHub Desktop (ตาม `AGENTS.md` ข้อ 9 ห้าม AI commit/push)
- นำ **Commit SHA** หลัง push ไปกรอกใน `README.md` และแนบลิงก์ GitHub
- ก่อน commit ให้ตรวจ `git diff` และ `git diff --staged` ว่ไม่มี `.venv`, `.env` หรือ credentials

---

# Lab 04 — BJT CE Amplifier Simulator ด้วย ngspice

## 18. สภาพแวดล้อมจริงที่ใช้

| รายการ | ค่าที่ตรวจได้จริง |
|---|---|
| Repo | `git clone https://github.com/B6809720Pakpoom/BJT-DC-Bias-Web-App.git` (clone ใหม่จริง แล้วเอา `.git` มาแทน working tree เดิม งานค้างไม่หาย) |
| Branch | `lab04-ngspice` → tracking `origin/lab04-ngspice` (branch นี้ publish แล้ว) |
| Python | 3.15.2 |
| Flask | 3.1.3 ใน `.venv` |
| ngspice | **ngspice-47** (build 11 Aug 2026), `ngspice_con.exe` โหมด batch |
| ตำแหน่ง engine | `C:\Users\B6809720\AppData\Local\Programs\ngspice-47\Spice64\bin\` |
| วิธีติดตั้ง | โหลด `ngspice-47_64.7z` จาก SourceForge แล้วแตกด้วย 7-Zip (winget ไม่มี package นี้) |

## 19. BJT model ที่ใช้ (ต้องระบุเพราะไม่มี Starter Kit จากอาจารย์)

```
.model QNPN NPN(IS=2e-15 BF=100 VAF=0 CJE=10p CJC=5p TF=0.3n)
```

- `BF=100`, `VAF=0` → ตรงกับสมมติฐาน Lab 3 (β คงที่, ไม่มี Early effect)
- `IS=2e-15` → ทำให้ VBE ≈ 0.70 V ที่กระแส-around-1 mA
- `CJE/CJC/TF` → ทำให้ `.ac` มีความถี่ตัดจริง (ไม่ใช่กราฟเส้นตรงที่แต่งขึ้น)
- model นี้ถูกเขียนลง netlist ทุกครั้ง และแสดงในหน้าเว็บช่อง **Model:** เสมอ
- เจ้าของโปรเจกต์อนุมัติให้ใช้ model ที่กำหนดเองแทน Starter Kit ของอาจารย์แล้ว

## 20. เครื่องมือตรวจ B1–B8

| เครื่องมือ | สถานะ | เหตุผล/หลักฐาน |
|---|---|---|
| Playwright MCP | **NOT RUN** | ไม่มี MCP ชื่อ `playwright` เชื่อมต่อใน session นี้ (ตรวจแล้วเช่นเดียวกับ Lab 3) |
| Superpowers skill | **NOT RUN** | ไม่มี skill/channel ชื่อ `superpowers` ใน session นี้ (available มีแค่ `browser`, `opencode`, `report`) → ใช้ integration plan → รอเจ้าของโปรเจกต์อนุมัติ → implement → verify แทน ตามเจตนาข้อ 07 |
| OpenCode Browser | **USED** | `tools.browser.*` (`navigate`, `snapshot`, `select`, `fill`, `evaluate`, `requestSubmit()` ผ่าน JS จริง) กดฟอร์มที่ `http://127.0.0.1:5000/` และอ่าน DOM ที่ render จริง |
| Chrome headless | **USED (เฉพาะ screenshot)** | `chrome.exe --headless=new --screenshot=...` โหลดหน้าเว็บจริงผ่านฟอร์มที่ auto-POST ไปยัง Flask → ได้ภาพ `captures/*.png`; **ไม่ได้อ้างว่าเป็น Playwright MCP** |
| Impeccable | **NOT RUN** | ไม่มี skill/channel ชื่อ Impeccable และเครื่องไม่มี `node`/`npx` (`npx impeccable install` ทำไม่ได้) → ปรับ UI ด้วย CSS ทั่วไปแทนและระบุตรง ๆ ที่นี่ |
| ngspice CLI | **USED** | `ngspice_con.exe -b -o run.log -r run.raw circuit.cir` ทุก analysis |

## 21. ตารางผล B1–B8 (ค่าที่เห็นจริง)

| เกณฑ์ตามใบงาน | สิ่งที่ทำจริง | ผลที่เห็น | สถานะ |
|---|---|---|---|
| **B1 · Regression** | รัน `unittest discover` + กรอก A1–A5 ซ้ำหลังเพิ่ม SPICE | `Ran 65 tests ... OK`; A1 `IC 1.230 mA / VCE 8.052 V`, A2 `1.130 / 9.514`, A3 `1.026 / 8.705`, A4 `0.940 / 8.033`, A5 แจ้ง error ไม่มีตารางผล | PASS |
| **B2 · DC SPICE** | เลือก `SPICE DC · .op` ด้วยค่าเดิม 12 V / 100 kΩ / 22 kΩ / 2.2 kΩ / 1 kΩ | `VB 1.942 V, VE 1.240 V, VC 9.298 V, VCE 8.058 V, IC 1.228 mA`; badge `success`, `Engine: ngspice · ngspice-47`, `Model: QNPN NPN(...)`; analytical `1.230 mA / 8.052 V` อยู่คนละหัวข้อ → ΔIC 0.002 mA, ΔVCE 0.006 V | PASS |
| **B3 · Change RE** | เปลี่ยนเฉพาะ `RE` 1→2 kΩ แล้วรัน DC และ AC ซ้ำ | DC: `VB 1.942→2.043 V`, `VCE 8.058→9.166 V`, `IC 1.228→0.671 mA`; AC: peak `4.86→−0.96 dB`; netlist เปลี่ยนเป็น `RE EMIT 0 2000` — ไม่ใช่ค่าค้าง | PASS |
| **B4 · AC Bode** | รัน `SPICE AC · .ac`, อ่าน gain + phase + cutoff | 121 points, 10–10 000 000 Hz, peak `4.86 dB @10 kHz`, `Phase at peak 180.0 degree`; `Lower/Upper cutoff (-3 dB) = not determined in sweep range` (ไม่มีจุดตัดจริงในช่วง sweep → ไม่แต่งตัวเลข); มี 2 กราฟ: Gain (dB) และ Phase (degree) | PASS |
| **B5 · Transient** | รัน `SPICE Transient · .tran` ที่ **10 mV peak, 1 kHz** | `Vin amplitude (fit) 10.0 mV peak`, `Vout min −0.017 V`, `Vout max 0.017 V`, `|Vout/Vin| 1.75 V/V`, `Phase Vout vs Vin −179.9 degree` → `inverted (≈180°)`; กราฟ 504 points มี 2 เส้น Vout/Vin พร้อมแกน Time (ms) / Voltage (V) | PASS |
| **B6 · Change Source** | เปลี่ยน amplitude `0.01→0.03 V` และ frequency `1→2 kHz` แล้วรันซ้ำ | `Vout max 0.017→0.052 V`, `Simulation time 5.000→2.500 ms`, netlist `SIN(0 0.03 2000)` — waveform เปลี่ยนตาม input จริง | PASS |
| **B7 · Invalid / Fail** | กรอก `RE = 0` ใน SPICE DC (และ `R1 = 0` ทวนซ้ำ) | ข้อความจริง `[SPICE DC] ค่าความต้านทานต้องมากกว่า 0 Ω (พบ RE = 0 Ω)`; ไม่มี `.spice-results`, ไม่มี `<polyline>`, ไม่มี `status-success` | PASS |
| **B8 · UI Desktop/Mobile** | เปิดหน้า AC จริงที่ 1280×2200 และ 500×2600 (Chromium headless ต่ำสุด 500 CSS px → media query `max-width:640px` ทำงาน; ตรวจ `grid-template-columns` ได้ `1fr`) | ปุ่ม/ช่อง/หน่วย/legend/กราฟอ่านได้จริง; mobile ใช้ single-column และกราฟเลื่อนแนวนอนได้ ไม่มีเนื้อหาสำคัญถูกตัด → `captures/b8_desktop.png`, `captures/b8_mobile.png` | PASS |

หลักฐานกราฟเพิ่มเติม: `captures/b4_ac_desktop.png` (Bode gain+phase), `captures/b5_tran_desktop.png` (Vin/Vout)

## 22. การพิสูจน์ว่าไม่ใช่ mock data (B3/B4/B5/B6)

- ทุกกราฟสร้าง `<polyline>` จาก `spice["series"]` → `parse_raw()` อ่านบรรทัด `Values:` ของ `run.raw` ที่ ngspice เขียนจริง
- `app.py::make_plot()` คำนวณพิกัด SVG จาก series เท่านั้น ไม่มีตัวเลขกราฟฝังใน HTML/JS
- netlist และ engine log ที่ส่ง/ได้จริงแสดงใน `<details>` ทุกครั้ง → ตรวจ `RE EMIT 0 2000` / `SIN(0 0.03 2000)` ได้
- ถ้า `ngspice` หาย ระบบขึ้น `ไม่พบ ngspice ใน PATH ...` และ **ไม่ส่ง** `spice`/`plot` ให้ template → ไม่มีผลสำเร็จปลอม (ทดสอบใน `tests/test_web.py`)

## 23. ผลการรันเทสต์ (จริง)

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t .
```

```
Ran 65 tests in 0.815s

OK
```

แบ่งเป็น 52 tests เดิมของ Lab 3 + 13 tests ใหม่ของ Lab 4
(`tests/test_spice_engine.py` 10 tests — 5 netlist/validation + 5 เรียก ngspice จริง;
`tests/test_web.py::SpicePages` 3 tests — หน้า AC/transient และ error RE=0)

## 24. ข้อจำกัดที่ต้องแจ้งอาจารย์

- ไม่มี Starter Kit จากอาจารย์ → ใช้ BJT model ที่ระบุในข้อ 19 (เจ้าของโปรเจกต์อนุมัติแล้ว)
- Playwright MCP, Impeccable และ Superpowers skill ไม่พร้อมใน session นี้ → ใช้ OpenCode Browser + Chrome headless, CSS และ integration plan/approval workflow แทน ตามข้อ 20
- **ไม่มีจุดตัด −3 dB ในช่วง 10 Hz–10 MHz** ของ model นี้ (VAF=0, CJE/CJC/TF เล็ก) → แสดง `not determined in sweep range` ตามใบงาน ไม่ได้สร้าง fL/fH ขึ้นมาเอง
- ผล SPICE ของ `.op` ต่างจาก analytical เล็กน้อย (0.006 V / 0.002 mA) เพราะ SPICE ใช้โมเดล exponential จริง ไม่ใช่สมการ VBE คงที่ — **ไม่ถือว่าเป็นข้อผิดพลาด** และไม่ได้นำค่าทั้งสองมาปนกัน
- `ngspice` ไม่มี installer ที่สร้าง icon → ติดตั้งแบบ 7z และเพิ่ม path ลง `PATH` ของ user

## 25. วิธีรันซ้ำ

```powershell
cd C:\Users\B6809720\Documents\BJT-DC-Bias-Web-App
$env:Path = 'C:\Users\B6809720\AppData\Local\Programs\ngspice-47\Spice64\bin;' + $env:Path
.\.venv\Scripts\python.exe -m flask --app app run --host 127.0.0.1 --port 5000
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

เปิด <http://127.0.0.1:5000/> → เลือก **Analysis Mode** เป็น `SPICE DC · .op`, `SPICE AC · .ac` หรือ `SPICE Transient · .tran` แล้วกด Run

## 26. การส่งงาน

ตาม `AGENTS.md` ข้อ 9 **เจ้าของโปรเจกต์เป็นคน commit/push เองผ่าน GitHub Desktop** (AI ไม่รัน `git commit`/`git push`)
Commit ล่าสุดที่ push แล้ว: `9d3549fc5995cbca3483f35c7bedd082577f59b9` (`docs: note superpowers skill not run`)
`git status` ขึ้นแค่ `## lab04-ngspice...origin/lab04-ngspice` → working tree สะอาด ตรง remote แล้ว

## 27. บันทึก 3–5 บรรทัด — AI ทำอะไร / นักศึกษาตรวจอะไรเอง

- **AI สร้าง/แก้:** `spice_engine.py` (สร้าง netlist, เรียก `ngspice_con.exe` ด้วย `subprocess.run` แบบ list + timeout, parse `run.raw` ทั้ง real/complex), `app.py` (route `.op/.ac/.tran`, `make_plot`, reference/provenance), `templates/index.html`, `static/style.css`, `tests/` และเอกสารนี้
- **AI ตรวจด้วย tool:** `Ran 65 tests ... OK`, OpenCode Browser B1–B8, Chrome headless สำหรับ `captures/*.png` — แต่ผลทั้งหมดถูกอ่านจากหน้าเว็บ/engine จริง ไม่ใช่ค่าที่แต่งขึ้น
- **นักศึกษาตรวจ/ยืนยันเอง:** เปิดแท็บที่ focus ดูหน้าจอจริง, ขอ screenshot, อนุมัติ plan และ BJT model ที่ใช้แทน Starter Kit, เป็นคน commit/push ทุก commit รวม `9d3549f`
- **ไม่มี before/after ของ Impeccable** เพราะ skill ไม่พร้อม → ปรับ UI ด้วย CSS ใน commit `f0a3853` และระบุ `NOT RUN` ไว้ในข้อ 20 ตามตรง
- ข้อความ/ตัวเลขที่เห็นตรงกับ ngspice log และ netlist ที่แสดงใน `<details>` ทุกครั้ง ถ้า engine fail ระบบไม่โชว์ผลเก่าหรือ badge success ปลอม

