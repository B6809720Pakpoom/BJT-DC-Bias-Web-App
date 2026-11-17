import math

from flask import Flask, render_template, request

from dc_bias import (
    calculate_dc_bias,
    calculate_emitter_bias,
    calculate_fixed_bias,
)

app = Flask(__name__)

COMMON_FIELDS = ("vcc", "rc", "beta", "vbe")
MODE_FIELDS = {
    "divider": COMMON_FIELDS + ("r1", "r2", "re"),
    "fixed": COMMON_FIELDS + ("rb",),
    "emitter": COMMON_FIELDS + ("rb", "re"),
}
CALCULATORS = {
    "divider": calculate_dc_bias,
    "fixed": calculate_fixed_bias,
    "emitter": calculate_emitter_bias,
}
MODE_LABELS = {
    "divider": "Voltage Divider Bias",
    "fixed": "Fixed Bias",
    "emitter": "Emitter Bias",
}
DEFAULT_MODE = "divider"

RESISTOR_FIELDS = ("r1", "r2", "rc", "re", "rb")
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
    "rb": "1000",
    "beta": "100",
    "vbe": "0.70",
}


def parse_form(form, mode: str) -> dict:
    """แปลงค่าจากฟอร์ม (kΩ) เป็น SI (Ω) และตรวจเฉพาะช่องที่โหมดนั้นใช้"""
    fields = MODE_FIELDS[mode]

    raw_values = {}
    missing = []
    for name in fields:
        raw = (form.get(name) or "").strip()
        if raw:
            raw_values[name] = raw
        else:
            missing.append(name)

    if missing:
        raise ValueError("กรุณากรอกตัวเลขให้ครบทุกช่อง: " + ", ".join(missing))

    values = {}
    non_numeric = []
    for name in fields:
        raw = raw_values[name]
        try:
            values[name] = float(raw)
        except ValueError:
            non_numeric.append(f'{name} ("{raw}")')

    if non_numeric:
        raise ValueError("ช่องต่อไปนี้ไม่ใช่ตัวเลข: " + ", ".join(non_numeric))

    # จุดเดียวของการแปลงหน่วย kΩ → Ω (AGENTS.md)
    for name in fields:
        if name in RESISTOR_FIELDS:
            values[name] *= KILO

    # ต้องตรวจหลังแปลงหน่วย เพราะ 1e308 kΩ × 1000 ล้นเป็น inf
    non_finite = [
        f"{name} ({raw_values[name]})"
        for name in fields
        if not math.isfinite(values[name])
    ]
    if non_finite:
        raise ValueError("ค่าต้องเป็นจำนวนจำกัด (finite): " + ", ".join(non_finite))

    return values


def converted_ohms(source, fields) -> dict:
    """ค่าตัวต้านทานที่แปลงเป็น Ω แล้ว พร้อมแสดงใต้ช่องที่โหมดนั้นใช้"""
    ohms = {}
    for name in fields:
        if name not in RESISTOR_FIELDS:
            continue
        raw = (source.get(name) or "").strip()
        try:
            value = float(raw) * KILO
        except ValueError:
            ohms[name] = None
        else:
            ohms[name] = f"{value:,.0f}" if math.isfinite(value) else None
    return ohms


def describe(result, mode: str) -> dict:
    """ค่าพร้อมแสดงผล — template ทำหน้าที่แค่จัดวาง ไม่คำนวณหรือแปลงหน่วยเอง"""
    rows = []
    if mode == "divider":
        rows.extend((
            ("VTH", f"{result.vth:.3f}", "V"),
            ("RTH", f"{result.rth / KILO:.2f}", "kΩ"),
        ))
    rows.extend((
        ("IB", f"{result.ib * 1e6:.3f}", "µA"),
        ("IC", f"{result.ic * 1e3:.3f}", "mA"),
        ("IE", f"{result.ie * 1e3:.3f}", "mA"),
        ("VB", f"{result.vb:.3f}", "V"),
        ("VE", f"{result.ve:.3f}", "V"),
        ("VC", f"{result.vc:.3f}", "V"),
        ("VCE", f"{result.vce:.3f}", "V"),
    ))
    return {
        "region_class": result.region,
        "region_label": REGION_LABELS[result.region],
        "mode_label": MODE_LABELS[mode],
        "rows": rows,
    }


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        mode = (request.form.get("mode") or DEFAULT_MODE).strip()

        # โหมดที่ไม่รู้จักต้องแจ้งข้อผิดพลาด ห้ามเดาเป็น Divider
        if mode not in MODE_FIELDS:
            return render_template(
                "index.html",
                values=request.form,
                mode=mode,
                ohms=converted_ohms(request.form, RESISTOR_FIELDS),
                errors=[f'โหมดไม่รู้จัก "{mode}" — เลือก Voltage Divider, Fixed หรือ Emitter Bias'],
            )

        try:
            values = parse_form(request.form, mode)
            result = CALCULATORS[mode](**values)
        except ValueError as exc:
            # ไม่ส่ง result/display → ผลรอบก่อนไม่โผล่มาเป็นผลของรอบที่กรอกผิด
            return render_template(
                "index.html",
                values=request.form,
                mode=mode,
                ohms=converted_ohms(request.form, MODE_FIELDS[mode]),
                errors=[f"[{MODE_LABELS[mode]}] {exc}"],
            )

        return render_template(
            "index.html",
            values=request.form,
            mode=mode,
            ohms=converted_ohms(request.form, MODE_FIELDS[mode]),
            result=result,
            display=describe(result, mode),
            warnings=result.warnings,
        )

    return render_template(
        "index.html",
        values=DEFAULTS,
        mode=DEFAULT_MODE,
        ohms=converted_ohms(DEFAULTS, MODE_FIELDS[DEFAULT_MODE]),
    )


if __name__ == "__main__":
    app.run(debug=True)
