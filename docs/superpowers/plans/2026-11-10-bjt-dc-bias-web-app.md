# BJT DC Bias Web App — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** สร้าง Flask Web Application ที่รับค่า VCC, R1, R2, RC, RE, β, VBE แล้วคำนวณ DC operating point ของ BJT Common-Emitter (voltage-divider bias) ด้วย Python พร้อม validation, region warning และ automated tests

**Architecture:** แยก 3 ชั้นชัดเจน — `dc_bias.py` (สมการบริสุทธิ์ SI units, ไม่รู้จัก HTTP), `app.py` (Flask routes, แปลง kΩ→Ω, จัดการ error), `templates/index.html` + `static/style.css` (การนำเสนอ) ทดสอบด้วย `unittest` ทั้งระดับสมการและ HTTP

**Tech Stack:** Python 3.15.2, Flask 3.1.3, Jinja2, `unittest` (stdlib)

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-dc-bias-web-app-design.md`

## Global Constraints

- Python 3.15.2; dependency เดียวที่อนุญาตคือ `Flask==3.1.3` (ห้ามเพิ่ม library อื่น)
- ใช้ `unittest` จาก stdlib เท่านั้น (ห้าม pytest)
- `dc_bias.py` รับหน่วย **SI เท่านั้น (V, Ω)** — ห้ามรับ kΩ ห้าม import Flask/HTML
- การแปลง kΩ → Ω เกิดขึ้นที่ `app.py` ที่เดียว (คูณ 1000)
- ห้ามปัดค่ากลาง: เก็บ float เต็ม ปัดเฉพาะตอนแสดงผล (V 3 ตำแหน่ง, mA 3, µA 3, kΩ 2)
- ข้อความ error/warning ภาษาไทย แต่ศัพท์เทคนิคเป็นอังกฤษ (cutoff, saturation, forward-active)
- **การ commit ทุกครั้งทำโดยเจ้าของโครงงานผ่าน GitHub Desktop** — agent ห้ามรัน `git commit`
- ชื่อไฟล์/ฟังก์ชันต้องตรงตาม Interfaces block ของแต่ละ task

## Review Focus

1. **ค่าตัวต้านทานเป็นศูนย์หรือติดลบในช่องใดก็ได้** (รวม R2=0, RC=0) → ต้องได้ข้อความ error ที่อ่านเข้าใจ ไม่ใช่ `ZeroDivisionError` หรือ HTTP 500
2. **ค่าที่ไม่ใช่ตัวเลขแต่ดูเหมือนตัวเลข** เช่น `12,0` (มีคอมมา) หรือ `1 000` → ต้องแจ้งว่ากรอกไม่ถูก ไม่ crash
3. **VTH ใกล้หรือเท่ากับ VBE พอดี** → ต้องจัดเป็น cutoff ไม่ใช่ active ที่มี IB ติดลบหรือเกือบศูนย์
4. **VCC ใหญ่มาก (1e6) หรือค่าน้อยมาก** → คำนวณได้ ไม่ overflow/ไม่ crash และยังแสดงผลได้
5. **กด POST ซ้ำ / refresh หน้าผลลัพธ์** → ยังตอบ 200 และคำนวณใหม่ได้ ไม่ error

---

## File Structure

| ไฟล์ | ความรับผิดชอบ |
|---|---|
| `dc_bias.py` | dataclass `DcBiasResult`, ฟังก์ชัน `calculate_dc_bias()`, validation, region logic — ไม่มี I/O |
| `app.py` | Flask app, helper `parse_form()` (str→float + kΩ→Ω), route `GET /` และ `POST /`, จัดการ `ValueError` |
| `templates/index.html` | ฟอร์ม, ตารางผลลัพธ์, badge region, error list, warning list |
| `static/style.css` | layout, สี, responsive |
| `tests/test_dc_bias.py` | unit tests ของสมการ + region + validation |
| `tests/test_web.py` | HTTP tests ผ่าน `app.test_client()` |
| `requirements.txt` | `Flask==3.1.3` |
| `AGENTS.md` | กติกาโค้ดสำหรับ AI agent |
| `docs/design-note.md` | เหตุผลการออกแบบ |
| `docs/validation.md` | หลักฐานตรวจสอบกับค่าอ้างอิง |
| `docs/reflection.md` | สิ่งที่เรียนรู้และข้อจำกัด |

---

### Task 1: Engineering core — active region + validation

**Files:**
- Create: `dc_bias.py`
- Create: `tests/test_dc_bias.py`
- Create: `requirements.txt`

**Interfaces:**
- Produces: `dc_bias.DcBiasResult` (frozen dataclass) fields — `vth, rth, ib, ic, ie, vb, ve, vc, vce: float`, `region: str`, `warnings: tuple[str, ...]`
- Produces: `dc_bias.calculate_dc_bias(vcc, r1, r2, rc, re, beta, vbe) -> DcBiasResult` — รับ SI, raise `ValueError` เมื่ออินพุตผิด

- [ ] **Step 1: เขียนเทสต์ที่ยังไม่ผ่าน**

สร้าง `tests/test_dc_bias.py`:

```python
import unittest

