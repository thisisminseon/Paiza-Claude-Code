"""e-Stat API から景気動向指数（CI・2020年=100・月次）を取得する"""

import os
from datetime import date

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData"
STATS_DATA_ID = "0003446461"  # 景気動向指数 長期系列（内閣府）
TAB_CI = "100"                # 表章項目: CI指数（2020年=100）

# 系列コード → 表示名
SERIES = {
    "100": "先行指数",
    "110": "一致指数",
    "120": "遅行指数",
}


def fetch_ci(months: int = 12) -> pd.DataFrame:
    """景気動向指数 CI（月次）の直近 months か月分を取得し、1行=1か月×1系列 の DataFrame で返す。

    列: 年月, 系列, CI指数
    """
    app_id = os.getenv("ESTAT_APP_ID")
    if not app_id:
        raise RuntimeError(".env に ESTAT_APP_ID が設定されていません")

    # 公表の遅れ（約2か月）を考慮し、余裕をもって取得してから直近 months か月に絞る
    start_year = date.today().year - (months // 12) - 1
    params = {
        "appId": app_id,
        "statsDataId": STATS_DATA_ID,
        "cdTab": TAB_CI,
        "cdCat01": ",".join(SERIES),
        "cdTimeFrom": f"{start_year}000101",
        "metaGetFlg": "N",
    }
    res = requests.get(API_URL, params=params, timeout=30)
    res.raise_for_status()
    data = res.json()["GET_STATS_DATA"]

    status = data["RESULT"]["STATUS"]
    if status != 0:
        raise RuntimeError(f"e-Stat API エラー ({status}): {data['RESULT']['ERROR_MSG']}")

    df = pd.DataFrame(data["STATISTICAL_DATA"]["DATA_INF"]["VALUE"])

    # 時間コード: YYYY00MMMM
    df = df[df["@time"].str[6:8] != "00"]
    df["年月"] = pd.to_datetime(df["@time"].str[:4] + "-" + df["@time"].str[8:10] + "-01")
    df["系列"] = df["@cat01"].map(SERIES)
    df["CI指数"] = pd.to_numeric(df["$"], errors="coerce")
    df = df.dropna(subset=["CI指数"])

    # 直近 months か月に絞る
    latest_months = sorted(df["年月"].unique())[-months:]
    df = df[df["年月"].isin(latest_months)]
    return df[["年月", "系列", "CI指数"]].sort_values(["系列", "年月"]).reset_index(drop=True)


if __name__ == "__main__":
    ci = fetch_ci(12)
    for name in SERIES.values():
        group = ci[ci["系列"] == name]
        print(f"\n■ {name}")
        print(group[["年月", "CI指数"]].to_string(index=False))
