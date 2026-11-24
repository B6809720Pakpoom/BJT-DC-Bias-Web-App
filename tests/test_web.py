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


class BiasModes(unittest.TestCase):
    """Lab 3 — mode selection, per-mode fields and browser-visible results."""

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def post(self, **overrides):
        return self.client.post("/", data={**VALID_FORM, **overrides})

    def test_get_form_has_mode_selector_and_rb_field(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn('name="mode"', body)
        for mode in ("divider", "fixed", "emitter"):
            self.assertIn(f'value="{mode}"', body)
        self.assertIn('name="rb"', body)

    def test_A1_divider_is_unchanged(self):
        body = self.post(mode="divider").get_data(as_text=True)
        for expected in ("8.052", "1.230", "12.299", "18.03"):
            self.assertIn(expected, body)

    def test_A2_fixed(self):
        body = self.post(mode="fixed", rb="1000").get_data(as_text=True)
        self.assertIn("1.130", body)
        self.assertIn("9.514", body)
        self.assertIn("Fixed Bias", body)

    def test_A3_emitter(self):
        body = self.post(mode="emitter", rb="1000", re="1").get_data(as_text=True)
        self.assertIn("1.026", body)
        self.assertIn("8.705", body)
        self.assertIn("Emitter Bias", body)

    def test_A4_re_change_is_visible(self):
        body = self.post(mode="emitter", rb="1000", re="2").get_data(as_text=True)
        self.assertIn("0.940", body)
        self.assertIn("8.033", body)

    def test_A5_zero_rb_shows_error_and_no_result(self):
        body = self.post(mode="fixed", rb="0").get_data(as_text=True)
        self.assertIn("RB", error_section(body))
        self.assertIn("มากกว่า 0", error_section(body))
        self.assertNotIn('class="region region-', body)
        self.assertNotIn("ผลลัพธ์ DC Bias", body)

    def test_unknown_mode_is_rejected_not_guessed_as_divider(self):
        body = self.post(mode="magic").get_data(as_text=True)
        self.assertIn("โหมดไม่รู้จัก", error_section(body))
        self.assertNotIn('class="region region-', body)
        self.assertNotIn("8.052", body)

    def test_fixed_mode_does_not_require_divider_only_fields(self):
        body = self.post(mode="fixed", rb="1000", r1="", r2="").get_data(as_text=True)
        self.assertIn("9.514", body)
        self.assertNotIn("กรุณากรอกตัวเลข", error_section(body))

    def test_error_does_not_reuse_previous_result(self):
        self.post(mode="divider")
        body = self.post(mode="fixed", rb="0").get_data(as_text=True)
        self.assertNotIn("8.052", body)
        self.assertNotIn('class="region region-active"', body)


NGSPICE_AVAILABLE = True
try:
    from spice_engine import find_engine
    find_engine()
except Exception:
    NGSPICE_AVAILABLE = False


@unittest.skipUnless(NGSPICE_AVAILABLE, "ngspice ไม่ได้ติดตั้งบนเครื่องนี้")
class SpicePages(unittest.TestCase):
    """Lab 4 — หน้าเว็บต้องแสดงผลจริงจาก engine และไม่โชว์ผลเก่าตอน error"""

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def post(self, **overrides):
        form = {
            **VALID_FORM,
            "rl": "10", "cin": "10", "cout": "10",
            "amplitude": "0.01", "frequency": "1",
            **overrides,
        }
        return self.client.post("/", data=form)

    def test_ac_page_has_phase_plot_and_cutoff_rows(self):
        body = self.post(analysis="spice_ac").get_data(as_text=True)
        self.assertIn("ผลลัพธ์จาก SPICE — AC Frequency Response (.ac)", body)
        self.assertIn("Phase (degree)", body)
        self.assertIn("Phase at peak", body)
        self.assertIn("Lower cutoff (-3 dB)", body)
        self.assertIn("not determined in sweep range", body)
        self.assertEqual(body.count("<polyline"), 2)  # gain + phase

    def test_polyline_points_use_valid_svg_polyline_syntax(self):
        body = self.post(analysis="spice_ac").get_data(as_text=True)
        points = re.search(r'<polyline points="([^"]+)"', body).group(1).strip()
        # <polyline> รับ "x,y x,y ..." เท่านั้น — คำสั่ง M/L ของ <path> ทำให้กราฟไม่ขึ้น
        self.assertNotRegex(points, r"[ML]")
        self.assertRegex(points, r"^(?:-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?\s*)+$")

    def test_tran_page_states_inversion_and_shows_two_waveforms(self):
        body = self.post(analysis="spice_tran").get_data(as_text=True)
        self.assertIn("Phase Vout vs Vin", body)
        self.assertIn("inverted (≈180°)", body)
        self.assertEqual(body.count("<polyline"), 2)  # Vout + Vin

    def test_re_zero_error_does_not_show_success_or_results(self):
        body = self.post(analysis="spice_dc", re="0").get_data(as_text=True)
        self.assertIn("RE", error_section(body))
        self.assertIn("มากกว่า 0", error_section(body))
        self.assertNotIn("status-success", body)
        self.assertNotIn("ผลลัพธ์จาก SPICE", body)
        self.assertNotIn("<polyline", body)


if __name__ == "__main__":
    unittest.main()
