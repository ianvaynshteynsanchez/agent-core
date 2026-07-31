"""One-shot: wait for DNS before poll, so a wake-from-sleep run doesn't
fire 27 retry storms at a nameserver that isn't up yet."""
import pathlib, shutil, sys

path = pathlib.Path("app/pipeline.py")
src = path.read_text()

HELPER = '''def wait_for_dns(host="api.grants.gov", timeout=600, interval=20):
    """Block until host resolves, or timeout. Never aborts the run."""
    import socket, time as _t
    deadline = _t.monotonic() + timeout
    attempt = 0
    while _t.monotonic() < deadline:
        try:
            socket.getaddrinfo(host, 443)
            if attempt:
                log("net", f"DNS up after {attempt} retries")
            return True
        except socket.gaierror:
            attempt += 1
            if attempt == 1:
                log("net", f"{host} not resolving, waiting up to {timeout}s")
            _t.sleep(interval)
    log("net", "DNS never came up; continuing anyway")
    return False


def run():'''

ANCHOR_CALL = '''    stage("poll", do_poll)'''
NEW_CALL = '''    stage("net", wait_for_dns)
    stage("poll", do_poll)'''

if "wait_for_dns" in src:
    sys.exit("already patched - no change made")
if "def run():" not in src or ANCHOR_CALL not in src:
    sys.exit("ANCHOR NOT FOUND - nothing written")

shutil.copy(path, "app/pipeline.py.bak2")
src = src.replace("def run():", HELPER, 1)
src = src.replace(ANCHOR_CALL, NEW_CALL, 1)
path.write_text(src)
print("patched OK (backup at app/pipeline.py.bak2)")
