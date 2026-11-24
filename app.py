import math

from flask import Flask, render_template, request

from dc_bias import (
    calculate_dc_bias,
    calculate_emitter_bias,
    calculate_fixed_bias,
)
from spice_engine import (
    BJT_MODEL,
    SpiceError,
    run_ac_analysis,
    run_dc_operating_point,
    run_transient_analysis,
)

app = Flask(__name__)


@app.context_processor
def inject_provenance():
    """ให้ template แสดง model ที่ใช้จริงได้ทุกหน้า (ไม่ hard-code ใน HTML)"""
    return {"spice_model": BJT_MODEL, "analysis_labels": ANALYSIS_LABELS}

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
DEFAULT_ANALYSIS = "analytical"
ANALYSIS_LABELS = {
    "analytical": "Analytical DC Bias (Lab 3)",
    "spice_dc": "SPICE DC · .op",
    "spice_ac": "SPICE AC · .ac",
    "spice_tran": "SPICE Transient · .tran",
}
SPICE_FIELDS = ("vcc", "r1", "r2", "rc", "re")

RESISTOR_FIELDS = ("r1", "r2", "rc", "re", "rb", "rl")
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
    "rl": "10",
    "cin": "10",
    "cout": "10",
    "amplitude": "0.01",
    "frequency": "1",
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


def spice_parameters(values: dict) -> dict:
    """เฉพาะพารามิเตอร์ที่ netlist ใช้ (ค่าที่แปลงเป็น SI แล้วจาก parse_form)"""
    return {name: values[name] for name in SPICE_FIELDS}


def parse_spice_extra(form) -> dict:
    """แปลงพารามิเตอร์ AC/Transient จากหน่วยในฟอร์มเป็น SI."""
    values = {}
    invalid = []
    for name in ("rl", "cin", "cout", "amplitude", "frequency"):
        raw = (form.get(name) or "").strip()
        try:
            values[name] = float(raw)
        except ValueError:
            invalid.append(f'{name} ("{raw}")')
            continue
        if not math.isfinite(values[name]) or values[name] <= 0:
            invalid.append(f'{name} ("{raw}") ต้องมากกว่า 0 และเป็นจำนวนจำกัด')
    if invalid:
        raise ValueError("พารามิเตอร์ SPICE ไม่ถูกต้อง: " + ", ".join(invalid))

    # จุดเดียวของการแปลงหน่วย: kΩ→Ω, µF→F, kHz→Hz
    values["rl"] *= KILO
    values["cin"] *= 1e-6
    values["cout"] *= 1e-6
    values["frequency"] *= 1e3
    return values


