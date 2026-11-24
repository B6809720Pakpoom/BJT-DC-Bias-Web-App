"""Lab 4 integration tests — ใช้ ngspice จริง ไม่มี mock data."""

import math
import unittest

from spice_engine import (
    SpiceError,
    build_ac_netlist,
    build_dc_netlist,
    build_tran_netlist,
    find_engine,
    run_ac_analysis,
    run_dc_operating_point,
    run_transient_analysis,
)

ENGINE_AVAILABLE = True
try:
    find_engine()
except SpiceError:
    ENGINE_AVAILABLE = False

BASE = dict(vcc=12.0, r1=100_000.0, r2=22_000.0, rc=2_200.0, re=1_000.0)
EXTRA = dict(rl=10_000.0, cin=10e-6, cout=10e-6, amplitude=0.01, frequency=1_000.0)


class NetlistTests(unittest.TestCase):
    def test_dc_netlist_uses_operating_point(self):
        self.assertIn(".op", build_dc_netlist(BASE))
        self.assertIn("Q1 COL BASE EMIT QNPN", build_dc_netlist(BASE))

    def test_ac_netlist_uses_ac_analysis(self):
        netlist = build_ac_netlist({**BASE, **EXTRA})
        self.assertIn(".ac dec", netlist)
        self.assertIn("CIN IN BASE", netlist)
        self.assertIn("RL OUT 0", netlist)

    def test_tran_netlist_uses_sine_source(self):
        netlist = build_tran_netlist({**BASE, **EXTRA})
        self.assertIn(".tran", netlist)
        self.assertIn("SIN(0 0.01 1000)", netlist)

    def test_positive_resistance_required(self):
        with self.assertRaises(SpiceError):
            run_dc_operating_point({**BASE, "r1": 0})


def numeric_row(result, name):
    return float(next(value for label, value, _ in result["rows"] if label == name))


@unittest.skipUnless(ENGINE_AVAILABLE, "ngspice ไม่ได้ติดตั้งบนเครื่องนี้")
class RealNgspiceTests(unittest.TestCase):
    def test_dc_operating_point(self):
        result = run_dc_operating_point(BASE)
        self.assertEqual(result["status"], "success")
        self.assertIn("ngspice", result["engine"])
        self.assertAlmostEqual(numeric_row(result, "VCE"), 8.058, delta=0.05)
        self.assertAlmostEqual(numeric_row(result, "IC"), 1.228, delta=0.02)
        for label in ("VB", "VE", "VC", "VCE", "IC"):
            self.assertTrue(math.isfinite(numeric_row(result, label)))

    def test_ac_gain_changes_with_emitter_resistor(self):
        small = run_ac_analysis({**BASE, **EXTRA, "re": 1_000.0})
        large = run_ac_analysis({**BASE, **EXTRA, "re": 2_000.0})
        self.assertGreater(numeric_row(small, "Peak gain"), numeric_row(large, "Peak gain"))
        self.assertTrue(all(math.isfinite(p["y"]) for p in small["series"]))

    def test_transient_output_scales_with_input_amplitude(self):
        small = run_transient_analysis({**BASE, **EXTRA, "amplitude": 0.01})
        large = run_transient_analysis({**BASE, **EXTRA, "amplitude": 0.03})
        self.assertGreater(numeric_row(large, "Vout max"), numeric_row(small, "Vout max"))
        self.assertTrue(all(math.isfinite(p["y"]) for p in small["series"]))


if __name__ == "__main__":
    unittest.main()
