
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from app import database as db
from app.models import VALID_PRIORITIES, VALID_STATUSES
from app.router import Router
from app.validators import validate_create, validate_update

router = Router()


def handle_health(request, **_):
    return 200, {"status": "healthy", "message": "Task Manager API is running"}


def handle_list_tasks(request, **_):
    params   = request.query_params
    status   = params.get("status",   [None])[0]
    priority = params.get("priority", [None])[0]

    if status and status not in VALID_STATUSES:
        return 400, {"error": f"Invalid status. Valid: {list(VALID_STATUSES)}"}
    if priority and priority not in VALID_PRIORITIES:
        return 400, {"error": f"Invalid priority. Valid: {list(VALID_PRIORITIES)}"}

    tasks = db.get_all_tasks(status=status, priority=priority)
    return 200, {"tasks": [t.to_dict() for t in tasks], "count": len(tasks)}


def handle_get_task(request, task_id: int):
    task = db.get_task_by_id(task_id)
    if not task:
        return 404, {"error": f"Task {task_id} not found"}
    return 200, task.to_dict()


def handle_create_task(request, **_):
    data   = request.body
    errors = validate_create(data)
    if errors:
        return 422, {"errors": errors}

    due_date, err = _parse_due_date(data.get("due_date"))
    if err:
        return 400, {"error": err}

    task = db.create_task(
        title       = data["title"],
        description = data.get("description", ""),
        status      = data.get("status",   "pending"),
        priority    = data.get("priority", "medium"),
        due_date    = due_date,
    )
    return 201, task.to_dict()


def handle_update_task(request, task_id: int):
    if not db.get_task_by_id(task_id):
        return 404, {"error": f"Task {task_id} not found"}

    data   = request.body
    errors = validate_update(data)
    if errors:
        return 422, {"errors": errors}

    if "due_date" in data and data["due_date"] is not None:
        due_date, err = _parse_due_date(data["due_date"])
        if err:
            return 400, {"error": err}
        data["due_date"] = due_date

    task = db.update_task(task_id, data)
    return 200, task.to_dict()


def handle_delete_task(request, task_id: int):
    if not db.delete_task(task_id):
        return 404, {"error": f"Task {task_id} not found"}
    return 200, {"message": f"Task {task_id} deleted successfully"}


def handle_complete_task(request, task_id: int):
    if not db.get_task_by_id(task_id):
        return 404, {"error": f"Task {task_id} not found"}
    task = db.update_task(task_id, {"status": "completed"})
    return 200, task.to_dict()


def handle_incomplete_task(request, task_id: int):
    if not db.get_task_by_id(task_id):
        return 404, {"error": f"Task {task_id} not found"}
    task = db.update_task(task_id, {"status": "pending"})
    return 200, task.to_dict()


router.add_route("GET",    "/api/v1/health",                         handle_health)
router.add_route("GET",    "/api/v1/tasks",                          handle_list_tasks)
router.add_route("POST",   "/api/v1/tasks",                          handle_create_task)
router.add_route("GET",    "/api/v1/tasks/<int:task_id>",            handle_get_task)
router.add_route("PUT",    "/api/v1/tasks/<int:task_id>",            handle_update_task)
router.add_route("DELETE", "/api/v1/tasks/<int:task_id>",            handle_delete_task)
router.add_route("PATCH",  "/api/v1/tasks/<int:task_id>/complete",   handle_complete_task)
router.add_route("PATCH",  "/api/v1/tasks/<int:task_id>/incomplete", handle_incomplete_task)


class RequestContext:
    def __init__(self, body: dict, query_params: dict):
        self.body         = body
        self.query_params = query_params


class TaskHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print(f"  [{self.log_date_time_string()}] {fmt % args}")

    def _send_json(self, status: int, data: dict) -> None:
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type",   "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def _dispatch(self) -> None:
        parsed       = urlparse(self.path)
        query_params = parse_qs(parsed.query)
        handler_fn, kwargs = router.resolve(self.command, parsed.path)

        if handler_fn is None:
            self._send_json(404, {"error": "Endpoint not found"})
            return

        body    = self._read_body()
        context = RequestContext(body=body, query_params=query_params)

        try:
            status, response = handler_fn(context, **kwargs)
            self._send_json(status, response)
        except Exception as exc:
            self._send_json(500, {"error": str(exc)})

    def do_GET(self):    self._dispatch()
    def do_POST(self):   self._dispatch()
    def do_PUT(self):    self._dispatch()
    def do_DELETE(self): self._dispatch()
    def do_PATCH(self):  self._dispatch()



def _parse_due_date(raw):
    if not raw:
        return None, None
    try:
        if "T" not in raw:
            raw = f"{raw}T00:00:00"
        datetime.fromisoformat(raw)
        return raw, None
    except ValueError:
        return None, "Invalid due_date. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS"
