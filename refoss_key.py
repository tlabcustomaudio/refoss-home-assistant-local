"""mitmproxy addon: read YOUR Refoss account key from the Refoss app's own sign-in response.

Only the key is kept (in a file only you can read). The request, which carries your password,
is never looked at or stored. It also prints your devices (name, model, MAC suffix) so you can
match them to IP addresses in your router.

    mitmdump --listen-port 8080 -s refoss_key.py
"""
import json
import os
import pathlib

from mitmproxy import http

OUT = pathlib.Path(os.environ.get("REFOSS_KEY_FILE", "refoss-key.txt"))
HOSTS = ("refoss.net", "refoss.com", "meross.com")


def _data(flow: http.HTTPFlow):
    if not flow.response or not flow.request.pretty_host.endswith(HOSTS):
        return None
    try:
        return json.loads(flow.response.get_text() or "").get("data")
    except (ValueError, AttributeError):
        return None


def response(flow: http.HTTPFlow) -> None:
    data = _data(flow)
    if "/Auth/signIn" in flow.request.path and isinstance(data, dict) and data.get("key"):
        key = data["key"]
        OUT.write_text(key + "\n")
        os.chmod(OUT, 0o600)
        print("\n*** Refoss key captured: %s…%s (%d chars), saved to %s ***" % (key[:3], key[-3:], len(key), OUT.resolve()))
        print("*** Cloud region: %s. You can stop mitmproxy now (Ctrl+C) and undo the phone settings. ***\n"
              % data.get("domain", "?"))
    elif "/Device/devList" in flow.request.path and isinstance(data, list):
        print("\nYour devices (match the MAC suffix in your router to find each IP):")
        for d in data:
            uuid = d.get("uuid", "")
            mac = ":".join(uuid[-12:][i:i + 2] for i in range(0, 12, 2)) if len(uuid) >= 12 else "?"
            print("  %-28s %-8s MAC %s  %s" % (d.get("devName", "?"), d.get("deviceType", "?"), mac,
                                                "online" if d.get("onlineStatus") == 1 else "offline"))
        print()
