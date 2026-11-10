# AGENTS.md — กติกาสำหรับ AI Agent

โปรเจกต์นี้เป็นงาน Lab 02 (ENG29 2121) — Flask Web App คำนวณ BJT DC Bias
อ่าน `README.md` และ `docs/design-note.md` ก่อนแก้โค้ด

## กติกาที่ห้ามละเมิด

1. **ห้ามใส่สมการใน template** — `templates/index.html` ทำหน้าที่แสดงผลเท่านั้น
   การคำนวณทุกอย่างต้องอยู่ใน `dc_bias.py`
2. **ห้าม import Flask (หรืออะไรที่เกี่ยวกับ HTTP) ใน `dc_bias.py`** — ไฟล์นี้ต้องเป็น
   ฟังก์ชันบริสุทธิ์ที่ทดสอบได้โดยไม่ต้องมี web server
3. **`dc_bias.py` รับ SI units เท่านั้น (V, Ω, A)** — การแปลง kΩ → Ω เกิดที่ `app.py`
   ใน `parse_form()` ที่เดียว ห้ามเพิ่มจุดแปลงหน่วยที่อื่น
4. **ห้ามปัดค่ากลาง** — เก็บ float เต็มความละเอียด ปัดเฉพาะตอนแสดงผล
   (V 3 ตำแหน่ง, IB 3 ตำแหน่ง µA, IC/IE 3 ตำแหน่ง mA, RTH 2 ตำแหน่ง kΩ)
5. **ทุกครั้งที่แก้สมการ ต้องมีหรือแก้เทสต์ใน `tests/test_dc_bias.py` ก่อน** และต้องรันให้เห็น
   ว่าเทสต์ล้มเหลวก่อนแก้ แล้วผ่านหลังแก้
6. **ใช้ `unittest` จาก stdlib เท่านั้น** — ห้ามเพิ่ม pytest หรือ test framework อื่น
7. **dependency ที่อนุญาตมีตัวเดียว: `Flask==3.1.3`** — ก่อนเพิ่มไลบรารีใหม่ต้องถามเจ้าของโครงงานก่อน
8. **ข้อความที่ผู้ใช้เห็นเป็นภาษาไทย** แต่ศัพท์เทคนิคคงเป็นอังกฤษ (cutoff, saturation,
   forward-active, VCE, VBE)
9. **ห้ามรัน `git commit` หรือ `git push`** — เจ้าของโครงงาน commit เองผ่าน GitHub Desktop
10. **ห้ามรายงานว่าผ่านโดยไม่รันคำสั่งจริง** — ต้องแสดงผลลัพธ์ `Ran N tests ... OK` ประกอบ

## คำสั่งที่ใช้

```powershell
# ติดตั้ง (ครั้งแรก)
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# รันเทสต์ทั้งหมด (ต้องได้ 33 tests OK)
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v

# รันเฉพาะชุด
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -p "test_dc_bias.py" -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -p "test_web.py" -v

# เปิดเว็บ
.\.venv\Scripts\python.exe -m flask --app app run --debug
```

> ต้องมี `-t .` เมื่อรันจาก root ของโปรเจกต์ถ้าเจอ ImportError (ใบงานใช้ `discover -s tests -v`
> ซึ่งก็ผ่านเช่นกัน) เพราะ `tests/` เป็น package (มี `tests/__init__.py`)

## แผนที่ไฟล์

| ไฟล์ | แก้เมื่อ |
|---|---|
| `dc_bias.py` | เปลี่ยนสมการ / validation / เกณฑ์ region |
| `app.py` | เปลี่ยน route / การแปลงหน่วย / การจัดการ error |
| `templates/index.html` | เปลี่ยนการแสดงผล (ห้ามคำนวณ) |
| `static/style.css` | เปลี่ยนหน้าตา |
| `tests/test_dc_bias.py` | แก้สมการหรือ region (ต้องแก้ก่อน/พร้อมโค้ด) |
| `tests/test_web.py` | แก้ route, ชื่อ field, ข้อความ error, การแสดงผล |

## ชื่อ field ที่ห้ามเปลี่ยน

`vcc`, `r1`, `r2`, `rc`, `re`, `beta`, `vbe` — ทั้ง `app.py`, template และเทสต์อ้างชื่อเหล่านี้
ถ้าจำเป็นต้องเปลี่ยน ให้แก้ทั้งสามที่พร้อมกันและอัปเดตเทสต์

## ค่าอ้างอิงสำหรับตรวจงาน

`VCC=12, R1=100k, R2=22k, RC=2.2k, RE=1k, β=100, VBE=0.70`
→ VCE = 8.052 V, IC = 1.230 mA, IB = 12.299 µA, region = Active

รายละเอียดการพิสูจน์อยู่ใน `docs/validation.md`

## รูปแบบ commit (เจ้าของโครงงานทำเอง)

ใช้ Conventional Commits ภาษาอังกฤษ ขึ้นต้นด้วย `feat:` / `fix:` / `docs:` / `test:` / `chore:`
เช่น `feat: add cutoff and saturation region warnings`
