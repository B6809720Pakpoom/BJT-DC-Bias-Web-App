from flask import Flask, render_template, request

from dc_bias import calculate_dc_bias

app = Flask(__name__)

FIELD_NAMES = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")
RESISTOR_FIELDS = ("r1", "r2", "rc", "re")
KILO = 1000.0

DEFAULTS = {
    "vcc": "12",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1",
    "beta": "100",
    "vbe": "0.70",
}


def parse_form(form):
    """แปลงค่าจากฟอร์ม (kΩ) เป็น SI (Ω) และตรวจว่ากรอกครบ/เป็นตัวเลข"""
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
    for name, raw in raw_values.items():
        try:
            values[name] = float(raw)
        except ValueError:
            raise ValueError(
                f"กรุณากรอกตัวเลขให้ครบทุกช่อง: ช่อง {name} = {raw!r} ไม่ใช่ตัวเลข"
            ) from None

    for name in RESISTOR_FIELDS:
        values[name] *= KILO

    return values


def converted_ohms(source):
    """ค่าตัวต้านทานที่แปลงเป็น Ω แล้ว สำหรับแสดงใต้ช่องกรอก"""
    ohms = {}
    for name in RESISTOR_FIELDS:
        raw = (source.get(name) or "").strip()
        try:
            ohms[name] = float(raw) * KILO
        except ValueError:
            ohms[name] = None
    return ohms


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
        )

    return render_template(
        "index.html",
        values=DEFAULTS,
        ohms=converted_ohms(DEFAULTS),
    )


if __name__ == "__main__":
    app.run(debug=True)