from dc_bias import calculate_dc_bias

TOL = 1e-9


class ReferenceCase(unittest.TestCase):
    def setUp(self):
        self.r = calculate_dc_bias(
            vcc=12.0, r1=100_000.0, r2=22_000.0,
            rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70,
        )

    def assertRel(self, actual, expected):
        self.assertAlmostEqual(actual, expected, delta=abs(expected) * TOL)

    def test_reference_case_matches_independent_calculation(self):
        self.assertRel(self.r.vth, 2.1639344262295084)
        self.assertRel(self.r.rth, 18032.786885245903)
        self.assertRel(self.r.ib, 1.2298581462608458e-05)
        self.assertRel(self.r.ic, 0.0012298581462608458)
        self.assertRel(self.r.ie, 0.0012421567277234543)
        self.assertRel(self.r.ve, 1.2421567277234544)
        self.assertRel(self.r.vb, 1.9421567277234544)
        self.assertRel(self.r.vc, 9.29431207822614)
        self.assertRel(self.r.vce, 8.052155350502685)

    def test_reference_case_is_active(self):
        self.assertEqual(self.r.region, "active")
        self.assertEqual(self.r.warnings, ())


class Validation(unittest.TestCase):
    BASE = dict(vcc=12.0, r1=100_000.0, r2=22_000.0,
                rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70)

    def call(self, **overrides):
        return calculate_dc_bias(**{**self.BASE, **overrides})

    def test_rejects_zero_resistance(self):
        for key in ("r1", "r2", "rc", "re"):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    self.call(**{key: 0.0})

    def test_rejects_negative_resistance(self):
        with self.assertRaises(ValueError):
            self.call(rc=-1.0)

    def test_rejects_non_positive_beta(self):
        for beta in (0.0, -5.0):
            with self.subTest(beta=beta):
                with self.assertRaises(ValueError):
                    self.call(beta=beta)

    def test_rejects_non_positive_vcc(self):
        with self.assertRaises(ValueError):
            self.call(vcc=0.0)

    def test_rejects_vbe_outside_range(self):
        for vbe in (-0.1, 12.0):
            with self.subTest(vbe=vbe):
                with self.assertRaises(ValueError):
                    self.call(vbe=vbe)

    def test_handles_very_large_vcc(self):
        r = self.call(vcc=1_000_000.0)
        self.assertEqual(r.region, "active")
        self.assertGreater(r.ic, 0.0)
```

- [ ] **Step 2: รันเทสต์ให้เห็นว่าล้มเหลว**

Run: `python -m unittest discover -s tests -t . -p "test_dc_bias.py" -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dc_bias'`

- [ ] **Step 3: เขียน `dc_bias.py`**

