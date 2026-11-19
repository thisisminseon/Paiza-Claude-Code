import base64

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from fetch_ci import fetch_ci
from fetch_cpi import fetch_cpi

# ── 言語設定（URL の ?lang= で切り替え。既定は日本語） ──────────────
LANGS = {"ja": "日本語", "en": "English", "ko": "한국어", "zh": "中文"}
LANG = st.query_params.get("lang", "ja")
if LANG not in LANGS:
    LANG = "ja"

TEXT = {
    "title": {"ja": "国内の経済指標", "en": "Japan Economic Indicators", "ko": "일본 경제지표", "zh": "日本经济指标"},
    "nav_cpi": {"ja": "消費者物価指数", "en": "Consumer Prices", "ko": "소비자물가지수", "zh": "消费者物价指数"},
    "nav_ci": {"ja": "景気動向指数", "en": "Business Conditions", "ko": "경기동향지수", "zh": "景气动向指数"},
    "language": {"ja": "言語", "en": "Language", "ko": "언어", "zh": "语言"},
    "live": {"ja": "最新データ　{m}分", "en": "Latest data · {m}", "ko": "최신 데이터 · {m}", "zh": "最新数据 · {m}"},
    "hero_label": {"ja": "消費者物価指数（総合）前年同月比", "en": "Consumer Price Index (all items), year-on-year",
                   "ko": "소비자물가지수(종합) 전년 동월 대비", "zh": "消费者物价指数（综合）同比"},
    "panel_title": {"ja": "主要指標", "en": "Key indicators", "ko": "주요 지표", "zh": "主要指标"},
    "group_cpi": {"ja": "消費者物価指数 · 前年同月比", "en": "CPI · year-on-year",
                  "ko": "소비자물가지수 · 전년 동월 대비", "zh": "消费者物价指数 · 同比"},
    "group_ci": {"ja": "景気動向指数 CI · 2020年=100", "en": "Composite Index · 2020=100",
                 "ko": "경기동향지수 CI · 2020년=100", "zh": "景气动向指数 CI · 2020年=100"},
    "ticker_ci": {"ja": "CI一致", "en": "CI-C", "ko": "CI일치", "zh": "CI一致"},
    "cpi_title": {"ja": "消費者物価指数", "en": "Consumer Price Index", "ko": "소비자물가지수", "zh": "消费者物价指数"},
    "cpi_meta": {"ja": "全国・2025年基準", "en": "Nationwide · 2025 base", "ko": "전국 · 2025년 기준", "zh": "全国 · 2025年基准"},
    "ci_title": {"ja": "景気動向指数（CI）", "en": "Composite Index of Business Conditions",
                 "ko": "경기동향지수(CI)", "zh": "景气动向指数（CI）"},
    "ci_meta": {"ja": "内閣府・2020年=100", "en": "Cabinet Office · 2020=100", "ko": "내각부 · 2020년=100", "zh": "内阁府 · 2020年=100"},
    "yoy": {"ja": "前年同月比", "en": "YoY", "ko": "전년 동월비", "zh": "同比"},
    "index": {"ja": "指数", "en": "Index", "ko": "지수", "zh": "指数"},
    "view": {"ja": "表示", "en": "View", "ko": "표시", "zh": "显示"},
    "target": {"ja": "日銀目標 {t}%", "en": "BoJ target {t}%", "ko": "일본은행 목표 {t}%", "zh": "日本央行目标 {t}%"},
    "stats": {"ja": "統計サマリー", "en": "Summary statistics", "ko": "통계 요약", "zh": "统计摘要"},
    "table": {"ja": "データテーブル", "en": "Data table", "ko": "데이터 테이블", "zh": "数据表"},
    "latest": {"ja": "最新", "en": "Latest", "ko": "최신", "zh": "最新"},
    "mean": {"ja": "平均", "en": "Mean", "ko": "평균", "zh": "平均"},
    "std": {"ja": "標準偏差", "en": "Std. dev.", "ko": "표준편차", "zh": "标准差"},
    "high": {"ja": "最高", "en": "High", "ko": "최고", "zh": "最高"},
    "low": {"ja": "最低", "en": "Low", "ko": "최저", "zh": "最低"},
    "change12": {"ja": "12か月の変化", "en": "12-month change", "ko": "12개월 변화", "zh": "12个月变化"},
    "month": {"ja": "年月", "en": "Month", "ko": "연월", "zh": "年月"},
    "flat": {"ja": "横ばい", "en": "Flat", "ko": "보합", "zh": "持平"},
    "loading": {"ja": "e-Stat からデータを取得中…", "en": "Loading data from e-Stat…",
                "ko": "e-Stat에서 데이터를 불러오는 중…", "zh": "正在从 e-Stat 获取数据…"},
    "error": {"ja": "データを取得できませんでした: {e}", "en": "Could not load data: {e}",
              "ko": "데이터를 불러오지 못했습니다: {e}", "zh": "无法获取数据：{e}"},
    "source": {
        "ja": "出典：総務省統計局「消費者物価指数」（2025年基準）、内閣府「景気動向指数」",
        "en": "Sources: Statistics Bureau of Japan, “Consumer Price Index” (2025 base); Cabinet Office, “Indexes of Business Conditions”",
        "ko": "출처: 총무성 통계국 「소비자물가지수」(2025년 기준), 내각부 「경기동향지수」",
        "zh": "来源：日本总务省统计局《消费者物价指数》（2025年基准）、内阁府《景气动向指数》",
    },
    "disclaimer": {
        "ja": "このサービスは、政府統計総合窓口（e-Stat）のAPI機能を使用していますが、サービスの内容は国によって保証されたものではありません。",
        "en": "This service uses the API of e-Stat (Portal Site of Official Statistics of Japan), but its content is not guaranteed by the Government of Japan.",
        "ko": "이 서비스는 일본 정부통계 종합창구(e-Stat)의 API 기능을 사용하지만, 서비스 내용은 일본 정부가 보증하는 것이 아닙니다.",
        "zh": "本服务使用了日本政府统计综合窗口（e-Stat）的API功能，但服务内容并不受日本政府保证。",
    },
}

