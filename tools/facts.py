"""Every number quoted in the README, notebook, dashboard notes and PDF guide - computed from data/clean.

Keeping the narrative numbers in one place means the written findings always match the data.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"


def egp(v):
    a = abs(v)
    if a >= 1e6:
        return f"{v/1e6:,.2f}M"
    if a >= 1e4:
        return f"{v/1e3:,.0f}K"
    if a >= 1e3:
        return f"{v/1e3:,.1f}K"
    return f"{v:,.0f}"


def pct(v, d=1):
    return f"{v*100:.{d}f}%"


def compute():
    p = pd.read_csv(CLEAN / "dim_product.csv")
    s = pd.read_csv(CLEAN / "fact_item_sales.csv")
    i = pd.read_csv(CLEAN / "fact_invoices.csv", parse_dates=["invoice_datetime", "business_date"])
    d = s.merge(p, on="product_id")
    F = {}

    def agg(x):
        return dict(rev=x.revenue.sum(), profit=x.profit.sum(), units=int(x.qty_sold.sum()),
                    margin=x.profit.sum() / x.revenue.sum() if x.revenue.sum() else np.nan, n=len(x))

    tot = agg(d)
    F.update(revenue=tot["rev"], profit=tot["profit"], margin=tot["margin"], units=tot["units"], products=len(d))
    for c in ["Tire", "Battery", "Rim", "Service"]:
        a = agg(d[d.category == c])
        F[c] = dict(a, rev_share=a["rev"] / tot["rev"], profit_share=a["profit"] / tot["profit"])
    goods = d[d.category != "Service"]
    F["goods_margin"] = goods.profit.sum() / goods.revenue.sum()

    svc = d[d.category == "Service"].set_index("product_name_en")
    F["svc_jobs"] = int(svc.qty_sold.sum())
    F["svc_profit_per_job"] = svc.profit.sum() / svc.qty_sold.sum()
    F["weld_jobs"], F["weld_price"] = int(svc.loc["Welding", "qty_sold"]), svc.loc["Welding", "unit_price"]
    F["straight_jobs"] = int(svc.loc["Rim Straightening & Welding", "qty_sold"])
    F["straight_price"] = svc.loc["Rim Straightening & Welding", "unit_price"]
    tires = d[d.category == "Tire"]
    F["profit_per_tire"] = tires.profit.sum() / tires.qty_sold.sum()

    # concentration
    r = d.sort_values("profit", ascending=False)
    F["n80_all"] = int((r.profit.cumsum() / r.profit.sum() < 0.8).sum() + 1)
    g = goods.sort_values("profit", ascending=False)
    F["n80_goods"], F["n_goods"] = int((g.profit.cumsum() / g.profit.sum() < 0.8).sum() + 1), len(g)
    F["sold_once"] = int((d.qty_sold == 1).sum())

    # tires
    rim = tires.groupby("rim_size_label").apply(lambda x: x.profit.sum() / x.revenue.sum(), include_groups=False)
    F["rim_margin"] = rim.to_dict()
    big = tires[tires.rim_diameter_in >= 17]
    F["big_rev"], F["big_margin"] = big.revenue.sum(), big.profit.sum() / big.revenue.sum()
    F["big_gain_11"] = big.revenue.sum() * 0.11 - big.profit.sum()
    F["big_gain_12"] = big.revenue.sum() * 0.12 - big.profit.sum()
    pb = tires.groupby(["price_band_order", "price_band"]).agg(rev=("revenue", "sum"), profit=("profit", "sum"),
                                                               units=("qty_sold", "sum"))
    pb["margin"] = pb.profit / pb.rev
    F["price_bands"] = [(b, row.margin, int(row.units)) for (_, b), row in pb.iterrows()]
    best_band = pb[pb.units >= 100].margin.idxmax()
    F["best_band"], F["best_band_margin"], F["best_band_units"] = best_band[1], pb.loc[best_band, "margin"], int(pb.loc[best_band, "units"])
    o = tires.groupby("origin_country").agg(rev=("revenue", "sum"), profit=("profit", "sum"))
    o["margin"] = o.profit / o.rev
    o = o.sort_values("rev", ascending=False)
    F["origins"] = o.head(7).to_dict("index")
    kr = o.loc["South Korea"]
    F["korea_gain_12"] = kr.rev * 0.12 - kr.profit
    b = tires.groupby("brand").agg(rev=("revenue", "sum"), profit=("profit", "sum"), units=("qty_sold", "sum"))
    b["margin"] = b.profit / b.rev
    F["brands_top"] = b.sort_values("profit", ascending=False).head(3).to_dict("index")
    F["brands"] = b.to_dict("index")
    sz = tires.groupby("tire_size").agg(units=("qty_sold", "sum"), n=("product_id", "size"))
    F["sizes_top"] = sz.sort_values("units", ascending=False).head(3).to_dict("index")
    F["size_max_n"], F["size_max_name"] = int(sz.n.max()), sz.n.idxmax()

    # losses
    loss = d[d.is_loss].sort_values("profit")
    F["loss_n"], F["loss_amt"], F["loss_rev"] = len(loss), -loss.profit.sum(), loss.revenue.sum()
    F["loss_top"] = [(r_.product_name_en, -r_.profit, r_.unit_price, r_.unit_cost, r_.margin_pct) for r_ in loss.head(4).itertuples()]
    gap = loss.groupby("loss_gap_band").agg(n=("product_id", "size"), amt=("profit", "sum"))
    F["gap"] = {k: (int(v.n), -v.amt) for k, v in gap.iterrows()}
    F["large_names"] = list(loss[loss.loss_gap_band == "Large (>15%)"].product_name_en.str.replace(r" - .*", "", regex=True))
    F["low_margin_n"] = int((d.margin_band == "0-5%").sum())
    mb = d.groupby(["margin_band_order", "margin_band"]).agg(n=("product_id", "size"), rev=("revenue", "sum"))
    F["margin_bands"] = [(k[1], int(v.n), v.rev) for k, v in mb.iterrows()]

    # batteries & rims
    bat = d[d.category == "Battery"]
    bl = bat.groupby("product_line").agg(rev=("revenue", "sum"), profit=("profit", "sum"), units=("qty_sold", "sum"))
    bl["margin"] = bl.profit / bl.rev
    F["bat_lines"] = bl.to_dict("index")
    F["bat_top"] = list(bl.sort_values("rev", ascending=False).head(3).index)
    F["td70_units"] = int(bat[bat.battery_model == "TD-70"].qty_sold.sum())
    F["td70_share"] = F["td70_units"] / bat.qty_sold.sum()
    rims = d[d.category == "Rim"]
    F["rims_n"] = len(rims)

    # invoices
    F["inv_n"], F["inv_rev"] = len(i), i.net_amount.sum()
    F["avg_ticket"], F["median_ticket"] = i.net_amount.mean(), i.net_amount.median()
    daily = i.groupby("business_date").net_amount.sum()
    F["days"] = len(daily)
    F["rev_per_day"], F["inv_per_day"] = F["inv_rev"] / F["days"], F["inv_n"] / F["days"]
    F["walkin_share"] = (i.customer_type == "Walk-in").mean()
    full = i[i.business_date < "2026-11-01"]
    m = full.groupby(full.business_date.dt.to_period("M")).agg(rev=("net_amount", "sum"), days=("business_date", "nunique"))
    m["per_day"] = m.rev / m.days
    F["months"] = {k.strftime("%b"): (v.rev, v.per_day) for k, v in m.iterrows()}
    F["best_month"] = m.per_day.idxmax().strftime("%B")
    wd = daily.groupby(daily.index.day_name()).mean()
    F["weekday"] = wd.to_dict()
    F["best_wd"], F["worst_wd"] = wd.sort_values(ascending=False).index[:2].tolist(), wd.idxmin()
    F["best_day"], F["best_day_rev"] = daily.idxmax(), daily.max()
    F["second_day"], F["second_day_rev"] = daily.nlargest(2).index[1], daily.nlargest(2).iloc[1]
    timed = i[~i.is_time_estimated]
    F["evening_inv"] = (timed.hour_sort >= 18).mean()
    F["evening_rev"] = timed[timed.hour_sort >= 18].net_amount.sum() / timed.net_amount.sum()
    F["peak_hour"] = timed.hour_label.value_counts().idxmax()
    F["morning_share"] = (timed.hour_sort < 12).mean()
    cell = timed.assign(wd=timed.business_date.dt.day_name()).groupby(["wd", "hour_label"]).size()
    F["busiest_cell"], F["busiest_cell_n"] = cell.idxmax(), int(cell.max())
    late = i[i.is_after_midnight]
    F["late_n"], F["late_rev"], F["late_ticket"] = len(late), late.net_amount.sum(), late.net_amount.mean()
    tb = i.groupby(["ticket_band_order", "ticket_band"]).agg(n=("invoice_no", "size"), rev=("net_amount", "sum"))
    tb = tb / tb.sum()
    F["ticket_bands"] = [(k[1], v.n, v.rev) for k, v in tb.iterrows()]
    F["small_inv"] = tb.iloc[:2].n.sum()
    F["small_rev"] = tb.iloc[:2].rev.sum()
    F["big_inv"], F["big_rev_share"] = tb.iloc[3:].n.sum(), tb.iloc[3:].rev.sum()
    F["gap_item_inv"] = F["revenue"] - F["inv_rev"]
    F["corrected"] = int(i.is_date_corrected.sum())
    return F


if __name__ == "__main__":
    import pprint
    pprint.pprint(compute(), width=140)
