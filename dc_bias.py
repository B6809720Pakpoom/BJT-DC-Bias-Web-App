"""BJT DC bias calculations (voltage-divider bias, forward-active model).

All inputs and outputs are in SI units: volts, ohms, amperes.
This module knows nothing about HTTP, Flask, or HTML on purpose:
the UI layer is responsible for converting kΩ to Ω before calling in.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

SATURATION_MARGIN_V = 0.3


@dataclass(frozen=True)
class DcBiasResult:
    """DC operating point of a voltage-divider biased BJT."""

    vth: float
    rth: float
    ib: float
    ic: float
    ie: float
    vb: float
    ve: float
    vc: float
    vce: float
    region: str
    warnings: tuple[str, ...]


def _validate(
    vcc: float,
    r1: float,
    r2: float,
    rc: float,
    re: float,
    beta: float,
    vbe: float,
) -> None:
    named = {
        "VCC": vcc,
        "R1": r1,
        "R2": r2,
        "RC": rc,
        "RE": re,
        "β": beta,
        "VBE": vbe,
    }
    for name, value in named.items():
        if not math.isfinite(value):
            raise ValueError(
                f"{name} ต้องเป็นจำนวนจำกัด (finite) — พบค่า {value!r}"
            )

    if vcc <= 0:
        raise ValueError("VCC ต้องมากกว่า 0 V")
    for name, value in (("R1", r1), ("R2", r2), ("RC", rc), ("RE", re)):
        if value <= 0:
            raise ValueError(f"ค่าความต้านทานต้องมากกว่า 0 Ω (พบ {name} = {value:g} Ω)")
    if beta <= 0:
        raise ValueError(f"β ต้องมากกว่า 0 (พบ β = {beta:g})")
    if vbe < 0 or vbe >= vcc:
        raise ValueError(
            f"VBE ต้องอยู่ระหว่าง 0 และ VCC (พบ VBE = {vbe:g} V, VCC = {vcc:g} V)"
        )


def _check_outputs(**values: float) -> None:
    """กันผลลัพธ์ล้นเป็น inf/nan แม้อินพุตทุกตัวจะเป็นจำนวนจำกัด"""
    for name, value in values.items():
        if not math.isfinite(value):
            raise ValueError(
                f"ผลลัพธ์ล้นช่วงตัวเลข ({name} = {value!r}) — กรุณาลดขนาดค่าอินพุต"
            )


def calculate_dc_bias(
    vcc: float,
    r1: float,
    r2: float,
    rc: float,
    re: float,
    beta: float,
    vbe: float,
) -> DcBiasResult:
    """Return the DC operating point for the given SI-unit inputs."""
    _validate(vcc, r1, r2, rc, re, beta, vbe)

    vth = vcc * r2 / (r1 + r2)
    rth = r1 * r2 / (r1 + r2)

    if vth <= vbe:
        # ไม่มีกระแสไหล → ไม่มีแรงดันตกคร่อม RC หรือ RE → VC = VCC, VE = 0, VCE = VCC
        _check_outputs(vth=vth, rth=rth, vce=vcc)
        warnings = (
            f"VTH ({vth:.3f} V) ≤ VBE ({vbe:.3f} V) → ทรานซิสเตอร์อยู่ใน cutoff "
            "แบบจำลอง forward-active ใช้ไม่ได้ กระแสทุกตัวเป็นศูนย์",
        )
        return DcBiasResult(
            vth=vth,
            rth=rth,
            ib=0.0,
            ic=0.0,
            ie=0.0,
            vb=vth,
            ve=0.0,
            vc=vcc,
            vce=vcc,
            region="cutoff",
            warnings=warnings,
        )

    ib = (vth - vbe) / (rth + (beta + 1) * re)
    ic = beta * ib
    ie = (beta + 1) * ib

    ve = ie * re
    vb = ve + vbe
    vc = vcc - ic * rc
    vce = vc - ve

    _check_outputs(ib=ib, ic=ic, ie=ie, vb=vb, ve=ve, vc=vc, vce=vce)

    if vce <= SATURATION_MARGIN_V:
        region = "saturation"
        warnings = (
            f"VCE ({vce:.3f} V) ≤ {SATURATION_MARGIN_V} V → ใกล้/อยู่ใน saturation "
            "ค่า VCE ที่คำนวณได้ไม่น่าเชื่อถือ",
        )
    else:
        region = "active"
        warnings = ()

    return DcBiasResult(
        vth=vth,
        rth=rth,
        ib=ib,
        ic=ic,
        ie=ie,
        vb=vb,
        ve=ve,
        vc=vc,
        vce=vce,
        region=region,
        warnings=warnings,
    )
