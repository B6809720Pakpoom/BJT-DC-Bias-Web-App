"""Lab 3 — tests for the two new bias modes.

Run the RED step before implementing the functions in dc_bias.py:

    .venv\\Scripts\\python.exe -m unittest tests.test_bias_modes -v
"""

import unittest

from dc_bias import calculate_emitter_bias, calculate_fixed_bias

REL_TOL = 1e-7

# Independent values from tools/independent_reference.py (Decimal, 50 digits).
A2 = dict(ib=11.3e-6, ic=1.13e-3, ie=1.1413e-3,
          vb=0.70, ve=0.0, vc=9.514, vce=9.514)
A3 = dict(ib=10.263396912e-6, ic=1.026339691e-3, ie=1.036603088e-3,
          vb=1.736603088, ve=1.036603088, vc=9.742052679, vce=8.705449591)
A4 = dict(ib=9.400998336e-6, ic=0.940099834e-3, ie=0.949500832e-3,
          vb=2.599001664, ve=1.899001664, vc=9.931780366, vce=8.032778702)

COMMON = dict(vcc=12.0, rc=2_200.0, beta=100.0, vbe=0.70)
RB_1M = 1_000_000.0


class BiasModesMixin:
    def assertOperatingPoint(self, result, expected):
        for key, value in expected.items():
            with self.subTest(key=key):
                self.assertAlmostEqual(
                    getattr(result, key), value, delta=abs(value) * REL_TOL
                )
        self.assertEqual(result.region, "active")
        self.assertEqual(result.warnings, ())
        self.assertIsNone(result.vth)
        self.assertIsNone(result.rth)


class FixedBias(BiasModesMixin, unittest.TestCase):
    def test_A2_matches_independent_reference(self):
        result = calculate_fixed_bias(rb=RB_1M, **COMMON)
        self.assertOperatingPoint(result, A2)

    def test_rejects_zero_rb(self):
        with self.assertRaises(ValueError):
            calculate_fixed_bias(rb=0.0, **COMMON)

    def test_rejects_negative_and_non_finite_rb(self):
        for rb in (-1.0, float("nan"), float("inf")):
            with self.subTest(rb=rb):
                with self.assertRaises(ValueError):
                    calculate_fixed_bias(rb=rb, **COMMON)

    def test_rejects_non_finite_common_inputs(self):
        for key in COMMON:
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    calculate_fixed_bias(rb=RB_1M, **{**COMMON, key: float("inf")})

    def test_result_as_dict_uses_agreed_keys_and_units(self):
        as_dict = calculate_fixed_bias(rb=RB_1M, **COMMON).as_dict()
        for key in ("vb_v", "ve_v", "vc_v", "vce_v", "ic_ma", "ib_ua", "region"):
            self.assertIn(key, as_dict)
        self.assertAlmostEqual(as_dict["ic_ma"], 1.13, places=6)
        self.assertAlmostEqual(as_dict["vce_v"], 9.514, places=6)


class EmitterBias(BiasModesMixin, unittest.TestCase):
    def test_A3_matches_independent_reference(self):
        result = calculate_emitter_bias(rb=RB_1M, re=1_000.0, **COMMON)
        self.assertOperatingPoint(result, A3)

    def test_A4_matches_independent_reference(self):
        result = calculate_emitter_bias(rb=RB_1M, re=2_000.0, **COMMON)
        self.assertOperatingPoint(result, A4)

    def test_increasing_re_reduces_ic(self):
        small = calculate_emitter_bias(rb=RB_1M, re=1_000.0, **COMMON)
        large = calculate_emitter_bias(rb=RB_1M, re=2_000.0, **COMMON)
        self.assertLess(large.ic, small.ic)

    def test_rejects_non_positive_re(self):
        for re in (0.0, -1.0):
            with self.subTest(re=re):
                with self.assertRaises(ValueError):
                    calculate_emitter_bias(rb=RB_1M, re=re, **COMMON)

    def test_warns_when_model_is_not_forward_active(self):
        result = calculate_emitter_bias(
            vcc=12.0, rb=100_000.0, re=1_000.0,
            rc=15_000.0, beta=100.0, vbe=0.70,
        )
        self.assertEqual(result.region, "saturation")
        self.assertTrue(result.warnings)


if __name__ == "__main__":
    unittest.main()
