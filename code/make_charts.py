# -*- coding: utf-8 -*-
"""
维界投影·电子价签(ESL)中台 — 可视化图表生成脚本
读取 data/ 下清洗后的 CSV，输出 images/ 下 12 张 PNG（300dpi、白底、中文）。
运行：python make_charts.py
依赖：matplotlib、pandas、PIL
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import pandas as pd
from PIL import Image

# ---------- 路径 ----------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
IMG_DIR = os.path.join(BASE_DIR, "images")
os.makedirs(IMG_DIR, exist_ok=True)

# ---------- 全局视觉规范 ----------
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["savefig.facecolor"] = "white"
plt.rcParams["figure.facecolor"] = "white"
plt.rcParams["axes.facecolor"] = "white"
plt.rcParams["font.size"] = 10

# 主色系
C_DARK = "#1F4E79"   # 深蓝
C_MID  = "#2E86AB"   # 青蓝
C_ORG  = "#E67E22"   # 橙
C_GREY = "#95A5A6"   # 灰
C_LT   = "#D5E3F0"   # 浅蓝
COLORS = [C_DARK, C_MID, C_ORG, C_GREY, "#7FB3D5", "#F5B041"]


def add_source(fig, text):
    """在图底部加小字来源。"""
    fig.text(0.02, 0.01, "数据来源：" + text, fontsize=8, color="#555555")


def save(fig, name):
    """保存并校验 PNG 可打开。"""
    out = os.path.join(IMG_DIR, name)
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    # PIL 校验
    with Image.open(out) as im:
        im.verify()
    print(f"[OK] {name}  ({os.path.getsize(out)//1024} KB)")


# ============================================================
# chart_01 全球ESL市场规模（多机构口径）
# ============================================================
def chart_01():
    df = pd.read_csv(os.path.join(DATA_DIR, "market_size_global.csv"))
    # 按年份画散点，同年份多机构横向错开
    years = sorted(df["year"].unique())
    fig, ax = plt.subplots(figsize=(10, 6))
    for i, y in enumerate(years):
        sub = df[df["year"] == y].reset_index(drop=True)
        xs = [i] * len(sub)
        # 错开
        offsets = [(-0.18 + k * 0.12) for k in range(len(sub))]
        xs = [i + o for o in offsets]
        ax.scatter(xs, sub["value_usd_bn"], s=80, color=C_MID, zorder=3, edgecolor="white")
        # 区间竖线
        ax.vlines(i, sub["value_usd_bn"].min(), sub["value_usd_bn"].max(),
                  color=C_ORG, lw=2, alpha=0.7, zorder=2)
        # 机构标签
        for j, r in sub.iterrows():
            ax.annotate(f"{r['agency'].split('(')[0][:18]}\n{r['value_usd_bn']:.2f}",
                        (xs[j], r["value_usd_bn"]),
                        textcoords="offset points", xytext=(6, 4), fontsize=7, color="#333333")
    ax.set_xticks(range(len(years)))
    ax.set_xticklabels(years)
    ax.set_xlabel("年份")
    ax.set_ylabel("市场规模（十亿美元 USD bn）")
    ax.set_title("全球ESL市场规模（2020-2026，多机构口径差异）", fontsize=13, weight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.axhspan(1.5, 3.2, alpha=0.08, color=C_DARK)
    add_source(fig, "GMI / Grand View / Mordor / TBRC / Straits / R&M / M&M / Market Business Insights (2020-2026)；2026年M&M口径待核实")
    save(fig, "chart_01_global_market_size.png")


# ============================================================
# chart_02 全球ESL出货量趋势
# ============================================================
def chart_02():
    df = pd.read_csv(os.path.join(DATA_DIR, "shipment_trend.csv"))
    # 主序列：每年取代表值
    main = {
        "2021": 1.67, "2022": 2.83, "2023": 3.02,
        "2024": 3.7, "2025": 5.0, "2026H1": 2.7,
    }
    years = list(main.keys())
    vals = list(main.values())
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(years, vals, color=C_LT, edgecolor=C_DARK, lw=1.2, zorder=2, label="代表出货量（亿片/亿台）")
    ax.plot(years, vals, "-o", color=C_ORG, lw=2, zorder=3)
    for x, v in zip(years, vals):
        ax.text(x, v + 0.1, f"{v}", ha="center", fontsize=10, color=C_DARK)
    # 补充另一口径散点
    ax.scatter(["2024", "2025", "2026H1"], [3.4, 5.4, 1.7],
               color=C_GREY, marker="D", s=60, zorder=4, label="另一机构口径")
    ax.set_ylabel("出货量（亿片/亿台）")
    ax.set_title("全球ESL出货量趋势（2021-2026H1）", fontsize=13, weight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend(loc="upper left")
    add_source(fig, "CINNO(汉朔招股书) / ePaperInsight / 元太科技 / 洛图RUNTO / 同花顺研报 (2021-2026H1)")
    save(fig, "chart_02_shipment_trend.png")


# ============================================================
# chart_03 区域结构（收入占比）
# ============================================================
def chart_03():
    df = pd.read_csv(os.path.join(DATA_DIR, "regional_share.csv"))
    regions = ["欧洲", "北美", "亚太"]
    agencies = df["agency"].unique().tolist()
    import numpy as np
    x = np.arange(len(regions))
    width = 0.18
    fig, ax = plt.subplots(figsize=(10, 6))
    for i, ag in enumerate(agencies):
        vals = []
        for r in regions:
            row = df[(df["region"] == r) & (df["agency"] == ag)]
            vals.append(row["share_pct"].values[0] if len(row) else 0)
        ax.bar(x + (i - len(agencies)/2) * width, vals, width,
               label=ag.split("(")[0][:20], color=COLORS[i % len(COLORS)])
    ax.set_xticks(x)
    ax.set_xticklabels(regions)
    ax.set_ylabel("收入占比（%）")
    ax.set_title("全球ESL区域收入结构（2025，各机构口径）", fontsize=13, weight="bold")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    add_source(fig, "GMI / Polaris / PW Consulting / Dataintelo (2025)；注：各机构样本/口径不同，数值不可直接相加")
    save(fig, "chart_03_regional_share.png")


# ============================================================
# chart_04 中国ESL市场：规模(柱)+渗透率(线) 双轴
# ============================================================
def chart_04():
    df = pd.read_csv(os.path.join(DATA_DIR, "china_market.csv"))
    size = df[df["metric"].str.contains("市场规模")]
    pen = df[df["metric"].str.contains("渗透率") & df["penetration_pct"].notna()]
    # 按年份聚合规模（min-max）
    years_size = sorted(size["year"].unique())
    mins = [size[size["year"] == y]["value_rmb_100m"].min() for y in years_size]
    maxs = [size[size["year"] == y]["value_rmb_100m"].max() for y in years_size]
    fig, ax1 = plt.subplots(figsize=(10, 6))
    x = range(len(years_size))
    ax1.bar(x, maxs, color=C_LT, edgecolor=C_DARK, lw=1.2, label="市场规模区间(亿元)")
    ax1.bar(x, mins, color=C_MID, edgecolor=C_DARK, lw=1.2, label="市场规模下限")
    for i, (lo, hi) in enumerate(zip(mins, maxs)):
        if lo == hi:
            ax1.text(i, hi + 1, f"{lo:.1f}", ha="center", fontsize=9)
        else:
            ax1.text(i, hi + 1, f"{lo:.1f}~{hi:.1f}", ha="center", fontsize=9)
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(years_size)
    ax1.set_xlim(-0.6, len(years_size)-0.4)
    ax1.set_ylabel("市场规模（亿元人民币）")
    ax1.set_xlabel("年份")
    # 渗透率轴：2020年<5%、2024年商超近30%（在柱图时间轴上标注）
    ax2 = ax1.twinx()
    # x=0 对应 2022 柱，x=1 对应 2025 柱；2020 点画在 x=-0.3，2024 画在 x=0.6
    ax2.plot([-0.3, 0.6], [5, 30], "--o", color=C_ORG, lw=2, label="商超渗透率(2020<5%→2024近30%)")
    ax2.annotate("2020年 <5%", (-0.3, 5), textcoords="offset points", xytext=(-5, 8), fontsize=8, color=C_ORG)
    ax2.annotate("2024年 商超近30%", (0.6, 30), textcoords="offset points", xytext=(5, 5), fontsize=8, color=C_ORG)
    ax2.set_ylabel("中国商超渗透率（%）", color=C_ORG)
    ax2.set_ylim(0, 50)
    ax2.tick_params(axis="y", labelcolor=C_ORG)
    ax2.legend(loc="upper left", fontsize=8)
    ax1.set_title("中国ESL市场规模与渗透率（2020-2026E）", fontsize=13, weight="bold")
    ax1.grid(axis="y", linestyle="--", alpha=0.4)
    add_source(fig, "ePaperInsight(2022) / 豆丁网行业报告(2025-2026E) / 搜狐·天波科技(渗透率)")
    save(fig, "chart_04_china_market.png")


# ============================================================
# chart_05 全球市占格局 环形图
# ============================================================
def chart_05():
    labels = ["VusionGroup\n(2024, 44%)", "汉朔科技\n(2023, 28%)",
              "SOLUM\n(2025, 12.3%)", "Pricer+Displaydata\n(CR5剩余)", "其他"]
    sizes = [44, 28, 12.3, 9.4, 6.3]
    colors = [C_DARK, C_MID, C_ORG, C_GREY, "#D5DBDB"]
    fig, ax = plt.subplots(figsize=(9, 7))
    wedges, texts = ax.pie(sizes, labels=labels, colors=colors, startangle=90,
                           wedgeprops=dict(width=0.4, edgecolor="white"),
                           textprops=dict(fontsize=9))
    ax.set_title("全球ESL市场份额格局（CR5=93.7%）", fontsize=13, weight="bold")
    add_source(fig, "中国电子视像行业协会(2024) / CINNO(2023) / ReportMines(2025) / GMI(2025)")
    save(fig, "chart_05_competitor_share.png")


# ============================================================
# chart_06 竞品营收对比（保留原始货币）
# ============================================================
def chart_06():
    df = pd.read_csv(os.path.join(DATA_DIR, "competitor_revenue.csv"))
    df["year"] = df["year"].astype(str)
    companies = ["汉朔科技", "VusionGroup", "Pricer AB"]
    years = ["2024", "2025"]
    fig, ax = plt.subplots(figsize=(11, 6.5))
    import numpy as np
    x = np.arange(len(companies))
    width = 0.32
    currency_map = {"汉朔科技": "亿人民币", "VusionGroup": "亿欧元", "Pricer AB": "亿瑞典克朗"}
    for i, y in enumerate(years):
        vals = []
        for c in companies:
            row = df[(df["company"] == c) & (df["year"] == y)]
            vals.append(row["revenue"].values[0] if len(row) else 0)
        bars = ax.bar(x + (i - 0.5) * width, vals, width, label=f"{y}年",
                      color=[C_DARK, C_MID][i])
        for b, v in zip(bars, vals):
            if v > 0:
                ax.text(b.get_x() + b.get_width()/2, v + 0.5, f"{v:.2f}",
                        ha="center", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{c}\n(单位：{currency_map[c]})" for c in companies])
    ax.set_ylabel("营收（原始货币单位，不做汇率换算）")
    ax.set_title("全球头部ESL厂商营收对比（2024-2025）", fontsize=13, weight="bold")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    add_source(fig, "汉朔科技2024/2025年报 / VusionGroup 2024/2025年报 / Pricer 2024/2025年报（原始货币）")
    save(fig, "chart_06_competitor_revenue.png")


# ============================================================
# chart_07 商业模式对标：SaaS收入占比
# ============================================================
def chart_07():
    df = pd.read_csv(os.path.join(DATA_DIR, "saas_model.csv"))
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = [C_GREY, C_MID, C_ORG]
    bars = ax.barh(df["company"], df["saas_revenue_share_pct"], color=colors, edgecolor="white")
    for b, v, note in zip(bars, df["saas_revenue_share_pct"], df["note"]):
        ax.text(v + 1, b.get_y() + b.get_height()/2, f"{v}%",
                va="center", fontsize=11, weight="bold")
    ax.set_xlabel("软件/SaaS/经常性收入占总营收比例（%）")
    ax.set_title("ESL行业商业模式对标：SaaS收入占比（汉朔 vs Vusion vs 维界投影目标）",
                 fontsize=12, weight="bold")
    ax.set_xlim(0, 85)
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    add_source(fig, "证券之星(汉朔2025) / VusionGroup AMF文件(2024) / 项目内部PPT(维界目标, 待核实)")
    save(fig, "chart_07_saas_model.png")


# ============================================================
# chart_08 产业链图谱
# ============================================================
def chart_08():
    fig, ax = plt.subplots(figsize=(13, 7))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 7)
    ax.axis("off")

    def box(x, y, w, h, text, color):
        bb = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08",
                            facecolor=color, edgecolor=C_DARK, lw=1.2)
        ax.add_patch(bb)
        ax.text(x + w/2, y + h/2, text, ha="center", va="center",
                fontsize=9, color="white", weight="bold")

    # 上游
    ax.text(1.2, 6.5, "上游", fontsize=12, weight="bold", color=C_DARK)
    box(0.2, 4.8, 2.2, 1.2, "元太科技\n电子纸市占90-95%\n(阅读器口径)", C_DARK)
    box(2.6, 4.8, 2.2, 1.2, "京东方等\n电子纸模组\n(累计出货近3亿只)", C_DARK)
    box(5.0, 4.8, 2.2, 1.2, "Nordic nRF52\nBLE通信芯片\n(BT5.4 ESL Profile)", C_DARK)

    # 中游
    ax.text(3.5, 3.8, "中游", fontsize=12, weight="bold", color=C_DARK)
    box(0.5, 2.2, 2.5, 1.2, "VusionGroup\n全球市占44%\n(法国巴黎)", C_MID)
    box(3.2, 2.2, 2.5, 1.2, "汉朔科技\n全球28%/中国62%\n(深交所301275)", C_MID)
    box(5.9, 2.2, 2.2, 1.2, "Pricer AB\n瑞典 28000+门店", C_MID)
    box(8.3, 2.2, 2.2, 1.2, "SOLUM\n韩国 3.5亿枚累计", C_MID)
    box(10.7, 2.2, 2.0, 1.2, "维界投影\n中立中台\n(SaaS目标70%+)", C_ORG)

    # 下游
    ax.text(3.5, 1.5, "下游", fontsize=12, weight="bold", color=C_DARK)
    box(0.5, 0.2, 2.6, 1.0, "沃尔玛\n美国2300店+墨西哥170万枚", C_GREY)
    box(3.3, 0.2, 2.6, 1.0, "家乐福\n法国货架数字化", C_GREY)
    box(6.1, 0.2, 2.6, 1.0, "永辉超市\n627店全覆盖\n单店1.8万枚", C_GREY)
    box(8.9, 0.2, 3.6, 1.0, "中国连锁百强\n25.72万门店(2024)\n销售2.13万亿", C_GREY)

    # 箭头
    for x0, x1 in [(1.3, 1.7), (3.7, 4.5), (6.1, 6.5)]:
        ax.add_patch(FancyArrowPatch((x0, 4.8), (x1, 3.4),
                                     arrowstyle="->", mutation_scale=15, color=C_DARK))
    for x0, x1 in [(1.7, 1.8), (4.5, 4.5), (7.0, 7.0), (9.4, 9.4), (11.7, 10.7)]:
        ax.add_patch(FancyArrowPatch((x0, 2.2), (x1, 1.2),
                                     arrowstyle="->", mutation_scale=15, color=C_MID))

    ax.set_title("ESL产业链图谱：上游电子纸 → 中游硬件+中台 → 下游连锁零售",
                 fontsize=13, weight="bold")
    add_source(fig, "元太/京东方/Nordic官网 / Vusion·汉朔·Pricer·SOLUM年报 / Walmart·Carrefour·永辉官网 / CCFA(2024)")
    save(fig, "chart_08_industry_chain.png")


# ============================================================
# chart_09 政策时间线
# ============================================================
def chart_09():
    events = [
        ("2024-04", "中国", "数字商务三年行动计划(2024-2026)", C_DARK),
        ("2024-06", "中国", "零售业创新提升工程实施方案", C_DARK),
        ("2024", "欧盟", "ESPR (EU 2024/1781)\n数字产品护照DPP", C_MID),
        ("2025-02", "欧盟", "PPWR (EU 2025/40)\n生效，2026-08适用", C_MID),
        ("2026-08", "欧盟", "PPWR全面适用", C_ORG),
        ("2026-09", "欧盟", "反漂绿指令(EU 2024/825)适用", C_ORG),
        ("2027-02", "欧盟", "DPP电池类强制落地", C_GREY),
        ("2025-26", "粤港", "粤港联合资助100万元/项", "#7FB3D5"),
    ]
    fig, ax = plt.subplots(figsize=(12, 6.5))
    ax.set_ylim(-1, 2)
    ax.set_xlim(0, len(events))
    ax.axis("off")
    ax.axhline(0, color=C_DARK, lw=2)
    for i, (date, region, text, color) in enumerate(events):
        up = i % 2 == 0
        y = 0.6 if up else -0.6
        ax.plot([i, i], [0, y*0.7], color=color, lw=1.2)
        ax.scatter([i], [0], s=80, color=color, zorder=5)
        ax.text(i, y, f"{date}\n{region}\n{text}", ha="center",
                va="bottom" if up else "top", fontsize=8.5,
                bbox=dict(boxstyle="round,pad=0.4", facecolor=color, alpha=0.15, edgecolor=color))
    ax.set_title("ESL相关政策时间线（2024-2027）", fontsize=13, weight="bold")
    add_source(fig, "中国政府网 / 欧盟委员会EUR-Lex / 广东省科技厅 (2024-2027)")
    save(fig, "chart_09_policy_timeline.png")


# ============================================================
# chart_10 客户价值测算（ROI）
# ============================================================
def chart_10():
    # ---- 假设与计算 ----
    # 假设：典型商超门店 SKU/标签数取 13000 枚（区间 8000-20000 的中位）
    n_labels = 13000
    price_213 = 63      # 元/枚（淘宝国内零售，2.13寸）
    price_420 = 128     # 元/枚（1688国内批发，4.2寸三色）
    capex_213 = n_labels * price_213 / 10000   # 万元
    capex_420 = n_labels * price_420 / 10000
    # 人工换标成本基线：假设单店年人工+纸张标签管理成本 15 万元（行业估算）
    baseline_labor = 15.0  # 万元/年
    save_low = 0.60   # 60% 节省（Deloitte转述，下限）
    save_high = 0.80  # 80% 节省（上限）
    annual_save_low = baseline_labor * save_low
    annual_save_high = baseline_labor * save_high
    payback_213_lo = capex_213 / annual_save_high
    payback_213_hi = capex_213 / annual_save_low
    payback_420_lo = capex_420 / annual_save_high
    payback_420_hi = capex_420 / annual_save_low

    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    # 左：硬件投入
    ax = axes[0]
    bars = ax.bar(["2.13寸\n(国内零售)", "4.2寸三色\n(国内批发)"],
                  [capex_213, capex_420], color=[C_MID, C_ORG], edgecolor="white")
    for b, v in zip(bars, [capex_213, capex_420]):
        ax.text(b.get_x() + b.get_width()/2, v + 2, f"{v:.1f}万元",
                ha="center", fontsize=11, weight="bold")
    ax.set_ylabel("单店硬件投入（万元）")
    ax.set_title(f"单店ESL硬件投入（按{n_labels}枚标签估算）", fontsize=11, weight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    # 右：回收期
    ax = axes[1]
    labels = ["2.13寸方案", "4.2寸三色方案"]
    lo = [payback_213_lo, payback_420_lo]
    hi = [payback_213_hi, payback_420_hi]
    ax.barh(labels, hi, color=C_LT, edgecolor=C_DARK, label="回收期区间")
    ax.barh(labels, lo, color=C_ORG, edgecolor=C_DARK, label="乐观(节省80%)")
    for i, (l, h) in enumerate(zip(lo, hi)):
        ax.text(h + 0.2, i, f"{l:.1f} ~ {h:.1f} 年", va="center", fontsize=10)
    ax.set_xlabel("投资回收期（年）")
    ax.set_title("单店ESL改造投资回收期估算", fontsize=11, weight="bold")
    ax.set_xlim(0, 20)
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(axis="x", linestyle="--", alpha=0.4)

    # 假设说明（合并来源，避免与 add_source 重叠）
    fig.text(0.02, 0.005,
             "假设：标签数=13000枚(区间8000-20000中位)；2.13寸63元/枚(淘宝)；4.2寸128元/枚(1688)；"
             "年人工+纸张基线成本15万元/店(行业估算)；人工换标节省60-80%(Deloitte口径转述, 未取原始报告, 标估算)。"
             "本图为测算示意，非权威财务数据。\n数据来源：淘宝/1688(2026-10) / 行业博客转述Deloitte / 磐达科技(换标耗时)",
             fontsize=7.5, color="#555555")
    fig.subplots_adjust(bottom=0.18)
    save(fig, "chart_10_customer_roi.png")


# ============================================================
# chart_11 渗透率对比
# ============================================================
def chart_11():
    items = [
        ("全球(2023)", 15, "约15%"),
        ("中国商超(2024)", 30, "近30%"),
        ("中国一二线(2024)", 60, ">60%"),
        ("中国三四线(2024)", 15, "约15%"),
        ("法国(近年)", 55, "50-60%"),
        ("欧美门店数(2025)", 30, "<30%"),
    ]
    fig, ax = plt.subplots(figsize=(10, 6))
    names = [x[0] for x in items]
    vals = [x[1] for x in items]
    colors = [C_GREY, C_MID, C_DARK, C_LT, C_ORG, C_GREY]
    bars = ax.barh(names, vals, color=colors, edgecolor="white")
    for b, v, label in zip(bars, vals, [x[2] for x in items]):
        ax.text(v + 1, b.get_y() + b.get_height()/2, label, va="center", fontsize=10)
    ax.set_xlabel("ESL渗透率（%）")
    ax.set_title("全球及区域ESL渗透率对比（不同口径并存）", fontsize=13, weight="bold")
    ax.set_xlim(0, 80)
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    add_source(fig, "汉朔投资评级(2023全球) / 搜狐·天波科技(中国2024) / 物联网世界(法国) / 洛图RUNTO(欧美2025)")
    save(fig, "chart_11_penetration_compare.png")


# ============================================================
# chart_12 仪表盘（3x2 拼接6张图）
# ============================================================
def chart_12():
    files = [
        "chart_01_global_market_size.png",
        "chart_02_shipment_trend.png",
        "chart_04_china_market.png",
        "chart_05_competitor_share.png",
        "chart_06_competitor_revenue.png",
        "chart_07_saas_model.png",
    ]
    fig, axes = plt.subplots(3, 2, figsize=(16, 18))
    axes = axes.flatten()
    for i, f in enumerate(files):
        img = Image.open(os.path.join(IMG_DIR, f))
        axes[i].imshow(img)
        axes[i].axis("off")
    fig.suptitle("维界投影·ESL中台数据仪表盘", fontsize=20, weight="bold", y=0.995)
    add_source(fig, "全部子图数据来源见各子图底部标注")
    save(fig, "chart_12_dashboard.png")


# ============================================================
# 主流程
# ============================================================
def main():
    print("=" * 60)
    print("维界投影 ESL 可视化图表生成")
    print("=" * 60)
    chart_01()
    chart_02()
    chart_03()
    chart_04()
    chart_05()
    chart_06()
    chart_07()
    chart_08()
    chart_09()
    chart_10()
    chart_11()
    chart_12()
    print("=" * 60)
    print(f"全部图表已写入：{IMG_DIR}")


if __name__ == "__main__":
    main()