# ヒーローの説明文（総合の前年同月比から組み立てる）
LEAD = {
    "up": {"ja": "前月から<strong>{d}ポイント上昇</strong>しました。", "en": "Up <strong>{d} points</strong> from the previous month. ",
           "ko": "전월보다 <strong>{d}%p 상승</strong>했습니다. ", "zh": "较上月<strong>上升{d}个百分点</strong>。"},
    "down": {"ja": "前月から<strong>{d}ポイント低下</strong>しました。", "en": "Down <strong>{d} points</strong> from the previous month. ",
             "ko": "전월보다 <strong>{d}%p 하락</strong>했습니다. ", "zh": "较上月<strong>下降{d}个百分点</strong>。"},
    "same": {"ja": "前月と<strong>同じ水準</strong>でした。", "en": "<strong>Unchanged</strong> from the previous month. ",
             "ko": "전월과 <strong>같은 수준</strong>입니다. ", "zh": "与上月<strong>持平</strong>。"},
    "reach_n": {"ja": "<strong>{n}か月ぶり</strong>に日銀の物価目標である2%に達しています。",
                "en": "Inflation is back at the BoJ’s 2% target for the <strong>first time in {n} months</strong>.",
                "ko": "<strong>{n}개월 만에</strong> 일본은행 물가 목표인 2%에 도달했습니다.",
                "zh": "<strong>时隔{n}个月</strong>达到日本央行2%的物价目标。"},
    "reach_first": {"ja": "直近12か月で初めて日銀の物価目標である2%に達しました。",
                    "en": "It reached the BoJ’s 2% target for the first time in the past 12 months.",
                    "ko": "최근 12개월 중 처음으로 일본은행 물가 목표인 2%에 도달했습니다.",
                    "zh": "为近12个月来首次达到日本央行2%的物价目标。"},
    "below_n": {"ja": "<strong>{n}か月ぶり</strong>に日銀の物価目標である2%を下回りました。",
                "en": "It fell below the BoJ’s 2% target for the <strong>first time in {n} months</strong>.",
                "ko": "<strong>{n}개월 만에</strong> 일본은행 물가 목표인 2%를 밑돌았습니다.",
                "zh": "<strong>时隔{n}个月</strong>跌破日本央行2%的物价目标。"},
    "below_first": {"ja": "直近12か月で初めて日銀の物価目標である2%を下回りました。",
                    "en": "It fell below the BoJ’s 2% target for the first time in the past 12 months.",
                    "ko": "최근 12개월 중 처음으로 일본은행 물가 목표인 2%를 밑돌았습니다.",
                    "zh": "为近12个月来首次跌破日本央行2%的物价目标。"},
    "stay_above": {"ja": "日銀の物価目標である2%以上の水準が続いています。",
                   "en": "It remains at or above the BoJ’s 2% target.",
                   "ko": "일본은행 물가 목표인 2% 이상 수준이 이어지고 있습니다.",
                   "zh": "持续处于日本央行2%物价目标以上的水平。"},
    "stay_below": {"ja": "日銀の物価目標である2%を下回る水準が続いています。",
                   "en": "It remains below the BoJ’s 2% target.",
                   "ko": "일본은행 물가 목표인 2%를 밑도는 수준이 이어지고 있습니다.",
                   "zh": "持续低于日本央行2%的物价目标。"},
}

MONTH_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def T(key: str, **kw) -> str:
    return TEXT[key][LANG].format(**kw)


st.set_page_config(page_title=T("title"), page_icon=":material/monitoring:", layout="wide")

# ── デザイントークン ──────────────────────────────────
INK = "#0B1220"      # 本文
INK_2 = "#425066"    # 補助テキスト
MUTED = "#8A94A6"    # 注記・軸ラベル
LINE = "#E6EAF0"     # 罫線
GRID = "#EEF1F6"     # グラフのグリッド
FONT = ("'Pretendard JP Variable', 'Pretendard Variable', 'Hiragino Sans', 'Noto Sans JP', "
        "'PingFang SC', 'Microsoft YaHei', sans-serif")
TARGET = 2.0         # 日銀の物価安定の目標（消費者物価の前年比上昇率）

