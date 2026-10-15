"""Exercise a running same-origin stack. Each run uses a fresh observation identity."""
import argparse
import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

parser = argparse.ArgumentParser()
parser.add_argument("--base", default="http://127.0.0.1:8080")
args = parser.parse_args()


def request(path, payload=None, key=None):
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Idempotency-Key"] = key
    body = None if payload is None else json.dumps(payload).encode()
    req = Request(args.base + path, data=body, headers=headers)
    try:
        with urlopen(req, timeout=10) as response:
            return response.status, response.read()
    except HTTPError as error:
        return error.code, error.read()


assert request("/")[0] == 200
assert request("/api/ready")[0] == 200
identity = "smoke-" + uuid4().hex
payload = {"identity": identity, "station": "Integration ridge", "kelvin": 281.25}
assert request("/api/readings", payload, identity)[0] == 201
assert request("/api/readings", payload, identity)[0] == 200
assert request("/api/readings", {**payload, "kelvin": 282}, identity)[0] == 409
status, body = request("/api/readings/" + identity)
assert status == 200 and json.loads(body)["observation"]["kelvin"] == 281.25
assert request("/api/export?format=json")[0] == 200
print("Stack smoke passed: web, readiness, create, replay, conflict, lookup, export.")