สร้าง `dc_bias.py` — ฟังก์ชัน `calculate_dc_bias` คำนวณ VTH, RTH, IB, IC, IE, VE, VB, VC, VCE ตามสมการใน spec §7.4 แล้วคืน `DcBiasResult`; ตรวจ validation ตามตาราง spec §7.3 และ raise `ValueError` พร้อมข้อความภาษาไทย; ใน task นี้ให้ตั้ง `region="active"` และ `warnings=()` ไว้ก่อน (region logic อยู่ใน Task 2)

สร้าง `requirements.txt`:

```
Flask==3.1.3
```

- [ ] **Step 4: รันเทสต์ให้ผ่าน**

Run: `python -m unittest discover -s tests -t . -p "test_dc_bias.py" -v`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit (เจ้าของโครงงานทำใน GitHub Desktop)**

Summary: `feat: add dc_bias core calculation and validation`
จากนั้นกด **Commit to main** → **Push origin**

---

### Task 2: Region logic — cutoff และ saturation

**Files:**
- Modify: `dc_bias.py`
- Modify: `tests/test_dc_bias.py`

**Interfaces:**
- Consumes: `calculate_dc_bias(...)` และ `DcBiasResult` จาก Task 1
- Produces: ค่า `region` เป็น `"active"` | `"cutoff"` | `"saturation"` และ `warnings` ที่ไม่ว่างเมื่อ region ไม่ใช่ active

- [ ] **Step 1: เขียนเทสต์ที่ยังไม่ผ่าน**

เพิ่มใน `tests/test_dc_bias.py`:

```python
class RegionLogic(unittest.TestCase):
    def test_cutoff_when_vth_not_above_vbe(self):
        r = calculate_dc_bias(
            vcc=12.0, r1=100_000.0, r2=5_000.0,
            rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70,
        )
        self.assertEqual(r.region, "cutoff")
        self.assertEqual(r.ib, 0.0)
        self.assertEqual(r.ic, 0.0)
        self.assertEqual(r.ie, 0.0)
        self.assertEqual(r.ve, 0.0)
        self.assertEqual(r.vc, 12.0)
        self.assertAlmostEqual(r.vb, 12.0 * 5_000.0 / 105_000.0)
        self.assertAlmostEqual(r.vce, 12.0 - r.vb)
        self.assertTrue(r.warnings)

    def test_saturation_when_vce_at_or_below_margin(self):
        r = calculate_dc_bias(
            vcc=12.0, r1=100_000.0, r2=22_000.0,
            rc=15_000.0, re=1_000.0, beta=100.0, vbe=0.70,
        )
        self.assertEqual(r.region, "saturation")
        self.assertLessEqual(r.vce, 0.3)
        self.assertTrue(r.warnings)

    def test_boundary_exactly_at_vbe_is_cutoff(self):
        # VTH == VBE exactly
        vcc, vbe = 12.0, 0.70
        r2 = 1_000.0
        r1 = vcc * r2 / vbe - r2
        r = calculate_dc_bias(vcc=vcc, r1=r1, r2=r2, rc=2_200.0,
                              re=1_000.0, beta=100.0, vbe=vbe)
        self.assertEqual(r.region, "cutoff")
        self.assertTrue(r.warnings)

    def test_warning_text_mentions_limitation(self):
        r = calculate_dc_bias(vcc=12.0, r1=100_000.0, r2=5_000.0,
                              rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70)
        joined = " ".join(r.warnings)
        self.assertIn("cutoff", joined)
```

- [ ] **Step 2: รันเทสต์ให้เห็นว่าล้มเหลว**

Run: `python -m unittest discover -s tests -t . -p "test_dc_bias.py" -v`
Expected: FAIL — region ยังเป็น `"active"` ในทุกกรณี (4 tests ใหม่ล้มเหลว)

- [ ] **Step 3: เพิ่ม region logic ใน `dc_bias.py`**

