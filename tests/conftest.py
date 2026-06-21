"""pytest fixtures：启动后端服务与 Playwright 浏览器。"""
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
VENV_PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"


def _wait_for_port(host: str, port: int, timeout: int = 30) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            try:
                s.connect((host, port))
                return True
            except OSError:
                time.sleep(0.5)
    return False


@pytest.fixture(scope="session")
def backend_server():
    """启动后端服务，测试结束后关闭。"""
    host = "127.0.0.1"
    port = 8123
    env = os.environ.copy()
    env["FUTU_OPEND_HOST"] = env.get("FUTU_OPEND_HOST", "127.0.0.1")
    env["FUTU_OPEND_PORT"] = env.get("FUTU_OPEND_PORT", "11111")

    cmd = [str(VENV_PYTHON), "-m", "uvicorn", "main:app", "--host", host, "--port", str(port), "--log-level", "warning"]
    proc = subprocess.Popen(
        cmd,
        cwd=str(BACKEND_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        if not _wait_for_port(host, port, timeout=30):
            proc.terminate()
            out, err = proc.communicate(timeout=5)
            raise RuntimeError(
                f"Backend failed to start on {host}:{port}.\nSTDOUT:\n{out.decode()}\nSTDERR:\n{err.decode()}"
            )
        yield f"http://{host}:{port}"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.fixture(scope="session")
def browser():
    """启动 Playwright 浏览器。"""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(browser, backend_server):
    """每个测试用例独立的页面实例。"""
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    pg = context.new_page()
    yield pg
    context.close()
