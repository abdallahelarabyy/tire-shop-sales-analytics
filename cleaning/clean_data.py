"""Phase 2 - clean the tire shop DEXEF POS exports into Power BI-ready tables.

Inputs  (data/raw/, confidential copies of the DEXEF POS exports):
    item_profit_report.xlsx   item profit report (one row per product, all-time)
    invoice_list.xlsx         invoice list (one row per invoice)

Outputs (data/clean/):
    dim_product.csv      product attributes parsed from the Arabic name
    fact_item_sales.csv  qty / revenue / cost / profit per product
    fact_invoices.csv    one row per invoice with corrected timestamps
    dim_date.csv         calendar table for the invoice dates
and docs/cleaning_report.md with every validation check and data flag.

Run:  python cleaning/clean_data.py
"""

from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from mappings import (BATTERY_BRANDS, ORIGINS, OTHER_PRODUCTS, REGIONS, RIMS,
                      TIRE_BRANDS, TIRE_TAGS, key, normalize)

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "clean"
DOCS = ROOT / "docs"
ITEMS_FILE = RAW / "item_profit_report.xlsx"
INVOICES_FILE = RAW / "invoice_list.xlsx"

BUSINESS_DAY_CUTOFF_HOURS = 5   # sales before 05:00 belong to the previous day
WALK_IN = "تعامل نقدي"

checks: list[tuple[str, bool, str]] = []
flags: dict[str, list[str] | str] = {}


def check(name: str, passed: bool, detail: str = "") -> None:
    checks.append((name, bool(passed), detail))


def money_eq(a: float, b: float, tol: float = 0.01) -> bool:
    return abs(float(a) - float(b)) <= tol


# ---------------------------------------------------------------------------
# 1. Item profit report
# ---------------------------------------------------------------------------
ITEM_HEADERS = {"الصنف": "item_ar", "الكمية المباعة": "qty",
                "الايرادات": "revenue", "التكلفة": "cost", "الربح": "profit"}


def read_item_report(path: Path) -> tuple[pd.DataFrame, dict]:
    raw = pd.read_excel(path, header=None)

    header_row = next(i for i, row in raw.iterrows() if "الصنف" in row.values)
    cols = {}
    for c, v in raw.iloc[header_row].items():
        if isinstance(v, str) and v.strip() in ITEM_HEADERS:
            cols[ITEM_HEADERS[v.strip()]] = c

    body = raw.iloc[header_row + 1:]
    is_item = pd.to_numeric(body[0], errors="coerce").notna()
    items = body[is_item]
    df = pd.DataFrame({"product_id": items[0].astype(int)})
    for name, c in cols.items():
        df[name] = items[c]
    for c in ["qty", "revenue", "cost", "profit"]:
        df[c] = pd.to_numeric(df[c])
    df["item_ar"] = df["item_ar"].astype(str).str.strip()

    # Totals row: first row after the items with a quantity but no row number
    after = body.loc[body.index > items.index.max()]
    total_row = after[pd.to_numeric(after[cols["qty"]], errors="coerce").notna()].iloc[0]
    footer = {name: float(total_row[c]) for name, c in cols.items() if name != "item_ar"}

    printed = raw.iloc[-1, 0]
    meta = {"printed_at": printed if isinstance(printed, str) else ""}
    return df.reset_index(drop=True), {"footer": footer, **meta}


# ---------------------------------------------------------------------------
# 2. Parse product names
# ---------------------------------------------------------------------------
AR_LETTER = r"؀-ۿ"
ORIGIN_RE = re.compile(
    rf"(?<![{AR_LETTER}])({'|'.join(sorted(ORIGINS, key=len, reverse=True))})(?![{AR_LETTER}])")
TIRE_RE = re.compile(r"^(\d{2})\s*-\s*(\d{2})\s*-\s*(\d{3})")
TIRE_LT_RE = re.compile(r"^(\d{2})\s*-\s*(\d{3})(?!\d)")
RIM_RE = re.compile(r"^(\d{2})-([45])-([\d-]+)")
BATTERY_RE = re.compile(r"(td|din|ns|n)\s*-?\s*(\d{2,3})\s*([lr])?(?![a-z])", re.I)
LOAD_SPEED_RE = re.compile(r"(\d{2,3})\s*([HVWYTSQ])(?:\s*XL)?(?![A-Z])")
PLY_RE = re.compile(r"(\d{1,2})\s*(?:PR|تيله)")