ใน `calculate_dc_bias` หลังคำนวณ VTH, RTH:
- ถ้า `vth <= vbe` → `region="cutoff"`, ตั้ง `ib=ic=ie=0.0`, `ve=0.0`, `vb=vth`, `vc=vcc`, `vce=vcc-vth`, `warnings=(ข้อความที่มีคำว่า "cutoff",)` แล้วคืนค่าทันที
- ไม่อย่างนั้นคำนวณ IB..VCE ตามปกติ แล้วถ้า `vce <= 0.3` → `region="saturation"`, `warnings=(ข้อความที่มีคำว่า "saturation",)`; ไม่อย่างนั้น `region="active"`, `warnings=()`

- [ ] **Step 4: รันเทสต์ให้ผ่าน**

Run: `python -m unittest discover -s tests -t . -p "test_dc_bias.py" -v`
Expected: PASS (12 tests)

- [ ] **Step 5: Commit (เจ้าของโครงงานทำใน GitHub Desktop)**

Summary: `feat: add cutoff and saturation region warnings`

---

### Task 3: Flask skeleton และหน้าฟอร์ม (GET /)

**Files:**
- Create: `app.py`
- Create: `templates/index.html`
- Create: `tests/test_web.py`

**Interfaces:**
- Consumes: `calculate_dc_bias` จาก Task 1–2
- Produces: `app` (Flask instance) ที่ `tests/test_web.py` import ได้; route `GET /` คืน 200
- Produces: ชื่อฟิลด์ฟอร์มที่คงที่ — `vcc`, `r1`, `r2`, `rc`, `re`, `beta`, `vbe` (ตัวต้านทานกรอกเป็น kΩ)

- [ ] **Step 1: เขียนเทสต์ที่ยังไม่ผ่าน**

สร้าง `tests/test_web.py`:

```python
import unittest

from app import app


class FormPage(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_get_index_returns_200(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)

    def test_form_contains_all_input_names(self):
        body = self.client.get("/").get_data(as_text=True)
        for name in ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"):
            self.assertIn(f'name="{name}"', body)

    def test_form_mentions_kohm_for_resistors(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn("kΩ", body)
```

- [ ] **Step 2: รันเทสต์ให้เห็นว่าล้มเหลว**

Run: `python -m unittest discover -s tests -t . -p "test_web.py" -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: สร้าง `app.py` และ `templates/index.html`**

`app.py`: สร้าง `app = Flask(__name__)`, route `GET /` คืน `render_template("index.html")`
`templates/index.html`: ฟอร์ม `method="post"` มี input 7 ช่องตามชื่อข้างต้น ใส่ค่าเริ่มต้น (12, 100, 22, 2.2, 1, 100, 0.70), label ตัวต้านทานมีหน่วย `kΩ`, ปุ่ม submit ชื่อ `Calculate DC Bias`, และมี block ว่างสำหรับ error/warning/ผลลัพธ์ไว้รอ Task 4

- [ ] **Step 4: รันเทสต์ให้ผ่าน**

Run: `python -m unittest discover -s tests -t . -p "test_web.py" -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit (เจ้าของโครงงานทำใน GitHub Desktop)**

Summary: `feat: add flask app and dc bias input form`

---

### Task 4: POST / — คำนวณ, แปลง kΩ, แสดงผล, จัดการ error

**Files:**
- Modify: `app.py`
- Modify: `templates/index.html`
- Modify: `tests/test_web.py`

**Interfaces:**
- Consumes: `calculate_dc_bias`, `DcBiasResult`
- Produces: helper `parse_form(form) -> dict` ใน `app.py` ที่คืนค่าหน่วย SI (Ω) หรือ raise `ValueError` พร้อมข้อความภาษาไทย

- [ ] **Step 1: เขียนเทสต์ที่ยังไม่ผ่าน**

เพิ่มใน `tests/test_web.py`:

