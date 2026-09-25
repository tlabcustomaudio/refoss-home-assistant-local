"""Offline check of refoss_key.py with fake flows: python test_refoss_key.py (needs mitmproxy installed)."""
import json
import os
import stat
import tempfile

from mitmproxy.test import tflow, tutils

os.environ["REFOSS_KEY_FILE"] = os.path.join(tempfile.mkdtemp(), "key.txt")
import refoss_key  # noqa: E402


def flow(host, path, body):
    f = tflow.tflow(req=tutils.treq(host=host, path=path), resp=tutils.tresp(content=json.dumps(body).encode()))
    return f


sign = {"apiStatus": 0, "data": {"key": "abc0123456789def0123456789abcxyz", "token": "t", "domain": "https://iotx-eu.refoss.net"}}
refoss_key.response(flow("iotx-eu.refoss.net", "/v1/Auth/signIn", sign))
p = refoss_key.OUT
assert p.read_text().strip() == sign["data"]["key"]
assert stat.S_IMODE(os.stat(p).st_mode) == 0o600

p.unlink()
refoss_key.response(flow("evil.example.com", "/v1/Auth/signIn", sign))    # other hosts are ignored
refoss_key.response(flow("iotx-eu.refoss.net", "/v1/Auth/signIn", {"data": {}}))   # failed login: nothing
assert not p.exists()

refoss_key.response(flow("iotx-eu.refoss.net", "/v1/Device/devList",
                         {"data": [{"devName": "Printer", "deviceType": "mss310", "uuid": "2306" + "0" * 16 + "aabbcc445566",
                                    "onlineStatus": 1}]}))
print("refoss_key OK")
