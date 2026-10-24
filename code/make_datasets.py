# -*- coding: utf-8 -*-
"""
维界投影·电子价签(ESL)中台 — 数据集清洗脚本
读取三份 JSON 原始调研数据，清洗为 10 张结构化 CSV，全部带 source_url 可追溯。
运行：python make_datasets.py
"""
import json
import os
import re

# 路径配置（脚本位于 code/ 目录，项目根为上一级）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# 读取三份 JSON
def _load(name):
    with open(os.path.join(DATA_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)["records"]

market = _load("esl_market_data.json")
compet = _load("esl_competitor_industry.json")
policy = _load("esl_policy_business.json")


def num(x):
    """把记录里的数值字段安全转成 float；失败返回 None。"""
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# ============================================================
# 1. market_size_global.csv — 全球ESL市场规模（各机构口径）
#    列：year, value_usd_bn, agency, source_url, pending_note
#    单位统一：十亿美元 -> 直接是 USD bn；亿美元 -> /10 转 USD bn
# ============================================================
def build_market_size():
    rows = []
    # 来自 market_data.json：metric 含“全球ESL市场规模”，单位为 十亿美元
    for r in market:
        if "全球ESL市场规模" in r["metric"] and r["unit"] == "十亿美元":
            v = num(r["value"])
            if v is None:
                continue
            rows.append({
                "year": r["year"],
                "value_usd_bn": round(v, 3),
                "agency": r["source_name"],
                "source_url": r["source_url"],
                "pending_note": "待核实：" + r["note"] if r.get("confidence") == "uncertain" else "",
            })
    # market_data.json 里 2026 年那条单位是“亿美元”(uncertain)，转成 USD bn
    for r in market:
        if r["metric"] == "全球ESL市场规模" and r["unit"] == "亿美元":
            v = num(r["value"])
            if v is not None:
                rows.append({
                    "year": r["year"],
                    "value_usd_bn": round(v / 10.0, 3),   # 50亿美元 = 5.0 USD bn
                    "agency": r["source_name"],
                    "source_url": r["source_url"],
                    "pending_note": "待核实(uncertain)：" + r["note"],
                })
    # competitor_industry.json：2024 年两个口径（单位 亿美元/美元）
    for r in compet:
        if "全球ESL市场规模" in r["metric"] and r["unit"] == "美元":
            m = re.search(r"([\d.]+)", str(r["value"]))
            if m:
                v_usd_bn = float(m.group(1)) / 10.0   # 亿美元 -> USD bn
                rows.append({
                    "year": r["year"],
                    "value_usd_bn": round(v_usd_bn, 3),
                    "agency": r["source_name"],
                    "source_url": r["source_url"],
                    "pending_note": "口径差异，并存记录" if "另一口径" in r["metric"] else "",
                })
    return rows


# ============================================================
# 2. shipment_trend.csv — 全球ESL出货量
#    列：year, units, unit_label(亿台/亿片), agency, source_url, pending_note
# ============================================================
def build_shipment():
    rows = []
    for r in market + compet:
        if r["metric"] == "全球ESL出货量":
            v = num(r["value"])
            if v is None:
                # 兼容 “2.7亿片（+19.3%）” 这类字符串
                m = re.search(r"([\d.]+)", str(r["value"]))
                v = float(m.group(1)) if m else None
            if v is None:
                continue
            unit_label = "亿片" if "片" in r["unit"] else ("亿台" if "台" in r["unit"] else r["unit"])
            rows.append({
                "year": r["year"],
                "units": round(v, 3),
                "unit_label": unit_label,
                "agency": r["source_name"],
                "source_url": r["source_url"],
                "pending_note": "待核实：" + r["note"] if r.get("confidence") == "uncertain" else "",
            })
    return rows


# ============================================================
# 3. regional_share.csv — 区域结构
#    列：region, metric(收入占比), share_pct, year, agency, source_url, pending_note
# ============================================================
def build_regional():
    rows = []
    for r in market:
        if "ESL市场占比" in r["metric"]:
            v = num(r["value"])
            if v is None:
                continue
            rows.append({
                "region": r["region"],
                "metric": "收入占比",
                "share_pct": round(v, 2),
                "year": r["year"],
                "agency": r["source_name"],
                "source_url": r["source_url"],
                "pending_note": "",
            })
    return rows


# ============================================================
# 4. china_market.csv — 中国市场
#    列：year, value_rmb_100m, penetration_pct, metric, source_url, pending_note
# ============================================================
def build_china():
    rows = []
    # 规模（亿元人民币）
    for r in market:
        if r["metric"] == "中国ESL市场规模" and r["unit"] == "亿元人民币":
            v = num(r["value"])
            if v is not None:
                rows.append({
                    "year": r["year"],
                    "value_rmb_100m": round(v, 2),
                    "penetration_pct": "",
                    "metric": "中国ESL市场规模(亿元人民币)",
                    "source_url": r["source_url"],
                    "pending_note": "estimate" if r.get("confidence") == "estimate" else "",
                })
    # 渗透率（%）
    for r in market:
        if r["metric"] in ("中国商超ESL渗透率",
                            "中国一二线城市商超ESL渗透率",
                            "中国三四线城市ESL渗透率"):
            raw = str(r["value"]).replace("<", "").replace(">", "").replace("%", "")
            v = num(raw)
            rows.append({
                "year": r["year"],
                "value_rmb_100m": "",
                "penetration_pct": v,
                "metric": r["metric"],
                "source_url": r["source_url"],
                "pending_note": ("含不等号原值:" + str(r["value"])) if ("<" in str(r["value"]) or ">" in str(r["value"])) else "",
            })
    return rows


# ============================================================
# 5. penetration_compare.csv — 渗透率对比
#    列：region, penetration_pct, year, scope口径, source_url, pending_note
# ============================================================
def build_penetration():
    rows = []
    # 从 market_data.json 抽取各区域渗透率
    for r in market:
        if r["metric"] in ("中国商超ESL渗透率",
                           "中国一二线城市商超ESL渗透率",
                           "中国三四线城市ESL渗透率",
                           "法国ESL渗透率",
                           "欧美发达国家ESL渗透率",
                           "中国ESL渗透率"):
            raw = str(r["value"]).replace("<", "").replace(">", "").replace("%", "")
            v = num(raw)
            rows.append({
                "region": r["region"],
                "penetration_pct": v,
                "year": r["year"],
                "scope": r["metric"],
                "source_url": r["source_url"],
                "pending_note": "旧口径冲突，待核实" if r.get("confidence") == "uncertain" else "",
            })
    # 从 policy_business.json 补全球口径
    for r in policy:
        if r["metric"] == "全球电子价签渗透率(权威口径)":
            rows.append({
                "region": "全球",
                "penetration_pct": num(r["value"]),
                "year": r["year"],
                "scope": r["metric"],
                "source_url": r["source_url"],
                "pending_note": "",
            })
    return rows


# ============================================================
# 6. competitor_revenue.csv — 竞品营收
#    列：company, year, revenue, currency, source_url, pending_note
# ============================================================
def build_comp_revenue():
    rows = []
    # 汉朔
    for r in compet:
        if r["metric"] == "汉朔科技营业收入":
            m = re.search(r"([\d.]+)亿元", str(r["value"]))
            if m:
                rows.append({
                    "company": "汉朔科技",
                    "year": r["year"],
                    "revenue": round(float(m.group(1)), 2),
                    "currency": "亿人民币",
                    "source_url": r["source_url"],
                    "pending_note": "",
                })
    # Vusion
    for r in compet:
        if r["metric"] == "VusionGroup调整后营收":
            m = re.search(r"([\d.]+)亿欧元", str(r["value"]))
            if m:
                rows.append({
                    "company": "VusionGroup",
                    "year": r["year"],
                    "revenue": round(float(m.group(1)), 2),
                    "currency": "亿欧元",
                    "source_url": r["source_url"],
                    "pending_note": "调整后口径(IFRS另见原文)",
                })
    # Pricer
    for r in compet:
        if r["metric"] == "Pricer AB净销售额":
            m = re.search(r"([\d.]+)亿瑞典克朗", str(r["value"]))
            if m:
                rows.append({
                    "company": "Pricer AB",
                    "year": r["year"],
                    "revenue": round(float(m.group(1)), 3),
                    "currency": "亿瑞典克朗",
                    "source_url": r["source_url"],
                    "pending_note": "",
                })
    # SOLUM
    for r in compet:
        if r["metric"] == "SOLUM ESL相关收入/市占":
            m = re.search(r"([\d.]+)亿美元", str(r["value"]))
            if m:
                rows.append({
                    "company": "SOLUM",
                    "year": r["year"],
                    "revenue": round(float(m.group(1)), 2),
                    "currency": "亿美元",
                    "source_url": r["source_url"],
                    "pending_note": "estimate，含市占约12.3%",
                })
    return rows


# ============================================================
# 7. competitor_share.csv — 竞品市占
#    列：company, share_pct, year, scope(全球/中国), source_url, pending_note
# ============================================================
def build_comp_share():
    rows = [
        {
            "company": "VusionGroup", "share_pct": 44.0, "year": "2024",
            "scope": "全球",
            "source_url": "https://www.cvianet.org.cn/static/files/file-21457.pdf",
            "pending_note": "按出货量口径",
        },
        {
            "company": "汉朔科技", "share_pct": 28.0, "year": "2023",
            "scope": "全球",
            "source_url": "https://m.jiemian.com/article/13390589_microcontent.html",
            "pending_note": "CINNO口径",
        },
        {
            "company": "汉朔科技", "share_pct": 62.0, "year": "2023",
            "scope": "中国",
            "source_url": "https://m.jiemian.com/article/13390589_microcontent.html",
            "pending_note": "CINNO口径",
        },
        {
            "company": "SOLUM", "share_pct": 12.3, "year": "2025",
            "scope": "全球",
            "source_url": "https://www.reportmines.com/en/report/electronic-shelf-label-market",
            "pending_note": "estimate",
        },
        {
            "company": "CR5合计", "share_pct": 93.7, "year": "2025",
            "scope": "全球",
            "source_url": "https://www.gminsights.com/ko/industry-analysis/electronic-shelf-label-esl-market",
            "pending_note": "前五大:Vusion/汉朔/Solum/Pricer/Displaydata",
        },
    ]
    return rows


# ============================================================
# 8. saas_model.csv — 商业模式对标
#    列：company, saas_revenue_share_pct, note, source_url, pending_note
# ============================================================
def build_saas():
    rows = [
        {
            "company": "汉朔科技", "saas_revenue_share_pct": 4.33,
            "note": "2025年软件/SaaS/技术服务1.83亿元，占比4.33%",
            "source_url": "https://wap.stockstar.com/detail/RB2026090400040144",
            "pending_note": "",
        },
        {
            "company": "VusionGroup", "saas_revenue_share_pct": 6.0,
            "note": "2024年经常性SaaS收入5740万欧元，约占总营收6%",
            "source_url": "https://echanges.dila.gouv.fr/OPENDATA/AMF/ACT/2025/02/FCACT073120_20250226.pdf",
            "pending_note": "",
        },
        {
            "company": "维界投影(本项目)", "saas_revenue_share_pct": 70.0,
            "note": "SaaS订阅收入占营收70%+，项目自述目标，非行业现状",
            "source_url": "",
            "pending_note": "项目内部PPT自述，无公开财报，待核实",
        },
    ]
    return rows


# ============================================================
# 9. policy_timeline.csv — 政策清单
#    列：year, region, policy_name, key_point, source_url, pending_note
# ============================================================
def build_policy():
    rows = [
        {
            "year": "2024-04", "region": "中国",
            "policy_name": "《数字商务三年行动计划(2024-2026年)》",
            "key_point": "5项行动20条举措；全文未提电子价签，仅提智慧商圈/智慧商店",
            "source_url": "https://www.gov.cn/zhengce/zhengceku/202404/content_6948104.htm",
            "pending_note": "",
        },
        {
            "year": "2024-06", "region": "中国",
            "policy_name": "《零售业创新提升工程实施方案》(商务部等7部门)",
            "key_point": "含以旧换新与智能消费新增长点，关联零售数字化",
            "source_url": "https://www.gov.cn/zhengce/zhengceku/202412/content_6992758.htm",
            "pending_note": "",
        },
        {
            "year": "2024", "region": "欧盟",
            "policy_name": "ESPR Regulation (EU) 2024/1781",
            "key_point": "可持续产品生态设计法规，数字产品护照DPP为核心支柱",
            "source_url": "https://single-market-economy.ec.europa.eu/single-market/digital-product-passport_en",
            "pending_note": "",
        },
        {
            "year": "2025-02", "region": "欧盟",
            "policy_name": "PPWR Regulation (EU) 2025/40",
            "key_point": "包装与包装废弃物法规；2025-02-11生效，2026-08-12起全面适用",
            "source_url": "https://environment.ec.europa.eu/topics/waste-and-recycling/packaging-waste_en",
            "pending_note": "",
        },
        {
            "year": "2024", "region": "欧盟",
            "policy_name": "ECGT反漂绿指令 Directive (EU) 2024/825",
            "key_point": "要求店内环保/价格信息实时可核验；2026-09-27起适用",
            "source_url": "https://eur-lex.europa.eu/legal-content/EN-FR/TXT/?uri=CELEX:32024L0825",
            "pending_note": "",
        },
        {
            "year": "2027-02", "region": "欧盟",
            "policy_name": "DPP电池类全面落地",
            "key_point": "2027-02-18起电池类数字产品护照强制落地，合规需求集中释放",
            "source_url": "https://www.eudigitalproductpassport.org/what-is-dpp",
            "pending_note": "estimate",
        },
        {
            "year": "2025-2026", "region": "粤港",
            "policy_name": "粤港科技创新联合资助专题",
            "key_point": "每项事前一次性资助100万元，实施周期2年；广东创新主体联合香港方",
            "source_url": "http://gdstc.gd.gov.cn/gkmlpt/content/4/4965/mpost_4965475.html",
            "pending_note": "",
        },
    ]
    return rows


# ============================================================
# 10. price_points.csv — 价签价格
#     列：spec, price, currency, market(国内/国际批发), source_url, pending_note
# ============================================================
def build_price():
    rows = [
        {
            "spec": "2.13寸 ESL", "price": "0.85-1.15", "currency": "美元/枚",
            "market": "国际批发(Made-in-China出口)",
            "source_url": "https://www.made-in-china.com/products-search/hot-china-products/wireless_label_price.html",
            "pending_note": "MOQ100",
        },
        {
            "spec": "2.13寸 ESL", "price": "约63", "currency": "人民币/枚",
            "market": "国内零售(淘宝)",
            "source_url": "https://mobile-phone.taobao.com/chanpin/acca8290864c77d352c0d1d2007f8d70f9cad8027770099951060a789e3a265d.html",
            "pending_note": "",
        },
        {
            "spec": "4.2寸三色 ESL", "price": "约128", "currency": "人民币/枚",
            "market": "国内批发(1688)",
            "source_url": "https://www.1688.com/chanpin/-B5E7D7D3B1EAC7A9CFD4CABEC6C1.html",
            "pending_note": "",
        },
        {
            "spec": "4.2寸 ESL", "price": "16.6-18.8", "currency": "美元/枚",
            "market": "国际零售(Alibaba)",
            "source_url": "https://www.alibaba.com/showroom/high-technology-electronic-shelf-label.html",
            "pending_note": "",
        },
    ]
    return rows


# ============================================================
# 主流程：写入 CSV 并打印统计
# ============================================================
def main():
    import pandas as pd

    builders = {
        "market_size_global.csv": build_market_size,
        "shipment_trend.csv": build_shipment,
        "regional_share.csv": build_regional,
        "china_market.csv": build_china,
        "penetration_compare.csv": build_penetration,
        "competitor_revenue.csv": build_comp_revenue,
        "competitor_share.csv": build_comp_share,
        "saas_model.csv": build_saas,
        "policy_timeline.csv": build_policy,
        "price_points.csv": build_price,
    }

    print("=" * 60)
    print("维界投影 ESL 数据集清洗 — 输出 CSV")
    print("=" * 60)
    for fname, fn in builders.items():
        rows = fn()
        df = pd.DataFrame(rows)
        out = os.path.join(DATA_DIR, fname)
        df.to_csv(out, index=False, encoding="utf-8-sig")
        print(f"[OK] {fname:32s} 行数={len(df):3d}  字段={list(df.columns)}")
    print("=" * 60)
    print(f"全部 CSV 已写入：{DATA_DIR}")


if __name__ == "__main__":
    main()
