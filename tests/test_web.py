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


if __name__ == "__main__":
    unittest.main()