```python
VALID_FORM = dict(vcc="12", r1="100", r2="22", rc="2.2",
                  re="1", beta="100", vbe="0.70")


class Calculation(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def post(self, **overrides):
        return self.client.post("/", data={**VALID_FORM, **overrides})

    def test_valid_post_shows_reference_results(self):
        resp = self.post()
        body = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("8.052", body)   # VCE
        self.assertIn("1.230", body)   # IC (mA)
        self.assertIn("12.299", body)  # IB (µA)

    def test_valid_post_shows_active_region(self):
        body = self.post().get_data(as_text=True)
        self.assertIn("Active", body)

    def test_zero_resistance_shows_readable_error(self):
        resp = self.post(r1="0")
        body = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("มากกว่า 0", body)
        self.assertNotIn("Traceback", body)

    def test_non_numeric_input_shows_readable_error(self):
        resp = self.post(vcc="abc")
        body = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("ตัวเลข", body)
        self.assertNotIn("Traceback", body)

    def test_comma_decimal_is_rejected_clearly(self):
        resp = self.post(r1="12,0")
        body = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("ตัวเลข", body)

    def test_repated_post_keeps_working(self):
        self.post()
        resp = self.post()
        self.assertEqual(resp.status_code, 200)
        self.assertIn("8.052", resp.get_data(as_text=True))
```

- [ ] **Step 2: รันเทสต์ให้เห็นว่าล้มเหลว**

Run: `python -m unittest discover -s tests -t . -p "test_web.py" -v`
Expected: FAIL — POST ยังไม่ถูก implement (405 หรือ 200 ที่ไม่มีตัวเลข)

- [ ] **Step 3: เพิ่ม `POST /` และการแสดงผล**

`app.py`:
- เพิ่ม `route("/", methods=["GET", "POST"])`
- helper `parse_form(form)`: อ่าน 7 ค่า, ถ้าว่างหรือแปลง float ไม่ได้ → `ValueError("กรุณากรอกตัวเลขให้ครบทุกช่อง: …")`; แปลง `r1, r2, rc, re` เป็น Ω ด้วย `× 1000`
- เรียก `calculate_dc_bias(...)` แล้วส่ง `result` ให้ template; จับ `ValueError` แล้วส่ง `errors=[str(e)]` กลับไปที่ฟอร์มพร้อมค่าที่ผู้ใช้กรอก (เพื่อไม่ให้ต้องพิมพ์ใหม่)

`templates/index.html`:
- แสดง `errors` เป็นรายการ
- แสดง `result.warnings` เป็นกล่องเตือน
- ใต้ช่องตัวต้านทานแต่ละช่องแสดงค่าที่แปลงเป็น Ω แล้ว (เช่น `= 100,000 Ω`) เพื่อให้ผู้ใช้ตรวจสอบหน่วยได้ — ส่งค่าที่แปลงแล้วมาจาก `app.py`
- ตารางผลลัพธ์: VTH (V), RTH (kΩ), IB (µA), IC (mA), IE (mA), VB (V), VE (V), VC (V), VCE (V) — ใช้ `"%.3f"` ยกเว้น RTH ใช้ `"%.2f"`
- badge region: `Active` / `Cutoff` / `Saturation`

- [ ] **Step 4: รันเทสต์ทั้งหมดให้ผ่าน**

Run: `python -m unittest discover -s tests -t . -v`
Expected: PASS (21 tests) — 12 จาก test_dc_bias + 9 จาก test_web

- [ ] **Step 5: ตรวจด้วยตาในเบราว์เซอร์**

Run: `python -m flask --app app run --debug` แล้วเปิด `http://127.0.0.1:5000/`
Expected: กรอกค่าเริ่มต้น → กด Calculate → เห็น VCE 8.052 V, IC 1.230 mA, IB 12.299 µA, badge Active
ทดลองกรอก `R1 = 0` → เห็นข้อความ error ไม่ใช่หน้า error ของ Flask

- [ ] **Step 6: Commit (เจ้าของโครงงานทำใน GitHub Desktop)**

