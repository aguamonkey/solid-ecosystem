"""Explicit demo data, idempotent across runs. Uses a running same-origin stack."""
import argparse
import json
from urllib.request import Request, urlopen

parser = argparse.ArgumentParser()
parser.add_argument("--base", default="http://127.0.0.1:5180")
args = parser.parse_args()
for identity, station, kelvin in [
    ("demo-ridge", "North ridge", 281.25),
    ("demo-canopy", "Canopy station", 285.60),
    ("demo-shore", "Eastern shore", 279.80),
]:
    payload = {"identity": identity, "station": station, "kelvin": kelvin}
    request = Request(
        args.base + "/api/readings", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Idempotency-Key": identity},
    )
    with urlopen(request, timeout=10) as response:
        print(identity, json.load(response)["outcome"])
