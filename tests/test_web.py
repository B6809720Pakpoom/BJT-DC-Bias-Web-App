import re
import unittest

from app import app


def error_section(body):
    """เนื้อในกล่อง error เท่านั้น (กันการไปเจอชื่อ field ใน <input value=...>)"""
    match = re.search(r'<section class="errors".*?</section>', body, re.S)
    return match.group(0) if match else ""


class FormPage(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_get_index_returns_200(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)

    def test_form_contains_all_input_names(self):
        body = self.client.get("/").get_data(as_text=True)
        for name in ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"):
            self.assertIn(f'name="{name}"', body)

    def test_form_mentions_kohm_for_resistors(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn("kΩ", body)

    def test_form_states_the_model_assumption(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn("Forward-Active", body)
        self.assertIn("β คงที่", body)

    def test_ohm_hint_uses_thousands_separator(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn("= 100,000 Ω", body)


VALID_FORM = dict(vcc="12", r1="100", r2="22", rc="2.2",
                  re="1", beta="100", vbe="0.70")


class Calculation(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def post(self, **overrides):
        return self.client.post("/", data={**VALID_FORM, **overrides})

    def test_valid_post_shows_reference_results(self):
        resp = self.post()
        body = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("8.052", body)
        self.assertIn("1.230", body)
        self.assertIn("12.299", body)

    def test_valid_post_shows_active_region(self):
        body = self.post().get_data(as_text=True)
        self.assertIn("Active", body)

    def test_zero_resistance_shows_readable_error(self):
        resp = self.post(r1="0")
        body = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("มากกว่า 0", body)
        self.assertNotIn("Traceback", body)

    def test_non_numeric_input_shows_readable_error(self):
        resp = self.post(vcc="abc")
        body = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("ตัวเลข", body)
        self.assertNotIn("Traceback", body)

    def test_comma_decimal_is_rejected_clearly(self):
        resp = self.post(r1="12,0")
        body = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("ตัวเลข", body)

    def test_repeated_post_keeps_working(self):
        self.post()
        resp = self.post()
        self.assertEqual(resp.status_code, 200)
        self.assertIn("8.052", resp.get_data(as_text=True))


class Hardening(unittest.TestCase):
    """ค่าที่แปลงเป็น float ได้แต่ไม่ใช่จำนวนจริงที่ใช้คำนวณได้"""

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def post(self, **overrides):
        return self.client.post("/", data={**VALID_FORM, **overrides})

    def test_nan_vcc_shows_error_and_never_active(self):
        resp = self.post(vcc="nan")
        body = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("จำนวนจำกัด", error_section(body))
        self.assertNotIn('class="region region-active"', body)
        self.assertNotIn("Traceback", body)

    def test_infinite_beta_shows_error(self):
        body = self.post(beta="inf").get_data(as_text=True)
        self.assertIn("จำนวนจำกัด", error_section(body))
        self.assertNotIn('class="region region-active"', body)

    def test_overflowing_resistor_shows_error(self):
        # 1e308 × 1000 = inf — ต้องถูกจับหลังการแปลงหน่วย
        body = self.post(r1="1e308").get_data(as_text=True)
        self.assertIn("จำนวนจำกัด", error_section(body))
        self.assertNotIn("Traceback", body)

    def test_reports_every_bad_field(self):
        body = self.post(vcc="abc", r1="12,0").get_data(as_text=True)
        section = error_section(body)
        self.assertIn("vcc", section)
        self.assertIn("r1", section)

    def test_error_response_has_no_region_badge(self):
        body = self.post(r1="0").get_data(as_text=True)
        self.assertNotIn("region-", body)

    def test_cutoff_post_shows_badge_and_warning(self):
        body = self.post(r2="5").get_data(as_text=True)
        self.assertIn('class="region region-cutoff"', body)
        self.assertIn('class="warnings"', body)
        self.assertIn("cutoff", body)

    def test_saturation_post_shows_badge_and_warning(self):
        body = self.post(rc="15").get_data(as_text=True)
        self.assertIn('class="region region-saturation"', body)
        self.assertIn('class="warnings"', body)
        self.assertIn("saturation", body)

    def test_cutoff_vce_equals_vcc(self):
        body = self.post(r2="5").get_data(as_text=True)
        match = re.search(r"<th>VCE</th>\s*<td>([\d.]+) V</td>", body)
        self.assertIsNotNone(match, "ไม่พบแถว VCE")
        self.assertEqual(match.group(1), "12.000")


if __name__ == "__main__":
    unittest.main()