Summary: `feat: calculate dc bias from form and render results`

---

### Task 5: Styling และเอกสารประกอบ

**Files:**
- Create: `static/style.css`
- Create: `AGENTS.md`
- Create: `docs/design-note.md`
- Create: `docs/validation.md`
- Create: `docs/reflection.md`
- Modify: `templates/index.html`
- Modify: `README.md`

**Interfaces:**
- Consumes: โครง HTML จาก Task 3–4 (ไม่เปลี่ยนชื่อ field หรือ route)

- [ ] **Step 1: เพิ่ม `static/style.css` และเชื่อมกับ template**

สร้าง CSS: พื้นหลังอ่อน, การ์ดขาว, ฟอร์มเป็น grid 2 คอลัมน์บนจอกว้างและ 1 คอลัมน์บนจอแคบ (`@media (max-width: 640px)`), ตารางผลลัพธ์มีเส้นตาราง, badge สีต่างกัน 3 สี (active เขียว / cutoff เทา / saturation ส้ม), กล่อง error แดงอ่อน, กล่อง warning ส้มอ่อน
ใน `templates/index.html` เพิ่ม `<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">`

- [ ] **Step 2: ตรวจว่าเว็บยังทำงานหลังเพิ่ม CSS**

Run: `python -m unittest discover -s tests -t . -v`
Expected: PASS (21 tests — ตัวเลขเดิม ไม่มี regression)

- [ ] **Step 3: เขียน `docs/validation.md`**

บันทึก: ค่าอ้างอิงความละเอียดเต็ม (spec §10.3), วิธีคำนวณอิสระ (มือ + สคริปต์), ผลจากหน้าเว็บที่ปัดแล้ว, และสรุปว่าตรงกันภายใน 0.1%

- [ ] **Step 4: เขียน `docs/design-note.md` และ `docs/reflection.md`**

`design-note.md`: สรุปการตัดสินใจ — แยก `dc_bias.py`, รับ kΩ ที่ UI แปลงที่ `app.py`, route เดียว, เกณฑ์ cutoff/saturation, ทำไมไม่ใช้ JavaScript คำนวณ
`reflection.md`: สิ่งที่เรียนรู้, จุดที่ AI ช่วย/ไม่ช่วย, ข้อจำกัดของแบบจำลอง forward-active, สิ่งที่จะทำต่อในสัปดาห์ถัดไป

- [ ] **Step 5: เขียน `AGENTS.md` และอัปเดต `README.md`**

`AGENTS.md`: กติกา — ห้ามใส่สมการใน template, ห้าม import Flask ใน `dc_bias.py`, ต้องมี test ทุกครั้งที่แก้สมการ, ใช้ `unittest`, ข้อความผู้ใช้ภาษาไทย
`README.md`: อัปเดตสถานะจาก WIP เป็นพร้อมใช้, เพิ่มตัวอย่างผลลัพธ์, ยืนยันคำสั่งรัน/ทดสอบตรงกับของจริง

- [ ] **Step 6: Commit (เจ้าของโครงงานทำใน GitHub Desktop)**

Summary: `docs: add styling, validation notes and reflection`

---

## Definition of Done (เทียบกับ Acceptance A1–A7)

| เกณฑ์ | Task ที่ทำให้สำเร็จ |
|---|---|
| A1 GET / = 200 + เห็นฟอร์ม | Task 3 |
| A2 POST คำนวณจริงด้วย Python | Task 4 |
| A3 ผลตรงค่าอ้างอิงอิสระ | Task 1 (test) + Task 4 (แสดงผล) |
| A4 Validation อ่านได้ ไม่ crash | Task 1 (logic) + Task 4 (web) |
| A5 Warning นอก active region | Task 2 + Task 4 |
| A6 ≥3 unit tests + ≥1 HTTP test | Task 1, 2, 3, 4 (รวม 17 tests) |
| A7 clone → รันได้ตาม README | Task 5 |