# 消費者物価指数（列「品目」）
CPI_SERIES = [
    {"item": "総合", "color": "#2a78d6", "width": 3,
     "name": {"ja": "総合", "en": "All items", "ko": "종합", "zh": "综合"},
     "sub": {"ja": "すべての品目", "en": "Headline", "ko": "전체 품목", "zh": "全部品目"}},
    {"item": "生鮮食品を除く総合", "color": "#eb6834", "width": 2,
     "name": {"ja": "コア", "en": "Core", "ko": "코어", "zh": "核心"},
     "sub": {"ja": "生鮮食品を除く", "en": "Excl. fresh food", "ko": "신선식품 제외", "zh": "不含生鲜食品"}},
    {"item": "生鮮食品及びエネルギーを除く総合", "color": "#1baf7a", "width": 2,
     "name": {"ja": "コアコア", "en": "Core-core", "ko": "코어코어", "zh": "核心核心"},
     "sub": {"ja": "生鮮・エネルギー除く", "en": "Excl. fresh food & energy", "ko": "신선식품·에너지 제외", "zh": "不含生鲜食品和能源"}},
]
# 景気動向指数 CI（列「系列」）
CI_SERIES = [
    {"item": "先行指数", "color": "#008300", "width": 2,
     "name": {"ja": "先行指数", "en": "Leading", "ko": "선행지수", "zh": "先行指数"},
     "sub": {"ja": "景気の先行き", "en": "Outlook", "ko": "경기 전망", "zh": "景气前景"}},
    {"item": "一致指数", "color": "#6250d6", "width": 3,
     "name": {"ja": "一致指数", "en": "Coincident", "ko": "일치지수", "zh": "一致指数"},
     "sub": {"ja": "景気の現状", "en": "Current conditions", "ko": "경기 현황", "zh": "景气现状"}},
    {"item": "遅行指数", "color": "#e34948", "width": 2,
     "name": {"ja": "遅行指数", "en": "Lagging", "ko": "후행지수", "zh": "滞后指数"},
     "sub": {"ja": "景気の事後確認", "en": "Confirms past trends", "ko": "사후 확인", "zh": "事后确认"}},
]

# Lucide Icons（ISC License） https://lucide.dev
ICONS = {
    "arrow-up": '<path d="m5 12 7-7 7 7"/><path d="M12 19V5"/>',
    "arrow-down": '<path d="M12 5v14"/><path d="m19 12-7 7-7-7"/>',
    "minus": '<path d="M5 12h14"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>',
    "chevron-down": '<path d="m6 9 6 6 6-6"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
}


def svg_img(svg: str, width: int, height: int, cls: str = "ic") -> str:
    """st.html は <svg> タグを除去するため、data URI の <img> として埋め込む"""
    src = "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f'<img class="{cls}" src="{src}" width="{width}" height="{height}" alt="">'


def icon(name: str, size: int = 16, stroke: float = 2, color: str = INK_2) -> str:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="none" stroke="{color}" stroke-width="{stroke}" stroke-linecap="round" '
        f'stroke-linejoin="round">{ICONS[name]}</svg>'
    )
    return svg_img(svg, size, size)


