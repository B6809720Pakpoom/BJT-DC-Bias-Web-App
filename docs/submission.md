# Lab 03 — สรุปสิ่งที่ส่ง (ENG29 2121 · 2/2569)

## 1. ข้อมูลRepository

| รายการ | ค่า |
|---|---|
| GitHub URL | <https://github.com/B6809720Pakpoom/BJT-DC-Bias-Web-App> |
| Branch | `main` |
| Commit SHA ของ Lab 3 | *(กรอกหลัง Push ผ่าน GitHub Desktop — ดูวิธีในข้อ 6)* |
| วิธีรัน | `python -m flask --app app run --debug` แล้วเปิด <http://127.0.0.1:5000/> |
| รันเทสต์ | `.venv\Scripts\python.exe -m unittest discover -s tests -t . -v` → **Ran 52 tests ... OK** |

---

## 2. สิ่งที่เปลี่ยนในโปรแกรม (ข้อ 1 ของ Deliverables)

| ไฟล์ | สิ่งที่เพิ่ม/เปลี่ยน |
|---|---|
| `dc_bias.py` | เพิ่ม `calculate_fixed_bias()` และ `calculate_emitter_bias()`; เพิ่ม `DcBiasResult.as_dict()`; รวม validation/region helper; **`calculate_dc_bias()` เดิมไม่ถูกแตะ** |
| `app.py` | `MODE_FIELDS`, `CALCULATORS`, `MODE_LABELS`; `if mode not in MODE_FIELDS` → error; `parse_form(form, mode)` อ่านเฉพาะฟิลด์ที่โหมดใช้; แปลง kΩ→Ω จุดเดียว; error ไม่ส่ง `result`/`display` |
| `templates/index.html` | `<select name="mode">`, ช่อง `rb`, JS `sync()` ซ่อน/โชว์ช่องตามโหมด (ไม่คำนวณ) |
| `static/style.css` | style ของ `select`, `.mode-field`, `[hidden]` |
| `tests/test_bias_modes.py` | 10 เทสต์ของ Fixed/Emitter (ใหม่) |
| `tests/test_web.py` | 9 เทสต์ของ A1–A5 + โหมดไม่รู้จัก + ไม่โชว์ผลเก่า |
| `tools/independent_reference.py` | ค่าอ้างอิงอิสระ `Decimal` 50 หลัก |
| `docs/` | `validation.md`, `design-note.md`, `reflection.md`, ภาพหลักฐาน |

### สมการที่เพิ่ม (หน่วย: Ω, A → แสดง V และ mA)

```
Fixed:    IB = (VCC − VBE) / RB                          ; VE = 0
Emitter:  IB = (VCC − VBE) / [RB + (β + 1)·RE]           ; VE = IE·RE
ร่วมกัน:   IC = β·IB, IE = (β+1)·IB, VB = VE + VBE
          VC = VCC − IC·RC, VCE = VC − VE
```

**จุดเลือกฟังก์ชัน:** `app.py` → `CALCULATORS[mode]` หลังตรวจ `mode in MODE_FIELDS`
**จุดแปลงหน่วย:** `app.py` → `parse_form()` บรรทัด `values[name] *= 1000` เท่านั้น
**คีย์ผลลัพธ์ร่วมกัน:** `vb_v`, `ve_v`, `vc_v`, `vce_v`, `ic_ma`, `ib_ua`, `region`, `warnings`
(สคริปต์อิสระ `tools/independent_reference.py` **ไม่ import** `dc_bias`/`app`)

---

## 3. ตาราง A1–A5 (ข้อ 2 ของ Deliverables)

ใช้ร่วมกัน: `VCC = 12 V, RC = 2.2 kΩ, β = 100, VBE = 0.70 V`
เกณฑ์: `|ΔIC| ≤ 0.01 mA`, `|ΔVCE| ≤ 0.02 V` เทียบค่าที่ยังไม่ปัดเศษ

