"""BJT DC bias calculations (voltage-divider bias, forward-active model).

All inputs and outputs are in SI units: volts, ohms, amperes.
This module knows nothing about HTTP, Flask, or HTML on purpose:
the UI layer is responsible for converting kΩ to Ω before calling in.
"""

from __future__ import annotations

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


def _validate(vcc, r1, r2, rc, re, beta, vbe):
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


def calculate_dc_bias(vcc, r1, r2, rc, re, beta, vbe) -> DcBiasResult:
    """Return the DC operating point for the given SI-unit inputs."""
    _validate(vcc, r1, r2, rc, re, beta, vbe)

    vth = vcc * r2 / (r1 + r2)
    rth = r1 * r2 / (r1 + r2)

    ib = (vth - vbe) / (rth + (beta + 1) * re)
    ic = beta * ib
    ie = (beta + 1) * ib

    ve = ie * re
    vb = ve + vbe
    vc = vcc - ic * rc
    vce = vc - ve

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
        region="active",
        warnings=(),
    )
