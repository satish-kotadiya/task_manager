

import argparse
import json
import sys
import urllib.error
import urllib.request

API_BASE = "http://localhost:5000/api/v1"



def _request(method: str, path: str, payload: dict = None) -> tuple:
    url  = f"{API_BASE}{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    hdrs = {"Content-Type": "application/json"} if data else {}

    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode())
    except urllib.error.URLError:
        print("\n  ✗ Cannot connect to API — is the server running?")
        print("    Start it with:  python main.py\n")
        sys.exit(1)



def _sep(char="─", width=62):
    return char * width


def _priority_badge(p):
    return {"high": "[HIGH]", "medium": "[MED] ", "low": "[LOW] "}.get(p, p)


def _status_badge(s):
    return {
        "completed":   "[DONE]",
        "in_progress": "[WIP] ",
        "pending":     "[    ]",
    }.get(s, s)


def _print_table(tasks: list) -> None:
    if not tasks:
        print("\n  (no tasks found)\n")
        return

    header = (
        f"  {'ID':<4}  {'Title':<35}  {'Status':<6}  {'Pri':<6}  {'Due Date':<10}"
    )
    print("\n" + _sep())
    print(header)
    print(_sep())
    for t in tasks:
        title = t["title"]
        if len(title) > 35:
            title = title[:32] + "..."
        due = (t.get("due_date") or "—")[:10]
        print(
            f"  {t['id']:<4}  {title:<35}  "
            f"{_status_badge(t['status']):<6}  "
            f"{_priority_badge(t['priority']):<6}  "
            f"{due:<10}"
        )
    print(_sep() + "\n")


def _print_detail(t: dict) -> None:
    print("\n" + _sep())
    print(f"  ID          : {t['id']}")
    print(f"  Title       : {t['title']}")
    print(f"  Description : {t.get('description') or '—'}")
    print(f"  Status      : {_status_badge(t['status'])}  ({t['status']})")
    print(f"  Priority    : {_priority_badge(t['priority'])}  ({t['priority']})")
    print(f"  Due Date    : {(t.get('due_date') or '—')[:10]}")
    print(f"  Created     : {(t.get('created_at') or '')[:19]}")
    print(f"  Updated     : {(t.get('updated_at') or '')[:19]}")
    print(_sep() + "\n")



def cmd_list(args):
    path = "/tasks"
    sep  = "?"
    if args.status:
        path += f"{sep}status={args.status}";   sep = "&"
    if args.priority:
        path += f"{sep}priority={args.priority}"

    status, data = _request("GET", path)
    if status != 200:
        print(f"\n  Error: {data.get('error')}\n")
        return
    print(f"\n  Found {data['count']} task(s)")
    _print_table(data["tasks"])


def cmd_get(args):
    status, data = _request("GET", f"/tasks/{args.id}")
    if status == 404:
        print(f"\n  Task {args.id} not found.\n")
        return
    if status != 200:
        print(f"\n  Error: {data.get('error')}\n")
        return
    _print_detail(data)


def cmd_add(args):
    payload = {
        "title":       args.title,
        "description": args.description or "",
        "priority":    args.priority,
        "status":      args.status,
    }
    if args.due_date:
        payload["due_date"] = args.due_date

    status, data = _request("POST", "/tasks", payload)
    if status == 201:
        print(f"\n  ✓ Task created — ID: {data['id']}")
        _print_table([data])
    else:
        print(f"\n  ✗ Error: {data.get('errors') or data.get('error')}\n")


def cmd_update(args):
    payload = {}
    if args.title       is not None: payload["title"]       = args.title
    if args.description is not None: payload["description"] = args.description
    if args.status      is not None: payload["status"]      = args.status
    if args.priority    is not None: payload["priority"]    = args.priority
    if args.due_date    is not None:
        payload["due_date"] = None if args.due_date.lower() == "none" else args.due_date

    if not payload:
        print("\n  Nothing to update — pass at least one option.\n")
        return

    status, data = _request("PUT", f"/tasks/{args.id}", payload)
    if status == 200:
        print(f"\n  ✓ Task {args.id} updated.")
        _print_table([data])
    elif status == 404:
        print(f"\n  Task {args.id} not found.\n")
    else:
        print(f"\n  ✗ Error: {data.get('errors') or data.get('error')}\n")


