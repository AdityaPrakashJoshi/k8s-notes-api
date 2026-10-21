
import unittest
from app.app import app


class NotesAPITestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_create_note_without_json_returns_415(self):
        response = self.client.post("/notes")

        self.assertEqual(response.status_code, 415)
if __name__ == "__main__":
    unittest.main()

