"""ngspice adapter for the Lab 4 CE amplifier simulator.

This module owns everything SPICE-related: building the netlist, invoking the
external ngspice executable, and parsing its raw output.  Flask code in
``app.py`` only validates form input and displays the structured result.

No value in this module is invented: every number returned here comes from a
real ngspice run (``.op``, ``.ac`` or ``.tran``).
"""

from __future__ import annotations

import math
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

TIMEOUT_SECONDS = 60

# Instructor starter kit was not supplied, so the lab uses this explicit,
# documented model.  BF=100 and VAF=0 match the Lab 3 assumptions (constant
# beta, no Early effect); IS is chosen so VBE is about 0.70 V near 1 mA.
BJT_MODEL = "QNPN NPN(IS=2e-15 BF=100 VAF=0 CJE=10p CJC=5p TF=0.3n)"
MODEL_NAME = BJT_MODEL.split()[0]
ENGINE_LABEL = "ngspice"

BASE_FIELDS = ("vcc", "r1", "r2", "rc", "re")
EXTRA_FIELDS = ("rl", "cin", "cout", "amplitude", "frequency")


class SpiceError(RuntimeError):
    """Raised when ngspice is unavailable, fails, or returns unusable data."""


def find_engine() -> str:
    """Return the ngspice console executable available on PATH."""
    for name in ("ngspice_con", "ngspice_con.exe", "ngspice", "ngspice.exe"):
        found = shutil.which(name)
        if found:
            return found

    # Fallback for this lab machine: installer-free 7z extraction.
    home = Path(os.path.expanduser("~"))
    candidates = [
        home / "AppData/Local/Programs/ngspice-47/Spice64/bin/ngspice_con.exe",
        Path("C:/Spice64/bin/ngspice_con.exe"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)

    raise SpiceError(
        "ไม่พบ ngspice ใน PATH — ตรวจการติดตั้งและเพิ่ม ngspice\\Spice64\\bin ลง PATH ก่อนรัน"
    )


def engine_version(executable: str | None = None) -> str:
    """Return a short version string for display in the Results panel."""
    exe = executable or find_engine()
    try:
        proc = subprocess.run(
            [exe, "--version"], capture_output=True, text=True, timeout=10
        )
    except (OSError, subprocess.SubprocessError):
        return ENGINE_LABEL
    for line in proc.stdout.splitlines():
        if "ngspice-" in line:
            return line.strip().split(" : ")[0].lstrip("* ").strip()
    return ENGINE_LABEL


def _validate(params: dict, names: tuple[str, ...]) -> None:
    for name in names:
        value = params.get(name)
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            raise SpiceError(f"พารามิเตอร์ {name} ต้องเป็นตัวเลขที่จำกัด")
        if value <= 0:
            raise SpiceError(f"พารามิเตอร์ {name} ต้องมากกว่า 0 ({name} = {value:g})")


def _amplifier_core(params: dict, source_line: str) -> str:
    """Circuit shared by .ac and .tran: divider-biased CE with coupling caps."""
    return f"""VCC VCC 0 DC {params['vcc']:.6g}
{source_line}
CIN IN BASE {params['cin']:.6g}
R1 VCC BASE {params['r1']:.6g}
R2 BASE 0 {params['r2']:.6g}
RC VCC COL {params['rc']:.6g}
RE EMIT 0 {params['re']:.6g}
Q1 COL BASE EMIT {MODEL_NAME}
.model {BJT_MODEL}
COUT COL OUT {params['cout']:.6g}
RL OUT 0 {params['rl']:.6g}
"""


def build_dc_netlist(params: dict) -> str:
    """Reference CE voltage-divider netlist for a ``.op`` run."""
    return f"""* CE Voltage Divider — Lab 4 DC operating point
VCC VCC 0 DC {params['vcc']:.6g}
R1 VCC BASE {params['r1']:.6g}
R2 BASE 0 {params['r2']:.6g}
RC VCC COL {params['rc']:.6g}
RE EMIT 0 {params['re']:.6g}
Q1 COL BASE EMIT {MODEL_NAME}
.model {BJT_MODEL}
.op
.end
"""


def build_ac_netlist(params: dict) -> str:
    """CE amplifier netlist for a log frequency sweep (AC amplitude = 1)."""
    core = _amplifier_core(params, "VIN IN 0 DC 0 AC 1")
    return f"""* CE Amplifier — Lab 4 AC frequency response
{core}.ac dec 20 10 10Meg
.end
"""


def build_tran_netlist(params: dict) -> str:
    """CE amplifier netlist for five periods of a sine input."""
    frequency = params["frequency"]
    t_stop = 5.0 / frequency
    t_step = 1.0 / (frequency * 200)
    source = (
        f"VIN IN 0 DC 0 SIN(0 {params['amplitude']:.6g} {frequency:.6g})"
    )
    core = _amplifier_core(params, source)
    return f"""* CE Amplifier — Lab 4 transient response
{core}.tran {t_step:.6g} {t_stop:.6g}
.end
"""


def parse_raw(raw_text: str, expected_plot: str) -> tuple[list[str], list[list]]:
    """Parse variables and points from an ngspice raw file.

    AC output is ``Flags: complex`` with ``real,imag`` pairs; DC and transient
    output are plain real numbers.  Both are converted here, never in JS.
    """
    lines = raw_text.splitlines()
    if not any(line.startswith(f"Plotname: {expected_plot}") for line in lines):
        raise SpiceError(f"ngspice ไม่ได้เขียน {expected_plot} ลงในไฟล์ raw")

    flags = next(
        (line.split(":", 1)[1].strip() for line in lines if line.startswith("Flags:")),
        "",
    )
    is_complex = "complex" in flags

    try:
        var_start = next(i for i, line in enumerate(lines) if line.strip() == "Variables:")
        val_start = next(i for i, line in enumerate(lines) if line.strip() == "Values:")
    except StopIteration as exc:
        raise SpiceError("รูปแบบไฟล์ raw ไม่ถูกต้อง (ไม่มี Variables/Values)") from exc

    variables = []
    for line in lines[var_start + 1:val_start]:
        parts = line.split()
        if len(parts) >= 3:
            variables.append(parts[1])
    if not variables:
        raise SpiceError("ไฟล์ raw ไม่มีรายการตัวแปร")

    # ngspice writes the point index only on the first line of each point;
    # the remaining values of that point are on unindexed continuation lines.
    points: list[list] = []
    for line in lines[val_start + 1:]:
        parts = line.split()
        if not parts:
            continue
        if parts[0].isdigit():
            points.append([])
            values = parts[1:]
        else:
            if not points:
                raise SpiceError("รูปแบบไฟล์ raw ไม่ถูกต้อง ( Values ไม่มีจุดข้อมูล)")
            values = parts

        for token in values:
            try:
                if is_complex:
                    real, imag = token.split(",")
                    points[-1].append(complex(float(real), float(imag)))
                else:
                    points[-1].append(float(token))
            except ValueError as exc:
                raise SpiceError(f"อ่านค่าจาก raw ไม่ได้: {token}") from exc

    if not points:
        raise SpiceError("ไฟล์ raw ไม่มีข้อมูลผลลัพธ์")
    if any(len(row) != len(variables) for row in points):
        raise SpiceError("จำนวนค่าในไฟล์ raw ไม่ตรงกับจำนวนตัวแปร")
    return variables, points


def _raw_index(variables: list[str], name: str) -> int:
    try:
        return variables.index(name)
    except ValueError as exc:
        raise SpiceError(f"ไม่พบตัวแปร {name} ในผลลัพธ์ ngspice") from exc


def _downsample(series: list, limit: int) -> list:
    if len(series) <= limit:
        return series
    step = math.ceil(len(series) / limit)
    return series[::step]


def _execute(netlist: str, prefix: str, plotname: str) -> tuple[list[str], list[list], str]:
    """Write a netlist, run ngspice in batch mode, and parse its raw output."""
    executable = find_engine()
    with tempfile.TemporaryDirectory(prefix=prefix) as tmp:
        workdir = Path(tmp)
        cir_path = workdir / "circuit.cir"
        log_path = workdir / "run.log"
        raw_path = workdir / "run.raw"
        cir_path.write_text(netlist, encoding="utf-8")

        try:
            proc = subprocess.run(
                [
                    executable,
                    "-b",
                    "-o", str(log_path),
                    "-r", str(raw_path),
                    str(cir_path),
                ],
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise SpiceError(f"ngspice ใช้เวลาเกิน {TIMEOUT_SECONDS} วินาที (timeout)") from exc

        log_tail = ""
        if log_path.exists():
            log_tail = "\n".join(
                log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-12:]
            )
        if proc.returncode != 0:
            message = (proc.stderr or log_tail or proc.stdout or "").strip()
            raise SpiceError(
                f"ngspice run ไม่สำเร็จ (exit {proc.returncode}): {message[-600:]}"
            )
        if not raw_path.exists():
            raise SpiceError("ngspice ไม่ได้สร้างไฟล์ run.raw")

        variables, points = parse_raw(
            raw_path.read_text(encoding="utf-8", errors="replace"), plotname
        )
    return variables, points, log_tail


def _envelope(engine: str, analysis: str, netlist: str, rows: list, log_tail: str, series: list) -> dict:
    return {
        "status": "success",
        "engine": f"{ENGINE_LABEL} · {engine_version()}",
        "model": BJT_MODEL,
        "analysis": analysis,
        "rows": rows,
        "series": series,
        "netlist": netlist.strip(),
        "log_tail": log_tail,
    }


def run_dc_operating_point(params: dict) -> dict:
    """Run a real ngspice ``.op`` simulation and return structured results."""
    _validate(params, BASE_FIELDS)
    netlist = build_dc_netlist(params)
    variables, points, log_tail = _execute(netlist, "ngspice-dc-", "Operating Point")
    vectors = dict(zip(variables, points[0]))

    def node(name: str) -> float:
        key = f"v({name})"
        if key not in vectors:
            raise SpiceError(f"ไม่พบโหนด {key} ในผลลัพธ์ ngspice")
        return float(vectors[key])

    vb, ve, vc, vcc = node("base"), node("emit"), node("col"), node("vcc")
    ic = (vcc - vc) / params["rc"]
    vce = vc - ve

    rows = [
        ("VB", f"{vb:.3f}", "V"),
        ("VE", f"{ve:.3f}", "V"),
        ("VC", f"{vc:.3f}", "V"),
        ("VCE", f"{vce:.3f}", "V"),
        ("IC", f"{ic * 1e3:.3f}", "mA"),
    ]
    return _envelope(
        "dc",
        "DC Operating Point (.op)",
        netlist,
        rows,
        log_tail,
        [],
    )


def run_ac_analysis(params: dict) -> dict:
    """Run a real ngspice ``.ac`` sweep and return gain vs frequency."""
    _validate(params, BASE_FIELDS + ("rl", "cin", "cout"))
    netlist = build_ac_netlist(params)
    variables, points, log_tail = _execute(netlist, "ngspice-ac-", "AC Analysis")

    f_i = _raw_index(variables, "frequency")
    vin_i = _raw_index(variables, "v(in)")
    vout_i = _raw_index(variables, "v(out)")

    series = []
    for row in points:
        frequency = float(row[f_i].real)
        vin, vout = complex(row[vin_i]), complex(row[vout_i])
        if vin == 0 or frequency <= 0:
            continue
        gain = abs(vout / vin)
        series.append({
            "x": frequency,
            "y": 20 * math.log10(gain) if gain > 0 else -400.0,
            "unit_x": "Hz",
            "unit_y": "dB",
        })
    if not series:
        raise SpiceError("ngspice ไม่ได้ส่งข้อมูล AC ที่ใช้คำนวณ gain ได้")

    plotted = _downsample(series, 240)
    peak = max(series, key=lambda point: point["y"])
    rows = [
        ("Frequency sweep", f"{series[0]['x']:.0f} – {series[-1]['x']:.0f}", "Hz"),
        ("Data points", str(len(series)), "points"),
        ("Peak gain", f"{peak['y']:.2f}", "dB"),
        ("Peak at", f"{peak['x']:.0f}", "Hz"),
    ]
    return _envelope("ac", "AC Frequency Response (.ac)", netlist, rows, log_tail, plotted)


def run_transient_analysis(params: dict) -> dict:
    """Run a real ngspice ``.tran`` simulation and return input/output waveforms."""
    _validate(params, BASE_FIELDS + ("rl", "cin", "cout", "amplitude", "frequency"))
    netlist = build_tran_netlist(params)
    variables, points, log_tail = _execute(netlist, "ngspice-tran-", "Transient Analysis")

    t_i = _raw_index(variables, "time")
    vin_i = _raw_index(variables, "v(in)")
    vout_i = _raw_index(variables, "v(out)")

    series = [{
        "x": float(row[t_i]) * 1e3,
        "y": float(row[vout_i].real) if isinstance(row[vout_i], complex) else float(row[vout_i]),
        "y2": float(row[vin_i].real) if isinstance(row[vin_i], complex) else float(row[vin_i]),
        "unit_x": "ms",
        "unit_y": "V",
    } for row in points]
    if not series:
        raise SpiceError("ngspice ไม่ได้ส่งข้อมูล transient")

    outputs = [point["y"] for point in series]
    rows = [
        ("Vin amplitude", f"{params['amplitude'] * 1e3:.1f}", "mV peak"),
        ("Input frequency", f"{params['frequency'] / 1e3:.3f}", "kHz"),
        ("Vout min", f"{min(outputs):.3f}", "V"),
        ("Vout max", f"{max(outputs):.3f}", "V"),
        ("Simulation time", f"{series[-1]['x']:.3f}", "ms"),
    ]
    return _envelope(
        "tran", "Transient Response (.tran)", netlist, rows, log_tail,
        _downsample(series, 600),
    )
