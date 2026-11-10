import unittest

from app import app


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

    def test_repated_post_keeps_working(self):
        self.post()
        resp = self.post()
        self.assertEqual(resp.status_code, 200)
        self.assertIn("8.052", resp.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
