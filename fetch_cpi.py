"""e-Stat API から消費者物価指数（2025年基準・全国・月次）を取得する"""

import os
from datetime import date

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData"
STATS_DATA_ID = "0004052037"  # 消費者物価指数（2025年基準）

# 品目コード → 表示名
ITEMS = {
    "0001": "総合",
    "0161": "生鮮食品を除く総合",            # コアCPI
    "0178": "生鮮食品及びエネルギーを除く総合",  # コアコアCPI
}

# 表章項目コード → 列名
TABS = {
    "1": "指数",
    "3": "前年同月比",
}


def fetch_cpi(months: int = 12) -> pd.DataFrame:
    """全国の CPI（月次）の直近 months か月分を取得し、1行=1か月×1品目 の DataFrame で返す。

    列: 年月, 品目, 指数, 前年同月比(%)
    """
    # 公表の遅れ（約1か月）を考慮し、余裕をもって取得してから直近 months か月に絞る
    start_year = date.today().year - (months // 12) - 1
    app_id = os.getenv("ESTAT_APP_ID")
    if not app_id:
        raise RuntimeError(".env に ESTAT_APP_ID が設定されていません")

    params = {
        "appId": app_id,
        "statsDataId": STATS_DATA_ID,
        "cdArea": "00000",  # 全国
        "cdCat01": ",".join(ITEMS),
        "cdTab": ",".join(TABS),
        "cdTimeFrom": f"{start_year}000101",
        "metaGetFlg": "N",
    }
    res = requests.get(API_URL, params=params, timeout=30)
    res.raise_for_status()
    data = res.json()["GET_STATS_DATA"]

    status = data["RESULT"]["STATUS"]
    if status != 0:
        raise RuntimeError(f"e-Stat API エラー ({status}): {data['RESULT']['ERROR_MSG']}")

    values = data["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]
    df = pd.DataFrame(values)

    # 月次データのみ残す（時間コード: YYYY00MMMM。年・年度の行は除外）
    df = df[(df["@time"].str[4:6] == "00") & (df["@time"].str[6:8] != "00")]

    df["年月"] = pd.to_datetime(df["@time"].str[:4] + "-" + df["@time"].str[8:10] + "-01")
    df["品目"] = df["@cat01"].map(ITEMS)
    df["表章項目"] = df["@tab"].map(TABS)
    df["値"] = pd.to_numeric(df["$"], errors="coerce")

    df = (
        df.pivot_table(index=["年月", "品目"], columns="表章項目", values="値")
        .reset_index()
        .rename(columns={"前年同月比": "前年同月比(%)"})
        .sort_values(["品目", "年月"])
        .reset_index(drop=True)
    )
    df.columns.name = None

    # 直近 months か月に絞る
    latest_months = sorted(df["年月"].unique())[-months:]
    df = df[df["年月"].isin(latest_months)].reset_index(drop=True)
    return df[["年月", "品目", "指数", "前年同月比(%)"]]


if __name__ == "__main__":
    cpi = fetch_cpi(12)
    for item in ITEMS.values():
        group = cpi[cpi["品目"] == item]
        print(f"\n■ {item}")
        print(group[["年月", "指数", "前年同月比(%)"]].to_string(index=False))