CSS = """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-jp-dynamic-subset.min.css');
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;600;700&display=swap');

:root {
  --ink: #0B1220; --ink-2: #425066; --muted: #8A94A6; --line: #E6EAF0;
  --page: #F6F8FB; --card: #FFFFFF; --night: #0B1220; --accent: #3B2BE0;
  --font: 'Pretendard JP Variable', 'Pretendard Variable', -apple-system, BlinkMacSystemFont,
          'Hiragino Sans', 'Noto Sans JP', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif;
  --mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  --shadow-float: 0 50px 100px -20px rgba(50, 50, 93, 0.25), 0 30px 60px -30px rgba(0, 0, 0, 0.30);
  --shadow-card: 0 1px 2px rgba(16, 24, 40, 0.04), 0 16px 40px -16px rgba(50, 50, 93, 0.18);
}

.stApp, .stApp *:not([data-testid="stIconMaterial"]) {
  font-family: var(--font) !important;
  -webkit-font-smoothing: antialiased;
}
.stApp .mono, .stApp .mono * { font-family: var(--mono) !important; }

/* ── Streamlit 標準 UI の整理 ── */
header[data-testid="stHeader"] { display: none; }
[data-testid="stAppViewContainer"], [data-testid="stMain"] { overflow-x: hidden; }
[data-testid="stMainBlockContainer"] { max-width: 1128px; padding: 0 24px; }
@media (max-width: 640px) { [data-testid="stMainBlockContainer"] { padding: 0 16px; } }

/* 画面幅いっぱいに広げるセクション */
.bleed { position: relative; width: 100vw; left: 50%; margin-left: -50vw; }
.wrap { position: relative; max-width: 1128px; margin: 0 auto; padding: 0 24px; }
@media (max-width: 640px) { .wrap { padding: 0 16px; } }
.ic { display: block; flex-shrink: 0; }

/* ── ヒーロー ── */
/* 背景はセクション全体を覆い、左側のテキストが必ずグラデーション上に来るようにする */
.hero { padding-bottom: 104px; }
.hero-bg {
  position: absolute; left: 0; right: 0; top: 0; bottom: 0;
  background:
    radial-gradient(circle at 12% 28%, #3B2BE0 0%, transparent 46%),
    radial-gradient(circle at 82% 12%, #FF5E7E 0%, transparent 42%),
    radial-gradient(circle at 92% 78%, #FFB443 0%, transparent 46%),
    radial-gradient(circle at 48% 92%, #19C3F5 0%, transparent 42%),
    linear-gradient(115deg, #2F22C9 0%, #6E46FF 34%, #FF6A88 70%, #FFB347 100%);
  background-size: 180% 180%;
  animation: drift 18s ease-in-out infinite alternate;
  clip-path: polygon(0 0, 100% 0, 100% 76%, 0 100%);
}
@keyframes drift { from { background-position: 0% 30%; } to { background-position: 100% 70%; } }
.hero-lines {
  position: absolute; top: 0; bottom: 0; left: 50%; width: min(1080px, calc(100% - 48px));
  transform: translateX(-50%); pointer-events: none;
  border-left: 1px dashed rgba(255, 255, 255, 0.22); border-right: 1px dashed rgba(255, 255, 255, 0.22);
  background: linear-gradient(90deg, transparent calc(50% - 0.5px), rgba(255, 255, 255, 0.16) 50%, transparent calc(50% + 0.5px));
}

/* グローバルナビ（言語メニューがパネルより前面に来るよう z-index を指定） */
.gnb { position: relative; z-index: 20; display: flex; align-items: center; justify-content: space-between;
       gap: 12px; height: 76px; }
.wordmark { font-size: 20px; font-weight: 800; letter-spacing: -0.02em; color: #fff; white-space: nowrap; }
.gnb-right { display: flex; align-items: center; gap: 8px; }
.gnb-nav { display: flex; gap: 4px; }
.gnb-nav a { padding: 8px 14px; border-radius: 999px; color: rgba(255, 255, 255, 0.88) !important;
             font-size: 14px; font-weight: 600; text-decoration: none !important; transition: background 0.2s; }
.gnb-nav a:hover { background: rgba(255, 255, 255, 0.16); }

/* 言語選択ドロップダウン */
.lang { position: relative; }
.lang summary { list-style: none; display: inline-flex; align-items: center; gap: 6px; padding: 8px 10px 8px 12px;
                border-radius: 999px; background: rgba(255, 255, 255, 0.16); border: 1px solid rgba(255, 255, 255, 0.28);
                color: #fff; font-size: 13px; font-weight: 600; cursor: pointer; user-select: none;
                backdrop-filter: blur(8px); transition: background 0.2s; }
.lang summary::-webkit-details-marker { display: none; }
.lang summary:hover, .lang[open] summary { background: rgba(255, 255, 255, 0.26); }
.lang[open] summary .chev { transform: rotate(180deg); }
.lang .chev { transition: transform 0.2s; }
.lang-menu { position: absolute; right: 0; top: calc(100% + 8px); min-width: 188px; padding: 6px;
             background: var(--card); border-radius: 14px; box-shadow: var(--shadow-float); }
.lang-menu a { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 10px 12px;
               border-radius: 10px; color: var(--ink) !important; font-size: 14px; font-weight: 600;
               text-decoration: none !important; }
.lang-menu a:hover { background: var(--page); }
.lang-menu a.on { color: var(--accent) !important; background: #F1EFFF; }
.lang-code { font-size: 11px; font-weight: 600; letter-spacing: 0.08em; color: var(--muted); }

.hero-grid { display: grid; grid-template-columns: 1.1fr 1fr; gap: 56px; align-items: center; padding-top: 48px; }
.live { display: inline-flex; align-items: center; gap: 8px; padding: 7px 14px 7px 12px; border-radius: 999px;
        background: rgba(255, 255, 255, 0.16); border: 1px solid rgba(255, 255, 255, 0.28);
        backdrop-filter: blur(8px); color: #fff; font-size: 13px; font-weight: 600; }
.pulse { width: 8px; height: 8px; border-radius: 50%; background: #7CFFB2; position: relative; }
.pulse::after { content: ""; position: absolute; inset: -4px; border-radius: 50%;
                border: 2px solid #7CFFB2; animation: pulse 1.8s ease-out infinite; }
@keyframes pulse { from { transform: scale(0.6); opacity: 1; } to { transform: scale(1.6); opacity: 0; } }

.hero-label { margin-top: 28px; font-size: 18px; font-weight: 600; color: rgba(255, 255, 255, 0.88); }
.display { font-size: clamp(96px, 13vw, 176px); font-weight: 800; letter-spacing: -0.06em; line-height: 0.92;
           color: #fff; font-variant-numeric: tabular-nums; margin: 10px 0 0 -6px; }
.display span { font-size: 0.42em; font-weight: 700; letter-spacing: -0.02em; margin-left: 6px; }
.lead { margin-top: 24px; max-width: 480px; font-size: 18px; line-height: 1.7; color: rgba(255, 255, 255, 0.92); }
.lead strong { color: #fff; font-weight: 700; }

/* ヒーロー右：主要指標パネル */
.panel { background: var(--card); border-radius: 20px; padding: 26px 28px 14px; box-shadow: var(--shadow-float); }
@media (min-width: 901px) { .panel { transform: translateY(96px); } }
.panel-head { display: flex; align-items: baseline; justify-content: space-between; }
.panel-title { font-size: 18px; font-weight: 800; color: var(--ink); letter-spacing: -0.02em; }
.panel-kicker { font-size: 11px; font-weight: 600; letter-spacing: 0.1em; color: var(--muted); }
.group-label { margin-top: 18px; font-size: 11px; font-weight: 600; letter-spacing: 0.08em; color: var(--muted); }
.stApp ul.rows { list-style: none; margin: 4px 0 0 !important; padding: 0 !important; }
.stApp li.row { display: flex; align-items: center; gap: 14px; margin: 0 !important; padding: 11px 0;
                border-top: 1px solid var(--line); }
.stApp li.row:first-child { border-top: none; }
.row-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.row-main { flex: 1; min-width: 0; }
.row-name { font-size: 15px; font-weight: 700; color: var(--ink); }
.row-sub { font-size: 12px; color: var(--muted); margin-top: 1px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.row-val { text-align: right; min-width: 72px; }
.row-val .v { font-size: 20px; font-weight: 800; letter-spacing: -0.03em; color: var(--ink); font-variant-numeric: tabular-nums; }
.row-val .d { display: inline-flex; align-items: center; gap: 2px; font-size: 12px; font-weight: 600;
              color: var(--ink-2); font-variant-numeric: tabular-nums; }

/* ── ティッカー ── */
.ticker { display: flex; height: 52px; margin-top: 40px; background: var(--night); color: #E6EAF2; font-size: 13px; }
.ticker-label { flex-shrink: 0; display: flex; align-items: center; padding: 0 20px; background: #fff;
                color: var(--night); font-weight: 700; letter-spacing: 0.06em; font-size: 12px; }
.ticker-view { flex: 1; overflow: hidden; display: flex; align-items: center;
               -webkit-mask-image: linear-gradient(90deg, transparent, #000 48px, #000 calc(100% - 48px), transparent);
               mask-image: linear-gradient(90deg, transparent, #000 48px, #000 calc(100% - 48px), transparent); }
.ticker-track { display: inline-flex; gap: 48px; padding-left: 48px; white-space: nowrap;
                animation: tick 70s linear infinite; }
.t-item { display: inline-flex; align-items: baseline; gap: 10px; }
.t-date { color: #7D879A; }
.t-key { color: #7D879A; font-size: 11px; }
.t-val { color: #fff; font-weight: 700; }
.t-sep { color: #2A3347; }
.t-up { color: #FF9A85; } .t-down { color: #6FD8FF; } .t-flat { color: #7D879A; }
@keyframes tick { from { transform: translateX(0); } to { transform: translateX(-50%); } }

/* ── 指標セクション（カード） ── */
[class*="st-key-card_"] { background: var(--card); border-radius: 20px; padding: 32px 32px 28px;
                          box-shadow: var(--shadow-card); margin-top: 40px; }
.kicker { font-size: 11px; font-weight: 600; letter-spacing: 0.12em; color: var(--muted); }
.card-title { margin-top: 6px; font-size: 26px; font-weight: 800; letter-spacing: -0.03em; color: var(--ink); }
.card-meta { margin-top: 4px; font-size: 13px; color: var(--muted); }
.legend { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px; }
.lg { display: inline-flex; align-items: center; gap: 8px; padding: 6px 12px; border-radius: 999px;
      background: var(--page); font-size: 13px; font-weight: 600; color: var(--ink-2); }
.lg i { display: inline-block; width: 16px; height: 3px; border-radius: 2px; }
.sub-h { display: flex; align-items: baseline; gap: 10px; margin-top: 12px; padding-top: 24px;
         border-top: 1px solid var(--line); font-size: 17px; font-weight: 800; letter-spacing: -0.02em; color: var(--ink); }
.sub-h span { font-size: 11px; font-weight: 600; letter-spacing: 0.1em; color: var(--muted); }

.st-key-view { align-self: flex-end; }
.st-key-view [role="radiogroup"] { gap: 2px; padding: 4px; background: #EEF1F6; border-radius: 12px; }
.st-key-view button { border: none !important; background: transparent !important; box-shadow: none !important;
                      border-radius: 9px !important; min-height: 36px; padding: 4px 16px !important; }
.st-key-view button, .st-key-view button * { color: var(--muted) !important; font-weight: 700 !important; font-size: 14px !important; }
.st-key-view button[aria-checked="true"] { background: var(--card) !important;
                                            box-shadow: 0 1px 3px rgba(11, 18, 32, 0.12) !important; }
.st-key-view button[aria-checked="true"], .st-key-view button[aria-checked="true"] * { color: var(--ink) !important; }

/* 統計サマリー */
.stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.stat { background: var(--page); border-radius: 16px; padding: 18px 20px 16px; }
.stat-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.stat-name { display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 700; color: var(--ink); }
.stat-name i { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.stat-latest { font-size: 20px; font-weight: 800; letter-spacing: -0.02em; color: var(--ink); font-variant-numeric: tabular-nums; white-space: nowrap; }
.stat-latest small { font-size: 11px; font-weight: 600; color: var(--muted); margin-right: 6px; letter-spacing: 0; }
.stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px 16px; margin-top: 14px; padding-top: 14px;
             border-top: 1px solid var(--line); }
.stat-k { font-size: 12px; color: var(--muted); }
.stat-v { margin-top: 2px; font-size: 17px; font-weight: 700; color: var(--ink); font-variant-numeric: tabular-nums; }
.stat-v small { display: block; font-size: 11px; font-weight: 500; color: var(--muted); }
.stat-foot { margin-top: 14px; font-size: 12px; color: var(--ink-2); }
.stat-foot b { font-weight: 700; color: var(--ink); font-variant-numeric: tabular-nums; }

[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 14px; overflow: hidden; }

/* ── フッター ── */
.foot { margin-top: 72px; padding: 48px 0 56px; background: var(--night); color: rgba(255, 255, 255, 0.55);
        font-size: 12px; line-height: 1.8; }
.foot-brand { font-size: 18px; font-weight: 800; letter-spacing: -0.02em; color: #fff; margin-bottom: 16px; }
.foot-src { color: rgba(255, 255, 255, 0.8); font-weight: 600; }
.foot-meta { margin-top: 20px; font-size: 11px; letter-spacing: 0.08em; color: rgba(255, 255, 255, 0.4); }

/* ── タブレット・スマホ ── */
@media (max-width: 900px) {
  .hero { padding-bottom: 48px; }
  .hero-grid { grid-template-columns: 1fr; gap: 40px; padding-top: 32px; }
  .hero-bg { clip-path: polygon(0 0, 100% 0, 100% 96%, 0 100%); }
  .lead { max-width: none; }
  .stats { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
  .gnb { height: 64px; }
  .gnb-nav { display: none; }
  .wordmark { font-size: 18px; }
  .hero-label { font-size: 15px; margin-top: 22px; }
  .display { font-size: 96px; }
  .lead { font-size: 16px; }
  .panel { padding: 22px 20px 10px; border-radius: 18px; }
  .ticker { margin-top: 32px; height: 46px; font-size: 12px; }
  .ticker-label { padding: 0 14px; font-size: 11px; }
  [class*="st-key-card_"] { padding: 22px 16px 18px; margin-top: 28px; border-radius: 18px; }
  .card-title { font-size: 22px; }
  .st-key-view { align-self: flex-start; }
  .foot { margin-top: 48px; padding: 36px 0 44px; }
}
@media (max-width: 420px) { .row .spark { display: none; } }

/* 動きを減らす設定の端末ではアニメーションを止める */
@media (prefers-reduced-motion: reduce) {
  .hero-bg, .ticker-track, .pulse::after { animation: none; }
}
</style>
"""


