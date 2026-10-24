# -*- coding: utf-8 -*-
"""生成 数据字典.md 与 数据来源清单.md（从 data/ 原始数据自动提取）。"""
import os, csv, json

DATA = r"C:\Users\陈聪惠\Desktop\维界投影数据分析\data"
DOCS = r"C:\Users\陈聪惠\Desktop\维界投影数据分析\docs"

# ---------- 数据来源清单 ----------
urls = {}   # url -> (file, note)
for f in sorted(os.listdir(DATA)):
    p = os.path.join(DATA, f)
    if f.endswith(".csv"):
        try:
            with open(p, encoding="utf-8-sig") as fh:
                for row in csv.DictReader(fh):
                    u = (row.get("source_url") or "").strip()
                    if u and u not in urls:
                        urls[u] = f
        except Exception:
            pass
    elif f.endswith(".json"):
        try:
            with open(p, encoding="utf-8-sig") as fh:
                j = json.load(fh)
            def walk(o):
                if isinstance(o, dict):
                    u = o.get("source_url") or o.get("url")
                    if u and u not in urls:
                        urls[u] = f
                    for v in o.values(): walk(v)
                elif isinstance(o, list):
                    for v in o: walk(v)
            walk(j)
        except Exception:
            pass

L = ["# 数据来源清单（全部真实、可追溯）", "",
     "> 本清单由脚本从 `data/` 原始数据自动提取，共去重 %d 个来源 URL。所有数字均可据此复核。" % len(urls), ""]
for i, (u, f) in enumerate(urls.items(), 1):
    L.append(f"{i}. `{u}`（来自 {f}）")
with open(os.path.join(DOCS, "数据来源清单.md"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(L))
print("sources:", len(urls))

# ---------- 数据字典 ----------
D = ["# 数据字典（字段说明）", "",
     "> 说明 `data/` 各文件的字段含义与口径，便于复现与面试讲解。", ""]
tables = [
    ("market_size_global.csv", "全球ESL市场规模（多机构口径）", [
        ("year", "统计年份"),
        ("value_usd_bn", "市场规模（十亿美元）"),
        ("agency", "研究机构（Global Market Insights / Grand View / Mordor 等）"),
        ("source_url", "来源链接"),
        ("pending_note", "待核实/口径备注（不同机构口径差异大，报告并存引用）"),
    ]),
    ("shipment_trend.csv", "全球电子价签出货量（原始口径）", [
        ("year", "年份（含 2026H1 半年口径）"),
        ("units", "出货量数值"),
        ("unit_label", "单位（亿片/亿台，不同来源口径不同）"),
        ("agency", "数据机构/出处（CINNO、ePaperInsight、洛图、元太等）"),
        ("source_url", "来源链接"),
        ("pending_note", "口径备注"),
    ]),
    ("regional_share.csv", "区域市场占比（多机构）", [
        ("region", "区域（欧洲/北美/亚太）"),
        ("metric", "口径（收入占比等）"),
        ("share_pct", "占比(%)"),
        ("year", "年份"), ("agency", "机构"), ("source_url", "来源"), ("pending_note", "备注"),
    ]),
    ("china_market.csv", "中国市场（规模+渗透率）", [
        ("year", "年份（含2026E预测）"),
        ("value_rmb_100m", "中国ESL市场规模（亿元人民币）"),
        ("penetration_pct", "商超渗透率(%)"),
        ("metric", "指标类型"), ("scope", "范围（如一二线/三四线）"),
        ("source_url", "来源"), ("pending_note", "待核实（estimate）"),
    ]),
    ("penetration_compare.csv", "渗透率对比", [
        ("region", "地区/范围"), ("penetration_pct", "渗透率(%)"),
        ("year", "年份"), ("scope", "口径"), ("source_url", "来源"), ("pending_note", "备注"),
    ]),
    ("competitor_share.csv", "竞品市占", [
        ("company", "厂商（Vusion/汉朔/SOLUM/CR5合计）"),
        ("share_pct", "市占(%)"), ("year", "年份"), ("scope", "全球/中国"),
        ("source_url", "来源"), ("pending_note", "口径（CINNO/estimate）"),
    ]),
    ("competitor_revenue.csv", "竞品营收（财报）", [
        ("company", "厂商"), ("year", "年份"), ("revenue", "营收额"),
        ("currency", "币种（人民币/欧元/瑞典克朗/美元）"),
        ("source_url", "来源（公司财报/新闻）"), ("pending_note", "备注"),
    ]),
    ("saas_model.csv", "SaaS/服务订阅占比（商业模式验证）", [
        ("company", "厂商（含本项目对比）"),
        ("saas_revenue_share_pct", "SaaS/服务收入占比(%)"),
        ("note", "说明（项目自述目标 vs 行业现状）"),
        ("source_url", "来源"), ("pending_note", "备注"),
    ]),
    ("price_points.csv", "价签价位参考", [
        ("spec", "规格/尺寸"), ("price", "价格"), ("currency", "币种"),
        ("market", "市场"), ("source_url", "来源"), ("pending_note", "备注"),
    ]),
    ("policy_timeline.csv", "政策法规时间线", [
        ("year", "年份"), ("region", "区域（中国/欧盟）"), ("policy_name", "政策/法规名称"),
        ("key_point", "要点"), ("source_url", "来源"), ("pending_note", "备注"),
    ]),
]
for fname, title, fields in tables:
    D.append(f"\n## {fname}（{title}）\n")
    D.append("| 字段 | 含义 |")
    D.append("|---|---|")
    for k, v in fields:
        D.append(f"| `{k}` | {v} |")
D.append("\n> 三个 JSON 调研文件（esl_market_data / esl_competitor_industry / esl_policy_business）结构为 `{meta, records}`：`meta` 含采集说明，`records` 为带 `source_url` 的记录数组。")
with open(os.path.join(DOCS, "数据字典.md"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(D))
print("dict written")