def find_origin(text: str) -> tuple[str, int | None]:
    m = ORIGIN_RE.search(text)
    return (ORIGINS[m.group(1)], m.start()) if m else ("Unknown", None)


def empty_attrs() -> dict:
    return dict(category=None, brand=None, product_line=None, origin_country=None,
                tire_width_mm=np.nan, tire_aspect_ratio=np.nan, rim_diameter_in=np.nan,
                tire_size=None, tire_type=None, load_index=np.nan, speed_rating=None,
                is_xl=False, is_run_flat=False, ply_rating=np.nan,
                rim_bolt_count=np.nan, rim_pcd=None, rim_width_in=None, rim_offset_et=None,
                rim_finish=None, is_oem=False,
                battery_model=None, battery_family=None,
                tags=None, product_name_en=None)


def parse_tire(text: str, a: dict) -> dict:
    m = TIRE_RE.match(text)
    if m:
        rim, aspect, width = (int(x) for x in m.groups())
        a.update(tire_aspect_ratio=aspect, tire_size=f"{width}/{aspect} R{rim}")
    else:
        m = TIRE_LT_RE.match(text)
        rim, width = (int(x) for x in m.groups())
        a["tire_size"] = f"{width} R{rim}"
    a.update(category="Tire", tire_width_mm=width, rim_diameter_in=rim)

    rest = text[m.end():].strip()
    origin, pos = find_origin(rest)
    tags = [en for ar, en in TIRE_TAGS.items() if ar in rest]
    if "White line" in tags:
        tags.remove("Line")

    brand_part = rest[:pos] if pos is not None else rest
    for ar in TIRE_TAGS:
        brand_part = brand_part.replace(ar, "")
    brand_part = re.sub(r"[A-Za-z0-9]+", "", brand_part)
    brand = TIRE_BRANDS.get(key(brand_part))

    upper = rest.upper()
    ls = LOAD_SPEED_RE.search(upper)
    ply = PLY_RE.search(upper)
    is_lt = (not TIRE_RE.match(text)) or ("Light truck" in tags) or bool(ply)
    a.update(
        brand=brand, product_line=brand, origin_country=origin,
        load_index=int(ls.group(1)) if ls else np.nan,
        speed_rating=ls.group(2) if ls else None,
        is_xl="XL" in upper, is_run_flat=("RFT" in upper) or ("Run-flat" in tags),
        ply_rating=int(ply.group(1)) if ply else np.nan,
        tire_type="Light Truck" if is_lt else "Passenger",
        tags=", ".join(tags) or None,
    )
    a["product_name_en"] = f"{a['tire_size']} {brand} - {origin}"
    return a


def parse_rim(pid: int, text: str, a: dict) -> dict:
    m = RIM_RE.match(text)
    diameter, bolts = int(m.group(1)), int(m.group(2))
    pcds = ["114.3" if p == "114" else p for p in m.group(3).strip("-").split("-")]
    pcd = f"{bolts}x{'/'.join(pcds)}"
    width = re.search(r"([\d.]+(?:-[\d.]+)?)\s*انش", text)
    et = re.search(r"ET\s*(\d+(?:-\d+)?)", text, re.I)
    brand, finish = RIMS[pid]
    origin, _ = find_origin(text)
    a.update(category="Rim", brand=brand, product_line=brand, origin_country=origin,
             rim_diameter_in=diameter, rim_bolt_count=bolts, rim_pcd=pcd,
             rim_width_in=width.group(1) if width else None,
             rim_offset_et=et.group(1) if et else None, rim_finish=finish,
             is_oem=("اصلي" in text) or ("OEM" in brand))
    a["product_name_en"] = f'{diameter}" {brand} {finish} ({pcd})'
    return a


