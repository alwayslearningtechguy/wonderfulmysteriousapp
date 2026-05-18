import subprocess
import time
import socket
import pytest
import httpx

def wait_for_port(host, port, timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError("Server did not start in time")

@pytest.fixture(scope="session")
def app_server():
    proc = subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
    )
    wait_for_port("127.0.0.1", 8000)
    yield
    proc.terminate()
    proc.wait()

@pytest.fixture
def client(app_server):
    with httpx.Client(base_url="http://127.0.0.1:8000") as c:
        yield c