# ── データ ───────────────────────────────────────────
@st.cache_data(ttl=60 * 60 * 6, show_spinner=False)
def load_cpi() -> pd.DataFrame:
    return fetch_cpi(12)


@st.cache_data(ttl=60 * 60 * 6, show_spinner=False)
def load_ci() -> pd.DataFrame:
    return fetch_ci(12)


# ── 表示用ヘルパー ─────────────────────────────────────
def name(s) -> str:
    return s["name"][LANG]


def sub(s) -> str:
    return s["sub"][LANG]


def ym(d) -> str:
    """日付を言語に合わせた「年月」表記にする（Windows では strftime の %-m が使えないため自前で整形）"""
    d = pd.Timestamp(d)
    if LANG == "en":
        return f"{MONTH_EN[d.month - 1]} {d.year}"
    if LANG == "ko":
        return f"{d.year}년 {d.month}월"
    return f"{d.year}年{d.month}月"


def month_label(d) -> str:
    d = pd.Timestamp(d)
    return {"en": MONTH_EN[d.month - 1], "ko": f"{d.month}월"}.get(LANG, f"{d.month}月")


HOVER_FORMAT = {"ja": "%Y年%-m月", "zh": "%Y年%-m月", "ko": "%Y년 %-m월", "en": "%b %Y"}


