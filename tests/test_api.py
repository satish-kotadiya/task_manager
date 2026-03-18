
import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import HTTPServer

_tmp_dir = tempfile.mkdtemp()
os.environ["DATABASE_PATH"] = os.path.join(_tmp_dir, "test_tasks.db")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db
from app.handlers import TaskHandler

TEST_HOST = "127.0.0.1"
TEST_PORT = 15001
BASE      = f"http://{TEST_HOST}:{TEST_PORT}/api/v1"


def _req(method, path, payload=None):
    url  = f"{BASE}{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    hdrs = {"Content-Type": "application/json"} if data else {}
    req  = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


class TestTaskAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.server = HTTPServer((TEST_HOST, TEST_PORT), TaskHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_01_health(self):
        status, data = _req("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "healthy")

    def test_02_create_task(self):
        status, data = _req("POST", "/tasks", {"title": "Buy milk", "priority": "low"})
        self.assertEqual(status, 201)
        self.assertEqual(data["title"], "Buy milk")
        self.assertEqual(data["priority"], "low")
        self.assertEqual(data["status"], "pending")
        self.assertIn("id", data)

    def test_03_create_missing_title(self):
        status, data = _req("POST", "/tasks", {"priority": "high"})
        self.assertEqual(status, 422)
        self.assertIn("errors", data)

    def test_04_create_invalid_priority(self):
        status, data = _req("POST", "/tasks", {"title": "X", "priority": "urgent"})
        self.assertEqual(status, 422)

    def test_05_list_tasks(self):
        status, data = _req("GET", "/tasks")
        self.assertEqual(status, 200)
        self.assertIn("tasks", data)
        self.assertIn("count", data)

    def test_06_filter_by_status(self):
        _req("POST", "/tasks", {"title": "Done task", "status": "completed"})
        status, data = _req("GET", "/tasks?status=completed")
        self.assertEqual(status, 200)
        self.assertTrue(all(t["status"] == "completed" for t in data["tasks"]))

    def test_07_filter_by_priority(self):
        _req("POST", "/tasks", {"title": "Urgent task", "priority": "high"})
        status, data = _req("GET", "/tasks?priority=high")
        self.assertEqual(status, 200)
        self.assertTrue(all(t["priority"] == "high" for t in data["tasks"]))

    def test_08_get_not_found(self):
        status, _ = _req("GET", "/tasks/99999")
        self.assertEqual(status, 404)

    def test_09_get_task(self):
        _, created = _req("POST", "/tasks", {"title": "Single task"})
        status, data = _req("GET", f"/tasks/{created['id']}")
        self.assertEqual(status, 200)
        self.assertEqual(data["title"], "Single task")

    def test_10_update_task(self):
        _, created = _req("POST", "/tasks", {"title": "Old title"})
        status, data = _req("PUT", f"/tasks/{created['id']}",
                            {"title": "New title", "priority": "high"})
        self.assertEqual(status, 200)
        self.assertEqual(data["title"], "New title")
        self.assertEqual(data["priority"], "high")

    def test_11_update_unknown_field(self):
        _, created = _req("POST", "/tasks", {"title": "T"})
        status, _ = _req("PUT", f"/tasks/{created['id']}", {"color": "red"})
        self.assertEqual(status, 422)

    def test_12_update_not_found(self):
        status, _ = _req("PUT", "/tasks/99999", {"title": "Ghost"})
        self.assertEqual(status, 404)

    # ── delete ────────────────────────────────
    def test_13_delete_task(self):
        _, created = _req("POST", "/tasks", {"title": "Delete me"})
        status, _ = _req("DELETE", f"/tasks/{created['id']}")
        self.assertEqual(status, 200)
        gone, _ = _req("GET", f"/tasks/{created['id']}")
        self.assertEqual(gone, 404)

    def test_14_delete_not_found(self):
        status, _ = _req("DELETE", "/tasks/99999")
        self.assertEqual(status, 404)

    # ── complete / incomplete ─────────────────
    def test_15_complete_task(self):
        _, created = _req("POST", "/tasks", {"title": "Finish me"})
        status, data = _req("PATCH", f"/tasks/{created['id']}/complete")
        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "completed")

    def test_16_incomplete_task(self):
        _, created = _req("POST", "/tasks", {"title": "Reset me", "status": "completed"})
        status, data = _req("PATCH", f"/tasks/{created['id']}/incomplete")
        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "pending")

    def test_17_create_with_due_date(self):
        status, data = _req("POST", "/tasks",
                            {"title": "Deadline task", "due_date": "2025-12-31"})
        self.assertEqual(status, 201)
        self.assertIn("2025-12-31", data["due_date"])

    def test_18_invalid_due_date(self):
        status, _ = _req("POST", "/tasks",
                         {"title": "Bad date", "due_date": "31-12-2025"})
        self.assertEqual(status, 400)


if __name__ == "__main__":
    unittest.main()
