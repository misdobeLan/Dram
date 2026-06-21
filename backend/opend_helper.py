"""OpenD 检测与启动辅助模块。

同时支持：
- 官方富途 OpenD-GUI.exe（优先）
- 项目内置的 FUTU-OpenD-rs 命令行网关（futu-opend.exe）
"""
import os
import subprocess
import sys
import time
from pathlib import Path

# 常见安装位置（Windows）
COMMON_OPEND_PATHS = [
    Path.home() / "Desktop",
    Path("C:/Program Files"),
    Path("C:/Program Files (x86)"),
    Path("D:/"),
]

OPEND_GUI_PATTERN = "*OpenD-GUI*.exe"
OPEND_DEFAULT_HOST = os.getenv("FUTU_OPEND_HOST", "127.0.0.1")
OPEND_DEFAULT_PORT = int(os.getenv("FUTU_OPEND_PORT", "11111"))


def find_opend_gui() -> Path | None:
    """在常见位置搜索官方 OpenD-GUI.exe。"""
    for base in COMMON_OPEND_PATHS:
        if not base.exists():
            continue
        try:
            matches = list(base.rglob(OPEND_GUI_PATTERN))
            if matches:
                matches.sort(key=lambda p: len(p.parts))
                return matches[0]
        except PermissionError:
            continue
    return None


def find_bundled_opend() -> Path | None:
    """搜索项目内置的 futu-opend-rs。"""
    project_root = Path(__file__).resolve().parent.parent
    tools_dir = project_root / "tools"
    if not tools_dir.exists():
        return None
    for sub in tools_dir.iterdir():
        if sub.is_dir() and "opend" in sub.name.lower():
            exe = sub / "futu-opend.exe"
            if exe.exists():
                return exe
    return None


def start_opend_gui(exe_path: Path, wait: int = 5) -> bool:
    """启动官方 OpenD GUI。"""
    try:
        subprocess.Popen([str(exe_path)], shell=False)
        time.sleep(wait)
        return True
    except Exception as e:
        print(f"启动 OpenD 失败: {e}", file=sys.stderr)
        return False


def start_bundled_opend(exe_path: Path) -> subprocess.Popen | None:
    """启动项目内置的 futu-opend-rs（命令行）。
    返回进程对象；调用方负责生命周期。
    """
    try:
        # 默认监听 127.0.0.1:11111，不启用 REST/gRPC/WS（仅 FTAPI TCP 协议）
        proc = subprocess.Popen(
            [str(exe_path), "-i", "127.0.0.1", "-p", str(OPEND_DEFAULT_PORT)],
            cwd=str(exe_path.parent),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return proc
    except Exception as e:
        print(f"启动 futu-opend-rs 失败: {e}", file=sys.stderr)
        return None


def _is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    import socket
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    import socket
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def ensure_opend() -> tuple[bool, str]:
    """
    确保 OpenD 可用。
    返回 (success, message)。
    """
    from futu import OpenQuoteContext

    # 先快速端口探测，避免 futu 内部长时间重试
    if _port_open(OPEND_DEFAULT_HOST, OPEND_DEFAULT_PORT):
        try:
            ctx = OpenQuoteContext(host=OPEND_DEFAULT_HOST, port=OPEND_DEFAULT_PORT)
            ctx.close()
            return True, f"OpenD 已在 {OPEND_DEFAULT_HOST}:{OPEND_DEFAULT_PORT} 运行"
        except Exception:
            pass

    # 1. 优先使用官方 GUI
    exe = find_opend_gui()
    if exe:
        print(f"检测到官方 OpenD: {exe}")
        if start_opend_gui(exe):
            try:
                ctx = OpenQuoteContext(host=OPEND_DEFAULT_HOST, port=OPEND_DEFAULT_PORT)
                ctx.close()
                return True, f"已自动启动官方 OpenD 并连接 {OPEND_DEFAULT_HOST}:{OPEND_DEFAULT_PORT}"
            except Exception as e:
                return (
                    False,
                    f"找到官方 OpenD 并已尝试启动，但仍无法连接 ({e})。请在 OpenD GUI 中完成登录后重试。",
                )
        else:
            return False, f"找到官方 OpenD ({exe})，但自动启动失败，请手动启动。"

    # 2. 使用项目内置的 futu-opend-rs
    bundled = find_bundled_opend()
    if bundled:
        print(f"检测到项目内置网关: {bundled}")
        proc = start_bundled_opend(bundled)
        if proc:
            # 等待端口就绪（最多 10 秒）
            for _ in range(20):
                if _is_port_open(OPEND_DEFAULT_HOST, OPEND_DEFAULT_PORT):
                    try:
                        ctx = OpenQuoteContext(host=OPEND_DEFAULT_HOST, port=OPEND_DEFAULT_PORT)
                        ctx.close()
                        return (
                            True,
                            f"已自动启动项目内置网关 {bundled} 并连接 {OPEND_DEFAULT_HOST}:{OPEND_DEFAULT_PORT}。"
                            "注意：如未配置登录信息，网关将处于离线模式，无法获取真实行情。",
                        )
                    except Exception:
                        pass
                time.sleep(0.5)
            return (
                False,
                f"项目内置网关已启动但无法建立行情连接。请检查日志或配置登录信息。",
            )
        else:
            return False, "项目内置网关启动失败。"

    return (
        False,
        "未检测到 OpenD。请先下载安装富途 OpenD（https://www.futunn.com/OpenAPI）并登录，"
        "或运行 install_opend_rs.bat 使用项目内置网关。",
    )


if __name__ == "__main__":
    ok, msg = ensure_opend()
    print(msg)
    sys.exit(0 if ok else 1)