def ym_dot(d) -> str:
    d = pd.Timestamp(d)
    return f"{d.year}.{d.month:02d}"


def period(df) -> str:
    months = sorted(df["年月"].unique())
    sep = " – " if LANG == "en" else "〜"
    return f"{ym(months[0])}{sep}{ym(months[-1])}"


def series_frame(df, key_col, item, value_col) -> pd.DataFrame:
    return df[df[key_col] == item].sort_values("年月")[["年月", value_col]].dropna()


def delta_html(diff: float, unit: str = "pt") -> str:
    if diff > 0:
        return f'{icon("arrow-up", 12, 2.5)}{diff:.1f}{unit}'
    if diff < 0:
        return f'{icon("arrow-down", 12, 2.5)}{abs(diff):.1f}{unit}'
    return f'{icon("minus", 12, 2.5)}{T("flat")}'


def sparkline(values, color, w=80, h=30, pad=4) -> str:
    vmin, vmax = min(values), max(values)
    rng = (vmax - vmin) or 1
    step = (w - 2 * pad) / (len(values) - 1)
    pts = [(pad + i * step, pad + (vmax - v) * (h - 2 * pad) / rng) for i, v in enumerate(values)]
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    lx, ly = pts[-1]
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
        f'<polyline points="{poly}" fill="none" stroke="{color}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="3.5" fill="{color}" stroke="#fff" stroke-width="2"/></svg>'
    )
    return svg_img(svg, w, h, cls="spark")


def headline_text(values) -> str:
    """総合の前年同月比から、ヒーローの説明文を組み立てる"""
    now, before = values[-1], values[-2]
    diff = round(now - before, 1)
    key = "up" if diff > 0 else "down" if diff < 0 else "same"
    s1 = LEAD[key][LANG].format(d=f"{abs(diff):.1f}")

    def months_since(cond):
        for i in range(len(values) - 2, -1, -1):
            if cond(values[i]):
                return len(values) - 1 - i
        return None

    if now >= TARGET > before:
        n = months_since(lambda v: v >= TARGET)
        s2 = LEAD["reach_n"][LANG].format(n=n) if n else LEAD["reach_first"][LANG]
    elif now < TARGET <= before:
        n = months_since(lambda v: v < TARGET)
        s2 = LEAD["below_n"][LANG].format(n=n) if n else LEAD["below_first"][LANG]
    elif now >= TARGET:
        s2 = LEAD["stay_above"][LANG]
    else:
        s2 = LEAD["stay_below"][LANG]
    return s1 + s2


def lang_menu_html() -> str:
    links = "".join(
        f'<a href="?lang={code}" class="{"on" if code == LANG else ""}" hreflang="{code}">'
        f'<span>{label}</span>'
        + (icon("check", 15, 2.5, "#3B2BE0") if code == LANG else f'<span class="lang-code mono">{code.upper()}</span>')
        + "</a>"
        for code, label in LANGS.items()
    )
    return f"""
<details class="lang">
  <summary aria-label="{T('language')}">{icon("globe", 15, 2, "#FFFFFF")}<span>{LANGS[LANG]}</span>{icon("chevron-down", 14, 2.5, "#FFFFFF").replace('class="ic"', 'class="ic chev"')}</summary>
  <div class="lang-menu">{links}</div>
</details>"""


def panel_rows(df, series, key_col, value_col, unit) -> str:
    rows = []
    for s in series:
        values = series_frame(df, key_col, s["item"], value_col)[value_col].tolist()
        diff = round(values[-1] - values[-2], 1)
        rows.append(f"""
<li class="row">
  <span class="row-dot" style="background:{s['color']}"></span>
  <div class="row-main"><div class="row-name">{name(s)}</div><div class="row-sub">{sub(s)}</div></div>
  {sparkline(values, s['color'])}
  <div class="row-val"><div class="v">{values[-1]:.1f}{unit}</div><div class="d">{delta_html(diff)}</div></div>
</li>""")
    return "".join(rows)