def parse_battery(text: str, a: dict) -> dict:
    m = BATTERY_RE.search(text)
    family = m.group(1).upper()
    model = f"{family}-{m.group(2)}{(m.group(3) or '').upper()}"
    brand, line = BATTERY_BRANDS.get(key(text[:m.start()]), (None, None))
    origin, _ = find_origin(text[m.end():])
    a.update(category="Battery", brand=brand, product_line=line, origin_country=origin,
             battery_model=model, battery_family=family)
    a["product_name_en"] = f"{line} {model} - {origin}"
    return a


def parse_product(pid: int, name_ar: str) -> dict:
    a = empty_attrs()
    text = normalize(name_ar)
    if key(text) in OTHER_PRODUCTS:
        cat, name_en, brand = OTHER_PRODUCTS[key(text)]
        a.update(category=cat, brand=brand, product_line=brand,
                 origin_country="Not applicable", product_name_en=name_en)
    elif pid in RIMS and RIM_RE.match(text):
        parse_rim(pid, text, a)
    elif TIRE_RE.match(text) or TIRE_LT_RE.match(text):
        parse_tire(text, a)
    elif BATTERY_RE.search(text):
        parse_battery(text, a)
    return a


def build_products(items: pd.DataFrame) -> pd.DataFrame:
    attrs = pd.DataFrame([parse_product(p, n) for p, n in zip(items.product_id, items.item_ar)])
    prod = pd.concat([items[["product_id", "item_ar"]].rename(columns={"item_ar": "product_name_ar"}),
                      attrs], axis=1)
    prod["origin_region"] = prod["origin_country"].map(REGIONS)

    # Same product entered twice in the POS (identical after normalising spelling)
    norm = prod["product_name_ar"].map(key)
    dup = norm.duplicated(keep=False)
    prod["is_possible_duplicate"] = dup
    flags["Products entered twice in the POS (same name after normalising spelling)"] = [
        f"#{r.product_id} `{r.product_name_ar}`" for r in prod[dup].itertuples()]

    # Make English names unique for Power BI slicers
    clash = prod["product_name_en"].duplicated(keep=False)
    prod.loc[clash, "product_name_en"] += " #" + prod.loc[clash, "product_id"].astype(str)

    unparsed = prod[prod["category"].isna()]
    no_brand = prod[prod["category"].notna() & prod["brand"].isna()]
    check("Every product classified into a category", unparsed.empty,
          ", ".join(unparsed.product_name_ar))
    check("Every product mapped to an English brand", no_brand.empty,
          ", ".join(f"#{r.product_id} {r.product_name_ar}" for r in no_brand.itertuples()))
    check("English product names are unique", prod["product_name_en"].is_unique)
    prod["rim_size_label"] = prod.rim_diameter_in.map(lambda d: f"R{int(d)}" if pd.notna(d) else None)

    unknown = prod[(prod.origin_country == "Unknown") & prod.category.isin(["Tire", "Battery"])]
    flags["Tires/batteries with unknown country of origin (most rims have none, not listed)"] = [
        f"#{r.product_id} `{r.product_name_ar}` -> {r.product_name_en}" for r in unknown.itertuples()]
    return prod