def make_plot(
    series: list, x_log: bool, y2: bool = False, key: str = "y",
    y_label: str | None = None, legend: str | None = None,
) -> dict | None:
    """สร้างพิกัด SVG จากข้อมูล ngspice จริง — ไม่มีการ hard-code กราฟ"""
    if not series:
        return None

    width, height = 760, 260
    left, right, top, bottom = 56, 18, 18, 38
    plot_w, plot_h = width - left - right, height - top - bottom

    xs = [math.log10(p["x"]) if x_log else p["x"] for p in series]
    ys = [p[key] for p in series]
    all_y = ys + ([p["y2"] for p in series] if y2 else [])
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(all_y), max(all_y)
    if x_max == x_min:
        x_max = x_min + 1
    if y_max == y_min:
        y_min -= 1
        y_max += 1
    y_pad = (y_max - y_min) * 0.08
    y_min, y_max = y_min - y_pad, y_max + y_pad

    def px(x: float) -> float:
        return left + (x - x_min) / (x_max - x_min) * plot_w

    def py(y: float) -> float:
        return top + (y_max - y) / (y_max - y_min) * plot_h

    def path(points: list, key: str) -> str:
        # <polyline points> ต้องเป็น "x,y x,y ..." — คำสั่ง M/L เป็นของ <path>
        return " ".join(
            f"{px(v):.2f},{py(p[key]):.2f}"
            for v, p in zip(points, series)
        )

    x_ticks = []
    for i in range(5):
        x_val = x_min + (x_max - x_min) * i / 4
        label = f"1e{x_val:.1f}" if x_log else f"{x_val:.3g}"
        x_ticks.append((round(px(x_val), 2), label))
    y_ticks = [
        (round(py(y_val), 2), f"{y_val:.2f}")
        for y_val in (y_min + (y_max - y_min) * i / 4 for i in range(5))
    ]

    return {
        "path_main": path(xs, key),
        "path_second": path(xs, "y2") if y2 else None,
        "x_ticks": x_ticks,
        "y_ticks": y_ticks,
        "x_label": "Frequency (Hz, log10)" if x_log else "Time (ms)",
        "y_label": y_label or ("Gain (dB)" if not y2 else "Voltage (V)"),
        "left": left, "top": top, "width": width, "height": height,
        "plot_w": round(plot_w, 2), "plot_h": round(plot_h, 2),
        "legend_main": legend or ("Gain (dB)" if not y2 else "Vout"),
        "legend_second": "Vin" if y2 else None,
        "points": len(series),
    }


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        analysis = (request.form.get("analysis") or DEFAULT_ANALYSIS).strip()
        mode = (request.form.get("mode") or DEFAULT_MODE).strip()

        if analysis not in ANALYSIS_LABELS:
            return render_template(
                "index.html",
                values=request.form,
                analysis=analysis,
                mode=mode,
                ohms=converted_ohms(request.form, RESISTOR_FIELDS),
                errors=[f'การวิเคราะห์ไม่รู้จัก "{analysis}" — เลือก Analytical หรือ SPICE'],
            )

        # --- SPICE DC: วงจร CE Voltage Divider อ้างอิง ---
        if analysis == "spice_dc":
            mode = "divider"
            try:
                values = parse_form(request.form, mode)
                analytical = CALCULATORS[mode](**values)
                spice = run_dc_operating_point(spice_parameters(values))
            except (ValueError, SpiceError) as exc:
                # ไม่ส่ง spice/display → ไม่มีกราฟ/ผลเก่าค้างพร้อมข้อความสำเร็จ
                return render_template(
                    "index.html",
                    values=request.form,
                    analysis=analysis,
                    mode=mode,
                    button_label="Run DC Simulation",
                    ohms=converted_ohms(request.form, MODE_FIELDS[mode] + ("rl",)),
                    errors=[f"[SPICE DC] {exc}"],
                )

            return render_template(
                "index.html",
                values=request.form,
                analysis=analysis,
                mode=mode,
                button_label="Run DC Simulation",
                ohms=converted_ohms(request.form, MODE_FIELDS[mode] + ("rl",)),
                spice=spice,
                analytical_display=describe(analytical, mode),
                warnings=analytical.warnings,
            )

        # --- SPICE AC / Transient: วงจร CE Voltage Divider อ้างอิงตัวเดียว ---
        if analysis in ("spice_ac", "spice_tran"):
            mode = "divider"
            button_label = (
                "Run AC Simulation" if analysis == "spice_ac"
                else "Run Transient Simulation"
            )
            try:
                values = parse_form(request.form, mode)
                extra = parse_spice_extra(request.form)
                analytical = CALCULATORS[mode](**values)
                params = {**spice_parameters(values), **extra}
                spice = (
                    run_ac_analysis(params) if analysis == "spice_ac"
                    else run_transient_analysis(params)
                )
            except (ValueError, SpiceError) as exc:
                # ไม่ส่ง spice/plot → ไม่มีกราฟหรือผลเก่าค้างกับข้อความผิดพลาด
                return render_template(
                    "index.html",
                    values=request.form,
                    analysis=analysis,
                    mode=mode,
                    button_label=button_label,
                    ohms=converted_ohms(request.form, RESISTOR_FIELDS),
                    errors=[f"[{ANALYSIS_LABELS[analysis]}] {exc}"],
                )

            return render_template(
                "index.html",
                values=request.form,
                analysis=analysis,
                mode=mode,
                button_label=button_label,
                ohms=converted_ohms(request.form, RESISTOR_FIELDS),
                spice=spice,
                analytical_display=describe(analytical, mode),
                warnings=analytical.warnings,
                plot=make_plot(
                    spice["series"],
                    x_log=(analysis == "spice_ac"),
                    y2=(analysis == "spice_tran"),
                ),
                phase_plot=(
                    make_plot(
                        spice["series"], x_log=True,
                        key="phase", y_label="Phase (degree)", legend="Phase",
                    )
                    if analysis == "spice_ac" else None
                ),
            )

        # --- Analytical DC Bias จาก Lab 3 (คงพฤติกรรมเดิมทุกประการ) ---
        if mode not in MODE_FIELDS:
            return render_template(
                "index.html",
                values=request.form,
                analysis=analysis,
                mode=mode,
                ohms=converted_ohms(request.form, RESISTOR_FIELDS),
                errors=[f'โหมดไม่รู้จัก "{mode}" — เลือก Voltage Divider, Fixed หรือ Emitter Bias'],
            )

        try:
            values = parse_form(request.form, mode)
            result = CALCULATORS[mode](**values)
        except ValueError as exc:
            return render_template(
                "index.html",
                values=request.form,
                analysis=analysis,
                mode=mode,
                ohms=converted_ohms(request.form, MODE_FIELDS[mode]),
                errors=[f"[{MODE_LABELS[mode]}] {exc}"],
            )

        return render_template(
            "index.html",
            values=request.form,
            analysis=analysis,
            mode=mode,
            ohms=converted_ohms(request.form, MODE_FIELDS[mode]),
            result=result,
            display=describe(result, mode),
            warnings=result.warnings,
        )

    return render_template(
        "index.html",
        values=DEFAULTS,
        analysis=DEFAULT_ANALYSIS,
        mode=DEFAULT_MODE,
        ohms=converted_ohms(DEFAULTS, MODE_FIELDS[DEFAULT_MODE]),
    )


if __name__ == "__main__":
    app.run(debug=True)