def hero_html(cpi, ci, latest) -> str:
    total = series_frame(cpi, "品目", "総合", "前年同月比(%)")["前年同月比(%)"].tolist()
    return f"""
<section class="hero bleed">
  <div class="hero-bg"></div>
  <div class="hero-lines"></div>
  <div class="wrap">
    <nav class="gnb">
      <div class="wordmark" role="heading" aria-level="1">{T("title")}</div>
      <div class="gnb-right">
        <div class="gnb-nav"><a href="#cpi">{T("nav_cpi")}</a><a href="#ci">{T("nav_ci")}</a></div>
        {lang_menu_html()}
      </div>
    </nav>
    <div class="hero-grid">
      <div>
        <span class="live"><span class="pulse"></span>{T("live", m=ym(latest))}</span>
        <div class="hero-label">{T("hero_label")}</div>
        <div class="display">{total[-1]:.1f}<span>%</span></div>
        <div class="lead">{headline_text(total)}</div>
      </div>
      <div class="panel">
        <div class="panel-head">
          <span class="panel-title">{T("panel_title")}</span>
          <span class="panel-kicker mono">{ym_dot(latest)}</span>
        </div>
        <div class="group-label">{T("group_cpi")}</div>
        <ul class="rows">{panel_rows(cpi, CPI_SERIES, "品目", "前年同月比(%)", "%")}</ul>
        <div class="group-label">{T("group_ci")}</div>
        <ul class="rows">{panel_rows(ci, CI_SERIES, "系列", "CI指数", "")}</ul>
      </div>
    </div>
  </div>
</section>"""


def ticker_html(cpi, ci) -> str:
    c = series_frame(cpi, "品目", "総合", "前年同月比(%)").set_index("年月")["前年同月比(%)"]
    k = series_frame(ci, "系列", "一致指数", "CI指数").set_index("年月")["CI指数"]

    def delta(cur, prev):
        if prev is None:
            return ""
        diff = round(cur - prev, 1)
        cls, mark = ("t-up", "▲") if diff > 0 else ("t-down", "▼") if diff < 0 else ("t-flat", "―")
        return f'<span class="{cls}">{mark}{abs(diff):.1f}</span>'

    items = []
    months = sorted(set(c.index) | set(k.index))
    for i, m in enumerate(months):
        parts = [f'<span class="t-date">{ym_dot(m)}</span>']
        if m in c.index:
            prev = c.get(months[i - 1]) if i > 0 else None
            parts.append(f'<span class="t-key">CPI</span><span class="t-val">{c[m]:.1f}%</span>{delta(c[m], prev)}')
        if m in k.index:
            prev = k.get(months[i - 1]) if i > 0 else None
            parts.append(f'<span class="t-sep">/</span><span class="t-key">{T("ticker_ci")}</span>'
                         f'<span class="t-val">{k[m]:.1f}</span>{delta(k[m], prev)}')
        items.append(f'<span class="t-item">{"".join(parts)}</span>')
    track = "".join(items)
    return f"""
<section class="ticker bleed mono">
  <div class="ticker-label">MONTHLY</div>
  <div class="ticker-view"><div class="ticker-track">{track}{track}</div></div>
</section>"""


def legend_html(series) -> str:
    return '<div class="legend">' + "".join(
        f'<span class="lg"><i style="background:{s["color"]}"></i>{name(s)}</span>' for s in series
    ) + "</div>"


def line_chart(df, series, key_col, value_col, unit, target=None) -> go.Figure:
    months = [pd.Timestamp(m) for m in sorted(df["年月"].unique())]
    # 目盛りは最新月から 2か月おき（スマホでも重ならないように）
    ticks = months[::-1][::2][::-1]
    ticktext = [
        f"{month_label(d)}<br>{d.year}" if (i == 0 or d.month == 1) else month_label(d)
        for i, d in enumerate(ticks)
    ]

    fig = go.Figure()
    for s in series:
        d = series_frame(df, key_col, s["item"], value_col)
        n = len(d)
        fig.add_trace(
            go.Scatter(
                x=d["年月"],
                y=d[value_col],
                name=name(s),
                mode="lines+markers",
                line=dict(color=s["color"], width=s["width"]),
                # 最新月だけ点を表示
                marker=dict(size=[0] * (n - 1) + [10], color=s["color"], line=dict(width=2, color="#FFFFFF")),
                hovertemplate=f"{name(s)}  <b>%{{y:.1f}}{unit}</b><extra></extra>",
            )
        )

    if target is not None:
        fig.add_hline(
            y=target,
            line=dict(color="#B4BCC9", width=1, dash="dash"),
            annotation_text=T("target", t=f"{target:g}"),
            annotation_position="top left",
            annotation_font=dict(size=11, color=MUTED, family=FONT),
        )

    fig.update_layout(
        height=360,
        margin=dict(l=0, r=0, t=12, b=0),
        font=dict(family=FONT, size=12, color=MUTED),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=LINE, font=dict(family=FONT, size=13, color=INK)),
        dragmode=False,  # スマホでのスクロールを妨げないようにする
        showlegend=False,  # 凡例は HTML で表示
        xaxis=dict(
            tickvals=ticks,
            ticktext=ticktext,
            hoverformat=HOVER_FORMAT[LANG],
            range=[months[0] - pd.Timedelta(days=12), months[-1] + pd.Timedelta(days=12)],
            showgrid=False,
            showline=False,
            ticks="",
            fixedrange=True,
            automargin=True,
            showspikes=True,
            spikemode="across",
            spikethickness=1,
            spikecolor="#C9D0DB",
            spikedash="solid",
        ),
        yaxis=dict(
            side="right",
            ticksuffix=unit,
            tickformat=".1f",
            gridcolor=GRID,
            zeroline=False,
            fixedrange=True,
            automargin=True,
        ),
    )
    return fig


