"""OpenD 检测与启动辅助模块。"""
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
    """在常见位置搜索 OpenD-GUI.exe。"""
    for base in COMMON_OPEND_PATHS:
        if not base.exists():
            continue
        try:
            matches = list(base.rglob(OPEND_GUI_PATTERN))
            if matches:
                # 优先选择目录层级较浅的
                matches.sort(key=lambda p: len(p.parts))
                return matches[0]
        except PermissionError:
            continue
    return None


def start_opend(exe_path: Path, wait: int = 5) -> bool:
    """启动 OpenD GUI，等待指定秒数。"""
    try:
        subprocess.Popen([str(exe_path)], shell=False)
        time.sleep(wait)
        return True
    except Exception as e:
        print(f"启动 OpenD 失败: {e}", file=sys.stderr)
        return False


def ensure_opend() -> tuple[bool, str]:
    """
    确保 OpenD 可用。
    返回 (success, message)。
    若已找到 OpenD 但无法自动启动，会提示用户手动启动。
    """
    from futu import OpenQuoteContext

    # 先尝试直接连接
    try:
        ctx = OpenQuoteContext(host=OPEND_DEFAULT_HOST, port=OPEND_DEFAULT_PORT)
        ctx.close()
        return True, f"OpenD 已在 {OPEND_DEFAULT_HOST}:{OPEND_DEFAULT_PORT} 运行"
    except Exception:
        pass

    exe = find_opend_gui()
    if exe:
        print(f"检测到 OpenD: {exe}")
        if start_opend(exe):
            # 再次验证
            try:
                ctx = OpenQuoteContext(host=OPEND_DEFAULT_HOST, port=OPEND_DEFAULT_PORT)
                ctx.close()
                return True, f"已自动启动 OpenD 并连接 {OPEND_DEFAULT_HOST}:{OPEND_DEFAULT_PORT}"
            except Exception as e:
                return (
                    False,
                    f"找到 OpenD 并已尝试启动，但仍无法连接 ({e})。请在 OpenD GUI 中完成登录后重试。",
                )
        else:
            return False, f"找到 OpenD ({exe})，但自动启动失败，请手动启动。"
    else:
        return (
            False,
            "未检测到 OpenD。请先下载安装富途 OpenD（https://www.futunn.com/OpenAPI）并登录。",
        )


if __name__ == "__main__":
    ok, msg = ensure_opend()
    print(msg)
    sys.exit(0 if ok else 1)
