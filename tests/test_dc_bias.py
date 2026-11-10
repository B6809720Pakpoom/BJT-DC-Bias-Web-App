import unittest

from dc_bias import calculate_dc_bias

TOL = 1e-9


class ReferenceCase(unittest.TestCase):
    def setUp(self):
        self.r = calculate_dc_bias(
            vcc=12.0, r1=100_000.0, r2=22_000.0,
            rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70,
        )

    def assertRel(self, actual, expected):
        self.assertAlmostEqual(actual, expected, delta=abs(expected) * TOL)

    def test_reference_case_matches_independent_calculation(self):
        self.assertRel(self.r.vth, 2.1639344262295084)
        self.assertRel(self.r.rth, 18032.786885245903)
        self.assertRel(self.r.ib, 1.2298581462608458e-05)
        self.assertRel(self.r.ic, 0.0012298581462608458)
        self.assertRel(self.r.ie, 0.0012421567277234543)
        self.assertRel(self.r.ve, 1.2421567277234544)
        self.assertRel(self.r.vb, 1.9421567277234544)
        self.assertRel(self.r.vc, 9.29431207822614)
        self.assertRel(self.r.vce, 8.052155350502685)

    def test_reference_case_is_active(self):
        self.assertEqual(self.r.region, "active")
        self.assertEqual(self.r.warnings, ())


class Validation(unittest.TestCase):
    BASE = dict(vcc=12.0, r1=100_000.0, r2=22_000.0,
                rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70)

    def call(self, **overrides):
        return calculate_dc_bias(**{**self.BASE, **overrides})

    def test_rejects_zero_resistance(self):
        for key in ("r1", "r2", "rc", "re"):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    self.call(**{key: 0.0})

    def test_rejects_negative_resistance(self):
        with self.assertRaises(ValueError):
            self.call(rc=-1.0)

    def test_rejects_non_positive_beta(self):
        for beta in (0.0, -5.0):
            with self.subTest(beta=beta):
                with self.assertRaises(ValueError):
                    self.call(beta=beta)

    def test_rejects_non_positive_vcc(self):
        with self.assertRaises(ValueError):
            self.call(vcc=0.0)

    def test_rejects_vbe_outside_range(self):
        for vbe in (-0.1, 12.0):
            with self.subTest(vbe=vbe):
                with self.assertRaises(ValueError):
                    self.call(vbe=vbe)

    def test_handles_very_large_vcc(self):
        r = self.call(vcc=1_000_000.0)
        self.assertEqual(r.region, "active")
        self.assertGreater(r.ic, 0.0)


class RegionLogic(unittest.TestCase):
    def test_cutoff_when_vth_not_above_vbe(self):
        r = calculate_dc_bias(
            vcc=12.0, r1=100_000.0, r2=5_000.0,
            rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70,
        )
        self.assertEqual(r.region, "cutoff")
        self.assertEqual(r.ib, 0.0)
        self.assertEqual(r.ic, 0.0)
        self.assertEqual(r.ie, 0.0)
        self.assertEqual(r.ve, 0.0)
        self.assertEqual(r.vc, 12.0)
        self.assertAlmostEqual(r.vb, 12.0 * 5_000.0 / 105_000.0)
        self.assertEqual(r.vce, 12.0)
        self.assertTrue(r.warnings)

    def test_saturation_when_vce_at_or_below_margin(self):
        r = calculate_dc_bias(
            vcc=12.0, r1=100_000.0, r2=22_000.0,
            rc=15_000.0, re=1_000.0, beta=100.0, vbe=0.70,
        )
        self.assertEqual(r.region, "saturation")
        self.assertLessEqual(r.vce, 0.3)
        self.assertTrue(r.warnings)

    def test_boundary_exactly_at_vbe_is_cutoff(self):
        vcc, vbe = 12.0, 0.70
        r2 = 1_000.0
        r1 = vcc * r2 / vbe - r2
        r = calculate_dc_bias(vcc=vcc, r1=r1, r2=r2, rc=2_200.0,
                              re=1_000.0, beta=100.0, vbe=vbe)
        self.assertEqual(r.region, "cutoff")
        self.assertTrue(r.warnings)

    def test_warning_text_mentions_limitation(self):
        r = calculate_dc_bias(vcc=12.0, r1=100_000.0, r2=5_000.0,
                              rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70)
        joined = " ".join(r.warnings)
        self.assertIn("cutoff", joined)


class NonFiniteInput(unittest.TestCase):
    """nan / inf แปลงเป็น float ได้ แต่ใช้คำนวณไม่ได้"""

    BASE = dict(vcc=12.0, r1=100_000.0, r2=22_000.0,
                rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70)

    def test_rejects_non_finite_values_in_every_field(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            for key in self.BASE:
                with self.subTest(key=key, value=value):
                    with self.assertRaises(ValueError):
                        calculate_dc_bias(**{**self.BASE, key: value})

    def test_rejects_infinite_result_instead_of_reporting_active(self):
        # ค่าที่ finite ทุกตัวแต่ผลลัพธ์ล้นเป็น inf ต้องไม่ถูกจัดเป็น active
        with self.assertRaises(ValueError):
            calculate_dc_bias(**{**self.BASE, "vcc": 1e308, "r1": 1e-300})


if __name__ == "__main__":
    unittest.main()