def stats_html(df, series, key_col, value_col, unit) -> str:
    """系列ごとの統計サマリー（最新・平均・標準偏差・最高・最低・12か月の変化）"""
    cards = []
    for s in series:
        d = series_frame(df, key_col, s["item"], value_col)
        v = d[value_col]
        hi, lo = d.loc[v.idxmax()], d.loc[v.idxmin()]
        change = v.iloc[-1] - v.iloc[0]
        cards.append(f"""
<div class="stat">
  <div class="stat-head">
    <span class="stat-name"><i style="background:{s['color']}"></i>{name(s)}</span>
    <span class="stat-latest"><small>{T("latest")}</small>{v.iloc[-1]:.1f}{unit}</span>
  </div>
  <div class="stat-grid">
    <div><div class="stat-k">{T("mean")}</div><div class="stat-v">{v.mean():.2f}{unit}</div></div>
    <div><div class="stat-k">{T("std")}</div><div class="stat-v">{v.std():.2f}</div></div>
    <div><div class="stat-k">{T("high")}</div><div class="stat-v">{hi[value_col]:.1f}{unit}<small>{ym(hi['年月'])}</small></div></div>
    <div><div class="stat-k">{T("low")}</div><div class="stat-v">{lo[value_col]:.1f}{unit}<small>{ym(lo['年月'])}</small></div></div>
  </div>
  <div class="stat-foot">{T("change12")} <b>{change:+.1f}{'pt' if unit == '%' else ''}</b>（{ym(d['年月'].iloc[0])} → {ym(d['年月'].iloc[-1])}）</div>
</div>""")
    return f'<div class="stats">{"".join(cards)}</div>'


def wide_table(df, series, key_col, value_col) -> pd.DataFrame:
    table = df.pivot_table(index="年月", columns=key_col, values=value_col)
    table = table[[s["item"] for s in series]].sort_index(ascending=False)
    table.columns = [name(s) for s in series]
    table.index = [ym(d) for d in table.index]
    table.index.name = T("month")
    return table


def data_table(table: pd.DataFrame, unit: str) -> None:
    fmt = "%.1f%%" if unit == "%" else "%.1f"
    st.dataframe(
        table,
        width="stretch",
        height=(len(table) + 1) * 35 + 3,
        column_config={c: st.column_config.NumberColumn(format=fmt) for c in table.columns},
    )


# ── 画面 ─────────────────────────────────────────────
st.html(CSS)

try:
    with st.spinner(T("loading")):
        cpi = load_cpi()
        ci = load_ci()
except Exception as e:
    st.error(T("error", e=e))
    st.stop()

latest = max(cpi["年月"])

st.html(hero_html(cpi, ci, latest))
st.html(ticker_html(cpi, ci))

# 01 消費者物価指数
with st.container(key="card_cpi"):
    head_l, head_r = st.columns([3, 2], vertical_alignment="bottom")
    head_l.html(f"""
<div id="cpi" class="kicker mono">01 / CONSUMER PRICE INDEX</div>
<div class="card-title">{T("cpi_title")}</div>
<div class="card-meta">{T("cpi_meta")}　{period(cpi)}</div>""")
    with head_r:
        view = st.segmented_control(
            T("view"), ["yoy", "index"], default="yoy", format_func=T,
            label_visibility="collapsed", key="view",
        ) or "yoy"

    col, unit = ("前年同月比(%)", "%") if view == "yoy" else ("指数", "")
    st.html(legend_html(CPI_SERIES))
    st.plotly_chart(
        line_chart(cpi, CPI_SERIES, "品目", col, unit, target=TARGET if view == "yoy" else None),
        theme=None, width="stretch", config={"displayModeBar": False},
    )
    st.html(f'<div class="sub-h">{T("stats")}<span class="mono">{T(view)} / 12M</span></div>')
    st.html(stats_html(cpi, CPI_SERIES, "品目", col, unit))
    st.html(f'<div class="sub-h">{T("table")}<span class="mono">{T(view)}</span></div>')
    data_table(wide_table(cpi, CPI_SERIES, "品目", col), unit)

# 02 景気動向指数
with st.container(key="card_ci"):
    st.html(f"""
<div id="ci" class="kicker mono">02 / COMPOSITE INDEX</div>
<div class="card-title">{T("ci_title")}</div>
<div class="card-meta">{T("ci_meta")}　{period(ci)}</div>""")
    st.html(legend_html(CI_SERIES))
    st.plotly_chart(
        line_chart(ci, CI_SERIES, "系列", "CI指数", ""),
        theme=None, width="stretch", config={"displayModeBar": False},
    )
    st.html(f'<div class="sub-h">{T("stats")}<span class="mono">CI / 12M</span></div>')
    st.html(stats_html(ci, CI_SERIES, "系列", "CI指数", ""))
    st.html(f'<div class="sub-h">{T("table")}<span class="mono">CI</span></div>')
    data_table(wide_table(ci, CI_SERIES, "系列", "CI指数"), "")

# e-Stat API 利用規約のクレジット表記（日本語以外では原文も併記）
disclaimer = T("disclaimer")
if LANG != "ja":
    disclaimer += f"<br>{TEXT['disclaimer']['ja']}"

st.html(f"""
<footer class="foot bleed">
  <div class="wrap">
    <div class="foot-brand">{T("title")}</div>
    <div class="foot-src">{T("source")}</div>
    <div>{disclaimer}</div>
    <div class="foot-meta mono">DATA SOURCE: E-STAT API · STATSDATAID 0004052037 / 0003446461</div>
  </div>
</footer>
""")
