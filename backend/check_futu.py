"""富途连通性与市场支持检查脚本。"""
import sys

from config import HOLDINGS, DRAM_ETF_CODES
from futu_client import FutuClient
from opend_helper import ensure_opend


def main():
    ok, msg = ensure_opend()
    print(f"[OpenD] {msg}")
    if not ok:
        print("请先安装/启动 OpenD 后重试。")
        sys.exit(1)

    print("\n正在检测各市场代码可用性...")
    with FutuClient() as client:
        resolved = client.resolve_all_codes()

    print("\n=== 解析结果 ===")
    print(f"DRAM ETF: {resolved.get('DRAM', '不可用')}")
    for h in HOLDINGS:
        code = resolved.get(h["ticker"], "不可用")
        status = "OK" if code != "不可用" else "FAIL"
        print(f"[{status}] {h['name']} ({h['ticker']}) -> {code}")

    if not resolved:
        print("\n警告：未解析到任何可用代码，请检查 OpenD 登录状态与行情权限。")
        sys.exit(1)

    # 尝试取一次快照
    print("\n=== 快照测试 ===")
    with FutuClient() as client:
        codes = [c for c in resolved.values() if c]
        quotes = client.get_snapshot(codes)
        for q in quotes.values():
            price = f"{q.price:.2f}" if q.price is not None else "N/A"
            change = f"{q.change_pct:.2f}%" if q.change_pct is not None else "N/A"
            if q.valid:
                print(f"{q.code}: price={price}, change_pct={change}")
            else:
                print(f"{q.code}: error={q.error}")

    print("\n检查完成。")


if __name__ == "__main__":
    main()
