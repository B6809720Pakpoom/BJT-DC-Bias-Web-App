"""BJT DC bias calculations (forward-active model).

All inputs and outputs are in SI units: volts, ohms, amperes.
This module knows nothing about HTTP, Flask, or HTML on purpose:
the UI layer is responsible for converting kΩ to Ω before calling in.

Three circuits share one result shape:

* ``calculate_dc_bias``     — voltage-divider bias (Lab 2, unchanged)
* ``calculate_fixed_bias``  — fixed bias with RB from VCC to base (Lab 3)
* ``calculate_emitter_bias`` — RB to base plus RE from emitter to ground (Lab 3)
"""

from __future__ import annotations

import math
from dataclasses import dataclass

SATURATION_MARGIN_V = 0.3


@dataclass(frozen=True)
class DcBiasResult:
    """DC operating point shared by all three bias circuits.

    ``vth`` and ``rth`` exist only for the voltage-divider circuit. The other
    modes leave them as ``None`` so the UI can omit those two rows instead of
    showing made-up numbers.
    """

    ib: float
    ic: float
    ie: float
    vb: float
    ve: float
    vc: float
    vce: float
    region: str
    warnings: tuple[str, ...]
    vth: float | None = None
    rth: float | None = None

    def as_dict(self) -> dict:
        """Agreed Lab 3 key names and units for review by Flask / the student."""
        return {
            "ib_a": self.ib,
            "ic_a": self.ic,
            "ie_a": self.ie,
            "ib_ua": self.ib * 1e6,
            "ic_ma": self.ic * 1e3,
            "ie_ma": self.ie * 1e3,
            "vb_v": self.vb,
            "ve_v": self.ve,
            "vc_v": self.vc,
            "vce_v": self.vce,
            "vth_v": self.vth,
            "rth_ohm": self.rth,
            "region": self.region,
            "warnings": list(self.warnings),
        }


def _check_finite(**named: float) -> None:
    for name, value in named.items():
        if not math.isfinite(value):
            raise ValueError(
                f"{name} ต้องเป็นจำนวนจำกัด (finite) — พบค่า {value!r}"
            )


def _validate_common(vcc: float, rc: float, beta: float, vbe: float) -> None:
    """Validation shared by all three circuits (VCC, RC, β, VBE)."""
    if vcc <= 0:
        raise ValueError("VCC ต้องมากกว่า 0 V")
    if rc <= 0:
        raise ValueError(f"ค่าความต้านทานต้องมากกว่า 0 Ω (พบ RC = {rc:g} Ω)")
    if beta <= 0:
        raise ValueError(f"β ต้องมากกว่า 0 (พบ β = {beta:g})")
    if vbe < 0 or vbe >= vcc:
        raise ValueError(
            f"VBE ต้องอยู่ระหว่าง 0 และ VCC (พบ VBE = {vbe:g} V, VCC = {vcc:g} V)"
        )


def _validate_resistors(**named: float) -> None:
    """Extra resistors required by the selected circuit (R1, R2, RE, RB)."""
    for name, value in named.items():
        if value <= 0:
            raise ValueError(f"ค่าความต้านทานต้องมากกว่า 0 Ω (พบ {name} = {value:g} Ω)")


def _check_outputs(**values: float) -> None:
    """กันผลลัพธ์ล้นเป็น inf/nan แม้อินพุตทุกตัวจะเป็นจำนวนจำกัด"""
    for name, value in values.items():
        if not math.isfinite(value):
            raise ValueError(
                f"ผลลัพธ์ล้นช่วงตัวเลข ({name} = {value!r}) — กรุณาลดขนาดค่าอินพุต"
            )


def _operating_point(
    vcc: float,
    rc: float,
    re: float,
    beta: float,
    vbe: float,
    ib: float,
    *,
    vth: float | None = None,
    rth: float | None = None,
) -> DcBiasResult:
    """Finish the DC operating point from an already-solved base current."""
    if ib <= 0:
        _check_outputs(vce=vcc)
        return DcBiasResult(
            ib=0.0,
            ic=0.0,
            ie=0.0,
            vb=vbe,
            ve=0.0,
            vc=vcc,
            vce=vcc,
            region="cutoff",
            warnings=(
                f"IB ที่คำนวณได้ ({ib:.3g} A) ≤ 0 → ทรานซิสเตอร์อยู่ใน cutoff "
                "แบบจำลอง forward-active ใช้ไม่ได้ กระแสทุกตัวเป็นศูนย์",
            ),
            vth=vth,
            rth=rth,
        )

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
        ib=ib,
        ic=ic,
        ie=ie,
        vb=vb,
        ve=ve,
        vc=vc,
        vce=vce,
        region=region,
        warnings=warnings,
        vth=vth,
        rth=rth,
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
    """Voltage-divider bias — Lab 2 behaviour is intentionally preserved."""
    _check_finite(VCC=vcc, R1=r1, R2=r2, RC=rc, RE=re, β=beta, VBE=vbe)
    _validate_common(vcc, rc, beta, vbe)
    _validate_resistors(R1=r1, R2=r2, RE=re)

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
            ib=0.0,
            ic=0.0,
            ie=0.0,
            vb=vth,
            ve=0.0,
            vc=vcc,
            vce=vcc,
            region="cutoff",
            warnings=warnings,
            vth=vth,
            rth=rth,
        )

    ib = (vth - vbe) / (rth + (beta + 1) * re)
    return _operating_point(
        vcc, rc, re, beta, vbe, ib, vth=vth, rth=rth
    )


def calculate_fixed_bias(
    vcc: float,
    rb: float,
    rc: float,
    beta: float,
    vbe: float,
) -> DcBiasResult:
    """Fixed bias: RB from VCC to base, emitter tied directly to ground.

    IB = (VCC − VBE) / RB; VE = 0.
    """
    _check_finite(VCC=vcc, RB=rb, RC=rc, β=beta, VBE=vbe)
    _validate_common(vcc, rc, beta, vbe)
    _validate_resistors(RB=rb)

    ib = (vcc - vbe) / rb
    return _operating_point(vcc, rc, 0.0, beta, vbe, ib)


def calculate_emitter_bias(
    vcc: float,
    rb: float,
    rc: float,
    re: float,
    beta: float,
    vbe: float,
) -> DcBiasResult:
    """Emitter bias with a single supply: RB to base, RE from emitter to ground.

    IB = (VCC − VBE) / [RB + (β + 1)·RE]; VE = IE·RE.
    """
    _check_finite(VCC=vcc, RB=rb, RC=rc, RE=re, β=beta, VBE=vbe)
    _validate_common(vcc, rc, beta, vbe)
    _validate_resistors(RB=rb, RE=re)

    ib = (vcc - vbe) / (rb + (beta + 1) * re)
    return _operating_point(vcc, rc, re, beta, vbe, ib)