# ---------------------------------------------------------------------------
# 3. Item sales fact
# ---------------------------------------------------------------------------
def build_item_sales(items: pd.DataFrame, footer: dict) -> pd.DataFrame:
    f = items[["product_id", "qty", "revenue", "cost", "profit"]].copy()
    f = f.rename(columns={"qty": "qty_sold"})

    check("Row profit = revenue - cost (source)",
          (abs(f.revenue - f.cost - f.profit) <= 0.01).all())
    for col, foot in [("qty_sold", "qty"), ("revenue", "revenue"), ("cost", "cost"), ("profit", "profit")]:
        check(f"Item {col} total matches report footer",
              money_eq(f[col].sum(), footer[foot]), f"{f[col].sum():,.2f} vs {footer[foot]:,.2f}")
    check("All quantities positive", (f.qty_sold > 0).all())

    f["revenue"] = f.revenue.round(2)
    f["cost"] = f.cost.round(2)
    f["profit"] = (f.revenue - f.cost).round(2)
    f["unit_price"] = (f.revenue / f.qty_sold).round(2)
    f["unit_cost"] = (f.cost / f.qty_sold).round(2)
    f["unit_profit"] = (f.profit / f.qty_sold).round(2)
    f["margin_pct"] = np.where(f.revenue > 0, f.profit / f.revenue, np.nan).round(4)
    f["revenue_share"] = (f.revenue / f.revenue.sum()).round(6)
    f["profit_share"] = (f.profit / f.profit.sum()).round(6)
    f["is_loss"] = f.profit < 0
    f["is_zero_cost"] = f.cost <= 0

    # ABC classification on profit (A = first 80 % of profit, B = next 15 %)
    order = f.sort_values("profit", ascending=False)
    cum_before = order.profit.cumsum().shift(fill_value=0) / order.profit.sum()
    f["abc_class"] = pd.cut(cum_before, [-np.inf, 0.80, 0.95, np.inf],
                            labels=["A", "B", "C"], right=False).astype(str)
    f["profit_rank"] = f.profit.rank(ascending=False, method="first").astype(int)
    return f


def band(values: pd.Series, edges: list, labels: list) -> tuple[pd.Series, pd.Series]:
    """Label + sort order for a banded numeric column (left-closed bins)."""
    cut = pd.cut(values, edges, labels=labels, right=False)
    order = cut.cat.codes.where(cut.notna()) + 1
    return cut.astype(object), order.astype("Int64")


def add_dashboard_bands(sales: pd.DataFrame, prod: pd.DataFrame) -> pd.DataFrame:
    """Banded columns used as Power BI axes (each with a sort-order column)."""
    cat = sales.product_id.map(prod.set_index("product_id").category)
    tire = cat == "Tire"
    service = cat == "Service"

    sales["price_band"], sales["price_band_order"] = band(
        sales.unit_price.where(tire), [0, 1500, 2000, 2500, 3000, 4000, np.inf],
        ["< 1.5K", "1.5K-2K", "2K-2.5K", "2.5K-3K", "3K-4K", "4K+"])

    sales["margin_band"], sales["margin_band_order"] = band(
        sales.margin_pct.where(~service), [-np.inf, 0, 0.05, 0.10, 0.15, 0.20, np.inf],
        ["Below cost", "0-5%", "5-10%", "10-15%", "15-20%", "20%+"])
    sales.loc[service, ["margin_band", "margin_band_order"]] = ["Service", 7]

    gap = -sales.margin_pct.where(sales.is_loss)
    sales["loss_gap_band"], sales["loss_gap_order"] = band(
        gap, [0, 0.05, 0.15, np.inf], ["Small (<5%)", "Medium (5-15%)", "Large (>15%)"])
    sales["sale_status"] = np.where(sales.is_loss, "Sold below cost", "Profitable")
    return sales


# ---------------------------------------------------------------------------
# 4. Invoices
# ---------------------------------------------------------------------------
INVOICE_COLS = ["stamp", "time_dup", "invoice_no", "customer", "items_count",
                "gross_amount", "discount", "tax", "net_amount", "paid_amount", "due_amount"]