| กรณี | อินพุต | คาดหมายก่อนรัน | เห็นจริง | วิธีตรวจ | สถานะ |
|---|---|---|---|---|---|
| A1 Divider | R1=100, R2=22, RE=1 kΩ | 1.229858146 mA / 8.052155351 V | **1.230 mA / 8.052 V**, Active | OpenCode Browser | PASS |
| A2 Fixed | RB=1000 kΩ (ไม่ใช้ RE) | 1.130000000 mA / 9.514000000 V | **1.130 mA / 9.514 V** | OpenCode Browser + ทวนซ้ำ Manual | PASS |
| A3 Emitter | RB=1000, RE=1 kΩ | 1.026339691 mA / 8.705449591 V | **1.026 mA / 8.705 V** | OpenCode Browser | PASS |
| A4 เปลี่ยนค่าเดียว | เหมือน A3 แต่ RE=2 kΩ | ทำนาย **IC ลด** → ~0.940 mA | **0.940 mA / 8.033 V** (ลดจริง) | OpenCode Browser | PASS |
| A5 อินพุตผิด | Fixed, RB=0 | แจ้งแก้ RB, ไม่ล่ม, ไม่โชว์ผลเก่า | `[Fixed Bias] ค่าความต้านทานต้องมากกว่า 0 Ω (พบ RB = 0 Ω)`; ไม่มีตารางผล | OpenCode Browser | PASS |

**วิธีตรวจจริง:** OpenCode Browser (`browser.navigate/snapshot/select/fill/click/evaluate/screenshot`).
มี `POST http://127.0.0.1:5000/` ใน network log ทุกกรณี — ไม่ได้ใช้ `curl` หรืออ่านโค้ดแทน

**Playwright MCP = NOT RUN** พร้อมเหตุผล: ไม่มี `node`/`npx`, ไม่มี `opencode.json`/`.jsonc`,
และไม่มี MCP `playwright` เชื่อมต่อใน session นี้ → ใช้ Browser Tool ของ OpenCode Desktop แทน
ตามที่ใบงาน Section 05 อนุญาต (ให้คะแนนการตรวจผลเท่ากัน)

**หลักฐาน:** `docs/evidence/A2-fixed-bias.png` (full-page screenshot) และข้อความผลที่คัดมา:
```
ผลลัพธ์ DC Bias — Fixed Bias
IB 11.300 µA | IC 1.130 mA | IE 1.141 mA
VB 0.700 V   | VE 0.000 V  | VC 9.514 V | VCE 9.514 V
```

---

## 4. ค่าอ้างอิงอิสระ (ข้อ 3 ของ Deliverables)

คำนวณด้วย `decimal.Decimal` 50 หลัก ตั้ง `IE` เป็นตัวตั้ง (ต่างเส้นทางจากโปรแกรมที่ตั้ง `IB`):

| กรณี | สมการที่ใช้ | IC (mA) | VCE (V) |
|---|---|---|---|
| A2 Fixed | `IB=(12−0.70)/1e6` | 1.130000000 | 9.514000000 |
| A3 Emitter | `IB=(12−0.70)/(1e6+101×1000)` | 1.026339691 | 8.705449591 |
| A4 Emitter | `IB=(12−0.70)/(1e6+101×2000)` | 0.940099834 | 8.032778702 |

รันซ้ำ: `.venv\Scripts\python.exe tools\independent_reference.py`

**AI ช่วยส่วนไหน / นักศึกษาตรวจอะไร** → ตารางละเอียดใน `docs/reflection.md`
**คำตอบคำถามปิด Lab** (ไล่ค่าจากฟอร์ม → Flask → แปลงหน่วย → ฟังก์ชัน) → `docs/reflection.md`

---

## 5. ผลทดสอบ

```
ก่อนแก้ (baseline Lab 2)   Ran 33 tests ... OK
เขียนเทสต์ใหม่ก่อนแก้ (RED)  Ran 43 tests ... FAILED (failures=8, errors=1)
หลังแก้ (GREEN)             Ran 52 tests ... OK
รอบสุดท้าย                 Ran 52 tests in 0.047s ... OK
```

---

## 6. สิ่งที่เจ้าของโปรเจกต์ต้องทำเอง (ผมไม่รัน commit/push ตาม `AGENTS.md` ข้อ 9)

1. เปิด **GitHub Desktop** → เลือก repo `BJT-DC-Bias-Web-App` → branch `main`
2. แท็บ **Changes** → ติ๊ก **All** → ตรวจว่าไม่มี `.venv`/`.env`
3. **Summary:** `feat: add fixed and emitter bias modes with browser validation`
4. กด **Commit to main** → กด **Push origin**
5. แท็บ **History** → **Copy full SHA** → กรอกใน `README.md` บรรทัด *Commit SHA ของ Lab 3* และ/หรือในรายงานส่ง
6. ส่งผ่าน Moodle: GitHub URL + Commit SHA + `docs/validation.md` + ภาพ `docs/evidence/A2-fixed-bias.png` + ไฟล์นี้
