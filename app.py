import math

from flask import Flask, render_template, request

from dc_bias import calculate_dc_bias

app = Flask(__name__)

FIELD_NAMES = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")
RESISTOR_FIELDS = ("r1", "r2", "rc", "re")
KILO = 1000.0

REGION_LABELS = {
    "active": "Active",
    "cutoff": "Cutoff",
    "saturation": "Saturation",
}

DEFAULTS = {
    "vcc": "12",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1",
    "beta": "100",
    "vbe": "0.70",
}


def parse_form(form) -> dict:
    """แปลงค่าจากฟอร์ม (kΩ) เป็น SI (Ω) และตรวจว่ากรอกครบ/เป็นตัวเลขจริง"""
    raw_values = {}
    missing = []
    for name in FIELD_NAMES:
        raw = (form.get(name) or "").strip()
        if raw:
            raw_values[name] = raw
        else:
            missing.append(name)

    if missing:
        raise ValueError("กรุณากรอกตัวเลขให้ครบทุกช่อง: " + ", ".join(missing))

    values = {}
    non_numeric = []
    for name in FIELD_NAMES:
        raw = raw_values[name]
        try:
            values[name] = float(raw)
        except ValueError:
            non_numeric.append(f'{name} ("{raw}")')

    if non_numeric:
        raise ValueError("ช่องต่อไปนี้ไม่ใช่ตัวเลข: " + ", ".join(non_numeric))

    for name in RESISTOR_FIELDS:
        values[name] *= KILO

    # ต้องตรวจหลังแปลงหน่วย เพราะ 1e308 kΩ × 1000 ล้นเป็น inf
    non_finite = [
        f"{name} ({raw_values[name]})"
        for name in FIELD_NAMES
        if not math.isfinite(values[name])
    ]
    if non_finite:
        raise ValueError("ค่าต้องเป็นจำนวนจำกัด (finite): " + ", ".join(non_finite))

    return values


def converted_ohms(source) -> dict:
    """ค่าตัวต้านทานที่แปลงเป็น Ω แล้ว พร้อมแสดง (คั่นหลักพัน) สำหรับใต้ช่องกรอก"""
    ohms = {}
    for name in RESISTOR_FIELDS:
        raw = (source.get(name) or "").strip()
        try:
            value = float(raw) * KILO
        except ValueError:
            ohms[name] = None
        else:
            ohms[name] = f"{value:,.0f}" if math.isfinite(value) else None
    return ohms


def describe(result) -> dict:
    """ค่าพร้อมแสดงผล — template ทำหน้าที่แค่จัดวาง ไม่คำนวณหรือแปลงหน่วยเอง"""
    return {
        "region_class": result.region,
        "region_label": REGION_LABELS[result.region],
        "rows": (
            ("VTH", f"{result.vth:.3f}", "V"),
            ("RTH", f"{result.rth / KILO:.2f}", "kΩ"),
            ("IB", f"{result.ib * 1e6:.3f}", "µA"),
            ("IC", f"{result.ic * 1e3:.3f}", "mA"),
            ("IE", f"{result.ie * 1e3:.3f}", "mA"),
            ("VB", f"{result.vb:.3f}", "V"),
            ("VE", f"{result.ve:.3f}", "V"),
            ("VC", f"{result.vc:.3f}", "V"),
            ("VCE", f"{result.vce:.3f}", "V"),
        ),
    }


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            values = parse_form(request.form)
            result = calculate_dc_bias(**values)
        except ValueError as exc:
            return render_template(
                "index.html",
                values=request.form,
                ohms=converted_ohms(request.form),
                errors=[str(exc)],
            )

        return render_template(
            "index.html",
            values=request.form,
            ohms=converted_ohms(request.form),
            result=result,
            display=describe(result),
            warnings=result.warnings,
        )

    return render_template(
        "index.html",
        values=DEFAULTS,
        ohms=converted_ohms(DEFAULTS),
    )


if __name__ == "__main__":
    app.run(debug=True)
