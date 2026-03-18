
import re
from typing import Callable, Optional


class Router:


    def __init__(self):
        self._routes = []

    def add_route(self, method: str, path: str, handler: Callable) -> None:
        param_names = []
        pattern     = path

        for match in re.finditer(r"<(int|str):(\w+)>", path):
            kind, name = match.group(1), match.group(2)
            regex_part = r"(\d+)" if kind == "int" else r"([^/]+)"
            pattern    = pattern.replace(match.group(0), regex_part, 1)
            param_names.append((name, kind))

        self._routes.append(
            (method.upper(), re.compile(f"^{pattern}$"), param_names, handler)
        )

    def resolve(self, method: str, path: str) -> tuple:
        path = path.split("?")[0].rstrip("/") or "/"

        for route_method, regex, param_names, handler in self._routes:
            if route_method != method.upper():
                continue
            m = regex.match(path)
            if m:
                kwargs = {}
                for (name, kind), value in zip(param_names, m.groups()):
                    kwargs[name] = int(value) if kind == "int" else value
                return handler, kwargs

        return None, {}
