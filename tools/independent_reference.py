"""Independent reference values for Lab 3 acceptance cases A1–A5.

This script deliberately does NOT import ``dc_bias`` or ``app``. It solves
for IE first (instead of IB) with ``decimal.Decimal`` at 50 digits, so it is
an independent check of the equations used by the web application.

Run with:

    .venv\\Scripts\\python.exe tools\\independent_reference.py
"""

from decimal import Decimal as D, getcontext

getcontext().prec = 50

VCC = D(12)
RC = D(2200)          # 2.2 kΩ in Ω
BETA = D(100)
VBE = D("0.70")
RB_1M = D(1_000_000)  # 1 MΩ in Ω


def report(case: str, ib: D, ve: D, *, vth: D | None = None, rth: D | None = None) -> None:
    """Print full-precision operating point in the units used by the form."""
    ic = BETA * ib
    ie = (BETA + 1) * ib
    vc = VCC - ic * RC
    vce = vc - ve
    fmt = lambda x: f"{float(x):.9f}"
    extras = ""
    if vth is not None and rth is not None:
        extras = f" VTH={fmt(vth)} V RTH={fmt(rth / D(1000))} kohm"
    print(
        f"{case}: IB={fmt(ib * D(10**6))} uA IC={fmt(ic * D(1000))} mA "
        f"IE={fmt(ie * D(1000))} mA VE={fmt(ve)} V VB={fmt(ve + VBE)} V "
        f"VC={fmt(vc)} V VCE={fmt(vce)} V{extras}"
    )


def main() -> None:
    # A1 · Voltage Divider — IE is the unknown here, not IB.
    r1, r2, re = D(100_000), D(22_000), D(1_000)
    vth = VCC * r2 / (r1 + r2)
    rth = r1 * r2 / (r1 + r2)
    ie = (vth - VBE) / (rth / (BETA + 1) + re)
    report("A1 Divider ", ie / (BETA + 1), ie * re, vth=vth, rth=rth)

    # A2 · Fixed Bias: emitter grounded, no RE term in the base loop.
    ib = (VCC - VBE) / RB_1M
    report("A2 Fixed   ", ib, D(0))

    # A3 · Emitter Bias with RE = 1 kΩ.
    re = D(1_000)
    ib = (VCC - VBE) / (RB_1M + (BETA + 1) * re)
    report("A3 Emitter ", ib, (BETA + 1) * ib * re)

    # A4 · Emitter Bias with RE = 2 kΩ (only RE changes from A3).
    re = D(2_000)
    ib = (VCC - VBE) / (RB_1M + (BETA + 1) * re)
    report("A4 Emitter ", ib, (BETA + 1) * ib * re)

    print("A5 Fixed RB=0 -> RB must be > 0 ohm, so the form must reject it.")


if __name__ == "__main__":
    main()