def reconstruct_datetimes(stamps: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Invoice numbers are sequential, so real time can never go backwards.

    DEXEF keeps the shift's date until the shift is closed (after midnight, or
    when a shift is left open overnight) while the clock time is correct. Move
    any timestamp that falls before the previous invoice forward by whole days.

    Guard against cascades: if the shifted time would land *after* the next
    invoice's own stamp, while that next stamp already fits the sequence, the
    invoice's clock time itself is wrong. It is then marked as estimated, given
    the next invoice's time, and not allowed to move the invoices after it.
    """
    s = list(stamps)
    fixed, shifts, estimated, last = [pd.NaT] * len(s), [0] * len(s), [False] * len(s), None
    for k, ts in enumerate(s):
        days = 0
        if last is not None and ts < last:
            days = int(np.ceil((last - ts) / pd.Timedelta(days=1)))
            if ts + pd.Timedelta(days=days) < last:
                days += 1
        candidate = ts + pd.Timedelta(days=days)
        nxt = s[k + 1] if k + 1 < len(s) else None
        if days > 0 and nxt is not None and last <= nxt < candidate:
            estimated[k] = True
            continue
        fixed[k], shifts[k], last = candidate, days, candidate

    fixed = pd.Series(fixed, index=stamps.index).bfill()
    shifts = pd.Series(shifts, index=stamps.index)
    estimated = pd.Series(estimated, index=stamps.index)
    shifts[estimated] = (fixed[estimated].dt.normalize() - stamps[estimated].dt.normalize()).dt.days
    return fixed, shifts, estimated


TICKET_BANDS = [0, 300, 1000, 3000, 10000, np.inf]
TICKET_LABELS = ["< 300", "300-999", "1K-2.9K", "3K-9.9K", "10K+"]


def build_invoices(path: Path) -> pd.DataFrame:
    raw = pd.read_excel(path)
    raw.columns = INVOICE_COLS
    footer_mask = raw.invoice_no.isna()
    footer = raw[footer_mask].iloc[0]
    inv = raw[~footer_mask].copy()
    n_source = len(inv)

    check("Time column is a copy of the date column", (inv.stamp == inv.time_dup).all())
    inv = inv.drop(columns="time_dup")
    inv["invoice_no"] = inv.invoice_no.astype(int)
    inv["items_count"] = inv.items_count.astype(int)

    # Exact duplicate rows exported twice
    exact = inv.duplicated(keep="first")
    removed = inv[exact]
    inv = inv[~exact]

    inv = inv.sort_values(["invoice_no", "stamp"]).reset_index(drop=True)
    inv["invoice_datetime"], inv["days_shifted"], inv["is_time_estimated"] = \
        reconstruct_datetimes(inv.stamp)

    # Duplicates that only differed by the (wrong) stamp date
    same = inv.duplicated(subset=[c for c in inv.columns
                                  if c not in ("stamp", "days_shifted", "is_time_estimated")],
                          keep="first")
    removed = pd.concat([removed, inv[same]])
    inv = inv[~same].reset_index(drop=True)

    flags["Duplicate invoice rows removed"] = [
        f"#{r.invoice_no} {r.stamp:%Y-%m-%d %H:%M} {r.net_amount:,.0f} EGP" for r in removed.itertuples()]
    check("Invoice numbers unique after de-duplication", inv.invoice_no.is_unique)
    check("Corrected timestamps never go backwards",
          inv.invoice_datetime.is_monotonic_increasing)

    nums = set(inv.invoice_no)
    missing = sorted(set(range(min(nums), max(nums) + 1)) - nums)
    flags["Invoice numbers missing from the export (deleted/voided in POS?)"] = [
        f"#{n}" for n in missing]

    # Totals reconcile with the export footer (minus removed duplicates)
    for col in ["gross_amount", "discount", "tax", "net_amount", "paid_amount", "due_amount"]:
        expected = float(footer[col]) - removed[col].sum()
        check(f"Invoice {col} total = footer - removed duplicates",
              money_eq(inv[col].sum(), expected), f"{inv[col].sum():,.2f} vs {expected:,.2f}")
    check("gross - discount + tax = net on every invoice",
          (abs(inv.gross_amount - inv.discount + inv.tax - inv.net_amount) <= 0.01).all())
    check("net = paid + due on every invoice",
          (abs(inv.net_amount - inv.paid_amount - inv.due_amount) <= 0.01).all())

    shifted = inv.days_shifted > 0
    flags["Invoice timestamps corrected (POS kept the previous shift date)"] = (
        f"{shifted.sum()} invoices moved forward by "
        + ", ".join(f"{d} day(s): {n}" for d, n in inv.days_shifted[shifted].value_counts().sort_index().items()))
    flags["Invoices whose clock time is impossible (time estimated from the next invoice)"] = [
        f"#{r.invoice_no} stamped {r.stamp:%Y-%m-%d %H:%M} -> {r.invoice_datetime:%Y-%m-%d %H:%M}"
        for r in inv[inv.is_time_estimated].itertuples()]
    big = inv[inv.days_shifted > 2]
    flags["Large date corrections (> 2 days, check in POS)"] = [
        f"#{r.invoice_no} stamped {r.stamp:%Y-%m-%d %H:%M} -> {r.invoice_datetime:%Y-%m-%d %H:%M}"
        for r in big.itertuples()]

    dt = inv.invoice_datetime
    inv["invoice_date"] = dt.dt.date
    inv["business_date"] = (dt - pd.Timedelta(hours=BUSINESS_DAY_CUTOFF_HOURS)).dt.date
    inv["invoice_hour"] = dt.dt.hour
    inv["hour_label"] = dt.dt.strftime("%H:00")
    inv["hour_sort"] = np.where(dt.dt.hour < BUSINESS_DAY_CUTOFF_HOURS, dt.dt.hour + 24, dt.dt.hour)
    inv["is_after_midnight"] = dt.dt.hour < BUSINESS_DAY_CUTOFF_HOURS
    inv["is_date_corrected"] = shifted

    # Customers: anonymise names (personal data never leaves data/raw/)
    named = inv.customer.str.strip() != WALK_IN
    order = inv.loc[named].drop_duplicates("customer")["customer"]
    ids = {c: f"C{i:03d}" for i, c in enumerate(order, start=1)}
    inv["customer_type"] = np.where(named, "Named customer", "Walk-in")
    inv["customer_id"] = inv.customer.map(ids).fillna("WALK-IN")

    inv["payment_status"] = np.select(
        [inv.due_amount <= 0, inv.paid_amount <= 0], ["Paid", "Unpaid"], "Partially paid")
    inv["has_discount"] = inv.discount > 0
    inv["ticket_band"], inv["ticket_band_order"] = band(inv.net_amount, TICKET_BANDS, TICKET_LABELS)
    inv["is_near_zero"] = inv.net_amount < 1
    flags["Near-zero invoices (kept, flagged is_near_zero)"] = [
        f"#{r.invoice_no} {r.net_amount} EGP" for r in inv[inv.is_near_zero].itertuples()]
    check("No negative amounts", (inv[["gross_amount", "net_amount", "paid_amount"]] >= 0).all().all())

    inv.attrs["n_source"] = n_source
    cols = ["invoice_no", "invoice_datetime", "invoice_date", "business_date", "invoice_hour",
            "hour_label", "hour_sort", "is_after_midnight", "is_date_corrected", "days_shifted", "is_time_estimated",
            "customer_type", "customer_id",
            "items_count", "gross_amount", "discount", "tax", "net_amount", "paid_amount",
            "due_amount", "payment_status", "has_discount", "ticket_band", "ticket_band_order",
            "is_near_zero"]
    return inv[cols]


# ---------------------------------------------------------------------------
# 5. Date dimension
# ---------------------------------------------------------------------------
def build_dates(invoices: pd.DataFrame) -> pd.DataFrame:
    start = pd.Timestamp(min(invoices.business_date)).replace(day=1)
    end = pd.Timestamp(max(invoices.business_date)) + pd.offsets.MonthEnd(0)
    d = pd.DataFrame({"date": pd.date_range(start, end, freq="D")})
    d["year"] = d.date.dt.year
    d["quarter"] = "Q" + d.date.dt.quarter.astype(str)
    d["month_num"] = d.date.dt.month
    d["month_name"] = d.date.dt.strftime("%B")
    d["month_short"] = d.date.dt.strftime("%b")
    d["year_month"] = d.date.dt.strftime("%Y-%m")
    d["month_start"] = d.date.dt.to_period("M").dt.start_time
    d["day_of_month"] = d.date.dt.day
    d["weekday_name"] = d.date.dt.day_name()
    d["weekday_short"] = d.date.dt.strftime("%a")
    d["weekday_num"] = (d.date.dt.dayofweek + 2) % 7 + 1      # Saturday = 1 ... Friday = 7
    d["week_start"] = d.date - pd.to_timedelta(d.weekday_num - 1, unit="D")
    d["is_friday"] = d.weekday_name == "Friday"
    d["date"] = d.date.dt.date
    d["month_start"] = d.month_start.dt.date
    d["week_start"] = d.week_start.dt.date
    return d


# ---------------------------------------------------------------------------
# 6. Report
# ---------------------------------------------------------------------------
def write_report(meta: dict, prod: pd.DataFrame, sales: pd.DataFrame,
                 inv: pd.DataFrame, dates: pd.DataFrame) -> None:
    uncertain = sorted({b for b in prod.brand.dropna()
                        if b in _uncertain_brands()})
    lines = [
        "# Phase 2 - Cleaning report",
        "",
        f"Generated {datetime.now():%Y-%m-%d %H:%M} by `cleaning/clean_data.py`.",
        f"Item report printed by DEXEF: {meta.get('printed_at', '')}",
        "",
        "## Output tables",
        "",
        "| File | Rows | Grain |",
        "|---|---|---|",
        f"| dim_product.csv | {len(prod)} | one row per POS product |",
        f"| fact_item_sales.csv | {len(sales)} | all-time totals per product (no dates) |",
        f"| fact_invoices.csv | {len(inv)} | one row per invoice (source: {inv.attrs['n_source']}) |",
        f"| dim_date.csv | {len(dates)} | one row per day {dates.date.min()} to {dates.date.max()} |",
        "",
        "## Validation checks",
        "",
        "| Check | Result | Detail |",
        "|---|---|---|",
    ]
    lines += [f"| {n} | {'PASS' if ok else '**FAIL**'} | {d} |" for n, ok, d in checks]
    lines += ["", "## Data flags", ""]
    for title, items in flags.items():
        if isinstance(items, str):          # one-line summary
            lines += [f"**{title}**", f"- {items}", ""]
            continue
        lines.append(f"**{title}** ({len(items)})")
        lines += [f"- {i}" for i in items] or ["- none"]
        lines.append("")
    lines += ["**Brand transliterations to confirm with the shop**", "",
              "- " + ", ".join(uncertain), "",
              "## Known limitations", "",
              "- The item report has no dates or invoice numbers, so product sales "
              "cannot be split by month or linked to invoices.",
              "- Services (welding, rim straightening) have zero recorded cost (`is_zero_cost`). "
              "The owner confirmed their costs are small and already deducted from the "
              "service revenue, so the recorded service profit is used as-is.",
              "- Cost is DEXEF's **last purchase price** (replacement cost), not the price "
              "paid for the units sold; when supplier prices rise, margins look lower and "
              "some sales show as losses.",
              f"- Item revenue ({sales.revenue.sum():,.0f}) exceeds invoice net "
              f"({inv.net_amount.sum():,.0f}); the invoice export ends "
              f"{max(inv.business_date)} while the item report covers all time "
              "up to its print date.",
              ]
    (DOCS / "cleaning_report.md").write_text("\n".join(lines), encoding="utf-8")


def _uncertain_brands() -> set[str]:
    src = (Path(__file__).parent / "mappings.py").read_text(encoding="utf-8")
    found = set()
    for line in src.splitlines():
        if "# ?" in line:
            found.update(re.findall(r'\("([^"]+)"', line))
            found.update(re.findall(r':\s*"([^"]+)"', line))
    return found


# ---------------------------------------------------------------------------
def main() -> int:
    OUT.mkdir(exist_ok=True)
    DOCS.mkdir(exist_ok=True)

    items, meta = read_item_report(ITEMS_FILE)
    prod = build_products(items)
    sales = add_dashboard_bands(build_item_sales(items, meta["footer"]), prod)
    inv = build_invoices(INVOICES_FILE)
    dates = build_dates(inv)

    for name, df in [("dim_product", prod), ("fact_item_sales", sales),
                     ("fact_invoices", inv), ("dim_date", dates)]:
        df.to_csv(OUT / f"{name}.csv", index=False, encoding="utf-8-sig")

    write_report(meta, prod, sales, inv, dates)

    failed = [c for c in checks if not c[1]]
    for name, ok, detail in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")
    print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed. "
          f"Outputs in {OUT}, report in {DOCS / 'cleaning_report.md'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