def cmd_delete(args):
    answer = input(f"  Delete task {args.id}? [y/N]: ").strip().lower()
    if answer != "y":
        print("  Cancelled.\n")
        return
    status, data = _request("DELETE", f"/tasks/{args.id}")
    if status == 200:
        print(f"\n  ✓ {data['message']}\n")
    elif status == 404:
        print(f"\n  Task {args.id} not found.\n")
    else:
        print(f"\n  ✗ Error: {data.get('error')}\n")


def cmd_complete(args):
    status, data = _request("PATCH", f"/tasks/{args.id}/complete")
    if status == 200:
        print(f"\n  ✓ Task {args.id} marked as completed!\n")
    elif status == 404:
        print(f"\n  Task {args.id} not found.\n")
    else:
        print(f"\n  ✗ Error: {data.get('error')}\n")


def cmd_incomplete(args):
    status, data = _request("PATCH", f"/tasks/{args.id}/incomplete")
    if status == 200:
        print(f"\n  ✓ Task {args.id} marked as pending.\n")
    elif status == 404:
        print(f"\n  Task {args.id} not found.\n")
    else:
        print(f"\n  ✗ Error: {data.get('error')}\n")




def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="task-manager",
        description="Task Manager CLI — pure Python stdlib",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # list
    p_list = sub.add_parser("list", help="List all tasks")
    p_list.add_argument("--status",   "-s",
                        choices=["pending", "in_progress", "completed"])
    p_list.add_argument("--priority", "-p",
                        choices=["low", "medium", "high"])
    p_list.set_defaults(func=cmd_list)

    # get
    p_get = sub.add_parser("get", help="Show task details")
    p_get.add_argument("id", type=int, help="Task ID")
    p_get.set_defaults(func=cmd_get)

    # add
    p_add = sub.add_parser("add", help="Create a new task")
    p_add.add_argument("--title",       "-t", required=True)
    p_add.add_argument("--description", "-d", default="")
    p_add.add_argument("--priority",    "-p",
                       choices=["low", "medium", "high"], default="medium")
    p_add.add_argument("--status",      "-s",
                       choices=["pending", "in_progress", "completed"], default="pending")
    p_add.add_argument("--due-date",    dest="due_date", metavar="YYYY-MM-DD")
    p_add.set_defaults(func=cmd_add)

    # update
    p_upd = sub.add_parser("update", help="Update a task")
    p_upd.add_argument("id", type=int)
    p_upd.add_argument("--title",       "-t")
    p_upd.add_argument("--description", "-d")
    p_upd.add_argument("--priority",    "-p",
                       choices=["low", "medium", "high"])
    p_upd.add_argument("--status",      "-s",
                       choices=["pending", "in_progress", "completed"])
    p_upd.add_argument("--due-date",    dest="due_date",
                       metavar="YYYY-MM-DD  (or 'none' to clear)")
    p_upd.set_defaults(func=cmd_update)

    # delete
    p_del = sub.add_parser("delete", help="Delete a task")
    p_del.add_argument("id", type=int)
    p_del.set_defaults(func=cmd_delete)

    # complete
    p_cmp = sub.add_parser("complete", help="Mark task as completed")
    p_cmp.add_argument("id", type=int)
    p_cmp.set_defaults(func=cmd_complete)

    # incomplete
    p_inc = sub.add_parser("incomplete", help="Mark task as pending")
    p_inc.add_argument("id", type=int)
    p_inc.set_defaults(func=cmd_incomplete)

    return parser


def main():
    parser = build_parser()
    args   = parser.parse_args()
    args.func(args)
