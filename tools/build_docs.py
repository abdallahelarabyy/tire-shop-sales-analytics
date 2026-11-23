"""Write README.md, docs/insights_and_recommendations.md, docs/qa_checklist.md and the dashboard guide (HTML).

Every number comes from tools/facts.py, so the documents always match data/clean.
The guide is printed to PDF by run_pipeline.bat (Microsoft Edge, headless).
"""
from pathlib import Path

from facts import ROOT, compute, egp, pct

F = compute()
DOCS = ROOT / "docs"
GH = "https://github.com/abdallahelarabyy"


def o(name):
    return F["origins"][name]


def bl(name):
    return F["bat_lines"][name]


big_bands = ", ".join(f"{b} {pct(m)}" for b, m, _ in F["price_bands"])
rims = ", ".join(f"{k} {pct(v)}" for k, v in sorted(F["rim_margin"].items(), key=lambda kv: int(kv[0][1:])))
loss0 = F["loss_top"][0]

# =============================================================================== README
readme = f"""# Tire Shop Sales & Profit Analytics

**End-to-end analytics on real point-of-sale data from a family-owned tire, battery and rim shop in Egypt** - Python cleaning,
exploratory analysis, a 6-page Power BI dashboard and business recommendations.

`Python` `pandas` `matplotlib` `Jupyter` `Power BI` `DAX` `Power Query` `TMDL / PBIR` `Data cleaning` `Data storytelling`

> **Real data, kept confidential.** The data comes from the shop's actual POS system (DEXEF). To protect the business,
> the shop is not named, customer names are removed, and **all money values are scaled by a secret factor and perturbed
> per product**. Percentages, counts, dates, times and patterns are real; absolute EGP amounts are not.

![Overview page](docs/screenshots/1-overview.png)

## Key findings

- **Services are the profit engine:** welding and rim straightening are {pct(F['Service']['rev_share'])} of revenue but
  **{pct(F['Service']['profit_share'], 0)} of profit** ({F['svc_jobs']:,} jobs) - and they bring most of the walk-in traffic.
- **Goods earn thin margins:** tires {pct(F['Tire']['margin'])}, batteries {pct(F['Battery']['margin'])}, rims {pct(F['Rim']['margin'])}.
- **Bigger tires earn the least:** R17 and larger earn {pct(F['big_margin'])}; re-pricing them to 11 % would add
  ~{pct(F['big_gain_11'] / F['big_rev'], 1)} of their revenue in profit.
- **Korean tires sell well at a low margin** ({pct(o('South Korea')['margin'])}, Hankook {pct(F['brands']['Hankook']['margin'])}),
  while Chinese, Vietnamese and European tires earn ~14-15 %.
- **{F['loss_n']} tires were sold below their last purchase price** - {F['gap']['Large (>15%)'][0]} of them by more than 15 %.
- **Egyptian batteries earn about twice the margin** of Varta / ACDelco; one size (TD-70) is {F['td70_share']:.0%} of battery sales.
- **An evening business:** {pct(F['evening_inv'], 0)} of invoices come after 18:00, peaking at {F['peak_hour']};
  {F['best_wd'][0]} and {F['best_wd'][1]} are the best days.

Full write-up: [docs/insights_and_recommendations.md](docs/insights_and_recommendations.md) ·
Page-by-page dashboard guide: [docs/Dashboard_Guide.pdf](docs/Dashboard_Guide.pdf)

## Dashboard (Power BI)

Open **`dashboard/Tire Shop Sales Dashboard.pbix`** in Power BI Desktop - the data is embedded, no setup needed.

| Tires | Batteries & Services |
|---|---|
| ![Tires](docs/screenshots/2-tires.png) | ![Batteries & Services](docs/screenshots/3-batteries-services.png) |
| **Pricing Alerts** | **Sales Activity** |
| ![Pricing Alerts](docs/screenshots/4-pricing-alerts.png) | ![Sales Activity](docs/screenshots/5-sales-activity.png) |

- **Model:** star schema (Products, Product Sales, Invoices, Calendar), 2 relationships, 30 DAX measures,
  sort-by columns, marked date table, a weekday x hour heat map driven by a DAX colour measure.
- **Design:** fixed colour per category, colour-blind-safe palette, every chart labelled; red is reserved for below-cost sales.
- The dashboard is also stored as a **PBIP project** (TMDL + PBIR JSON) generated and validated by
  `tools/dashboard/build_pbip.py` - every visual checked against Microsoft's report schemas.

## What I did

| Step | Work | Output |
|---|---|---|
| 1. Understand | Profiled two POS exports: an item profit report (343 products) and an invoice list ({F['inv_n']:,} invoices) | `docs/cleaning_report.md` |
| 2. Clean (Python) | Parsed free-text Arabic product names into category, tire size, brand and origin; rebuilt invoice timestamps; removed duplicates; anonymised customers; **21 automated checks** reconcile every total with the POS footers | `cleaning/`, `data/clean/` |
| 3. Explore | 7 business questions, 13 charts, written findings | `eda/tire_shop_eda.ipynb` |
| 4. Model & dashboard | Power BI star schema, DAX measures, 6 report pages | `dashboard/` |
| 5. Validate | Schema validation, field-reference checks, expected value for every visual | `docs/qa_checklist.md` |
| 6. Recommend | Prioritised, quantified recommendations for the owner | `docs/insights_and_recommendations.md` |

### Data problems solved

- **Product master in free Arabic text.** `15-65-185 كروس ويند اوروبي` becomes tire size **185/65 R15**, brand
  **Crosswind**, origin **Europe** - plus rim bolt patterns (`4x100/114.3`), battery models (`TD-70`) and 20+ spelling variants.
- **Wrong invoice dates.** The POS stamps a sale with the date of the *open shift*, not the real day. Because invoice numbers
  are sequential, {F['corrected']} timestamps were rebuilt from the sequence, with a guard that stops one bad clock time from
  shifting hundreds of later invoices.
- **Cost basis.** The POS values cost at the *last purchase price*, so "losses" are split by how far below cost they sold
  (small / medium / large) to separate pricing mistakes from supplier price increases.

## Repository structure

```
data/raw/          confidential copies of the two POS exports (identity removed, money scaled)
data/clean/        star-schema CSVs produced by the cleaning script
cleaning/          clean_data.py (pipeline + 21 validation checks), mappings.py (Arabic -> English)
eda/               tire_shop_eda.ipynb (+ HTML) and 13 charts
dashboard/         Tire Shop Sales Dashboard.pbix + PBIP project (TMDL model, PBIR report)
docs/              insights & recommendations, dashboard guide (PDF), data dictionary, QA checklist, cleaning report
tools/             facts.py (all numbers quoted in the docs), notebook / dashboard / docs builders
run_pipeline.bat   rebuild everything from data/raw
```

## How to run

```bash
pip install -r requirements.txt
python cleaning/clean_data.py      # data/raw -> data/clean (+ docs/cleaning_report.md)
python tools/build_notebook.py     # runs the analysis notebook
```

Or double-click **`run_pipeline.bat`** (Windows). Open the `.pbix` in Power BI Desktop; to load data from your own
clone, open the `.pbip`, set **Transform data > Edit parameters > DataFolder** to your `data\\clean\\` path and click Refresh.

## Confidentiality method

1. Shop name, address, tax and commercial-register numbers, logo and file metadata removed from the POS exports.
2. Customer names replaced (`Customer 01`...), then anonymised again to IDs in the clean data.
3. Every money value multiplied by one secret factor (kept offline) and rounded; each product's cost changed by a
   further random amount, so real purchase prices cannot be recovered. No product's profit sign was changed.

---
**Abdallah Mohammed** - Data Analyst · [GitHub]({GH})
"""
(ROOT / "README.md").write_text(readme, encoding="utf-8")

# =============================================================================== INSIGHTS
insights = f"""# Insights & Recommendations

*Real POS data from a tire, battery and rim shop in Egypt. Money values are scaled for confidentiality
(see README); percentages, counts and patterns are real. Cost = POS last purchase price.*

## The shop in one paragraph

The shop sold **{egp(F['revenue'])} EGP** ({F['units']:,} units across {F['products']} products) for **{egp(F['profit'])} EGP profit
({pct(F['margin'])})**. Between 1 Apr and 3 Nov 2026 it issued **{F['inv_n']:,} invoices on {F['days']} trading days - about
{egp(F['rev_per_day'])} EGP and {F['inv_per_day']:.0f} invoices a day**, average ticket {F['avg_ticket']:,.0f} EGP. Products are a
thin-margin business (about {pct(F['goods_margin'], 0)}); the **welding and rim-straightening services earn
{pct(F['Service']['profit_share'], 0)} of all profit**. It is an **evening shop**: {pct(F['evening_inv'], 0)} of invoices come after 18:00.

## Key findings

| # | Finding | Numbers |
|---|---|---|
| 1 | **Services are the profit engine** | {pct(F['Service']['rev_share'])} of revenue, **{pct(F['Service']['profit_share'], 0)} of profit**; {F['svc_jobs']:,} jobs at ~{F['svc_profit_per_job']:,.0f} EGP profit each (vs ~{F['profit_per_tire']:,.0f} per tire). |
| 2 | **Products earn thin margins** | Tires {pct(F['Tire']['margin'])}, batteries {pct(F['Battery']['margin'])}, rims {pct(F['Rim']['margin'])}. |
| 3 | **Bigger, pricier tires earn the least** | By rim size: {rims}. By price band: {big_bands}. |
| 4 | **Korean tires sell well at a low margin** | {egp(o('South Korea')['rev'])} revenue (2nd origin) at **{pct(o('South Korea')['margin'])}**; Hankook {pct(F['brands']['Hankook']['margin'])}. China {pct(o('China')['margin'])}, Vietnam {pct(o('Vietnam')['margin'])}, Europe {pct(o('Europe (unspecified)')['margin'])}. |
| 5 | **{F['loss_n']} tires sold below last purchase price** | {F['gap']['Small (<5%)'][0]} small gaps (< 5 %), {F['gap']['Medium (5-15%)'][0]} medium (5-15 %), **{F['gap']['Large (>15%)'][0]} large (> 15 %)** - worst: {loss0[0].split(' - ')[0]} sold at {loss0[2]:,.0f} vs {loss0[3]:,.0f}. |
| 6 | **Egyptian batteries earn ~2x the margin** | Chloride {pct(bl('Chloride Gold')['margin'], 0)}-{pct(bl('Chloride Standard')['margin'], 0)}, Nesr {pct(bl('Nesr')['margin'], 0)} vs Varta {pct(bl('Varta')['margin'])}, ACDelco {pct(bl('ACDelco')['margin'])}. TD-70 = {F['td70_share']:.0%} of battery units. |
| 7 | **A long tail of stock** | {F['sold_once']} products sold only once; one size ({F['size_max_name']}) is stocked in {F['size_max_n']} brands/origins. |
| 8 | **Evening business** | {pct(F['evening_inv'], 0)} of invoices after 18:00, peak {F['peak_hour']}; busiest slot {F['busiest_cell'][0]} {F['busiest_cell'][1]}. {F['late_n']} after-midnight invoices. |
| 9 | **{F['best_month']} peak, autumn slowdown** | {F['best_wd'][0]} and {F['best_wd'][1]} are the best days, {F['worst_wd']} the weakest. |
| 10 | **Few invoices carry the revenue** | Invoices of 3K+ are {pct(F['big_inv'], 0)} of invoices but **{pct(F['big_rev_share'], 0)} of revenue**; {pct(F['small_inv'], 0)} are under 1,000 EGP (mostly service jobs). |
| 11 | **No customer data** | {pct(F['walkin_share'], 0)} walk-in cash; no repeat-customer analysis is possible. |

## Recommendations

| Priority | Recommendation | Why / expected effect |
|---|---|---|
| 1 | **Update selling prices the day a more expensive batch is entered**, and add a minimum-margin warning in the POS | Cost = last purchase price, so a stale price list turns into below-cost sales. |
| 2 | **Re-price large tires (R17+)** | Lifting R17+ from {pct(F['big_margin'])} to 11 % on the same volume adds profit worth {pct(F['big_gain_11'] / F['big_rev'], 1)} of their revenue. |
| 3 | **Review Korean / Japanese / Turkish tire pricing**, or offer the 14-15 % origins in the same size | Korean tires at 12 % instead of {pct(o('South Korea')['margin'])} would add {pct(F['korea_gain_12'] / o('South Korea')['rev'], 1)} of their revenue in profit. |
| 4 | **Cross-sell during service visits** - a free tire / battery check with every welding or straightening job | Services bring the traffic and the profit; a few extra tire or battery sales a week add high-value tickets. |
| 5 | **Push Egyptian battery lines** when the customer has no brand preference | Roughly double the margin on the same TD-70 sale. |
| 6 | **Trim the long tail** - keep 3-5 brands per popular size across price points | Frees cash tied up in slow stock. |
| 7 | **Record a phone number on every invoice** | Enables repeat-customer analysis and reminders. |
| 8 | **Staff for 19:00-23:00**; review opening before 12:00 | Mornings bring only {pct(F['morning_share'], 0)} of invoices. |

## Caveats

- Margins are **at last purchase price**: when supplier prices rise, past profit is understated and some sales look like losses.
- Item revenue and invoice revenue cover different periods (item report to 22 Nov, invoices to 3 Nov).
- {F['corrected']} invoice dates were corrected because the POS kept the open shift's date - see `cleaning_report.md`.
"""
(DOCS / "insights_and_recommendations.md").write_text(insights, encoding="utf-8")

# =============================================================================== QA
qa_rows = [
    ("Overview", "Revenue / Profit / Margin", f"{egp(F['revenue'])} / {egp(F['profit'])} / {pct(F['margin'])}"),
    ("Overview", "Units sold / Invoices / Average ticket", f"{F['units']:,} / {F['inv_n']:,} / {F['avg_ticket']:,.0f}"),
    *[("Overview", f"{c}: revenue / profit / margin", f"{F[c]['rev']:,.0f} / {F[c]['profit']:,.0f} / {pct(F[c]['margin'])}")
      for c in ["Tire", "Battery", "Rim", "Service"]],
    ("Overview", "Monthly invoice revenue", ", ".join(f"{k} {egp(v[0])}" for k, v in F["months"].items())),
    ("Tires", "Margin by rim size", rims),
    ("Tires", "Margin by price band", big_bands),
    ("Batteries & Services", "Battery revenue / margin / units", f"{egp(F['Battery']['rev'])} / {pct(F['Battery']['margin'])} / {F['Battery']['units']}"),
    ("Batteries & Services", "Service profit / jobs / profit per job", f"{egp(F['Service']['profit'])} / {F['svc_jobs']:,} / {F['svc_profit_per_job']:,.0f}"),
    ("Pricing Alerts", "Below cost / lost / revenue on them / 0-5 % products", f"{F['loss_n']} / {F['loss_amt']:,.0f} / {F['loss_rev']:,.0f} / {F['low_margin_n']}"),
    ("Pricing Alerts", "Products by margin band", ", ".join(f"{b} {n}" for b, n, _ in F["margin_bands"])),
    ("Sales Activity", "Revenue / trading days / revenue per day", f"{egp(F['inv_rev'])} / {F['days']} / {egp(F['rev_per_day'])}"),
    ("Sales Activity", "Busiest heat-map cell", f"{F['busiest_cell'][0]} {F['busiest_cell'][1]} ({F['busiest_cell_n']} invoices)"),
]
qa = "\n".join([
    "# Dashboard QA checklist", "",
    "## Automated checks", "",
    "| Check | Result |", "|---|---|",
    "| Cleaning: totals reconcile with both POS report footers (21 checks) | PASS - `cleaning_report.md` |",
    "| Report JSON validated against Microsoft's PBIR schemas | PASS - 0 errors (`tools/dashboard/validate_pbir.py`) |",
    "| Every formatting property valid for its visual type (Power BI Desktop's own schema) | PASS (`tools/dashboard/check_props.py`) |",
    "| Every table / column / measure used by a visual exists in the model | PASS |", "",
    "## Expected values (computed in Python from data/clean)", "",
    "| Page | Item | Expected |", "|---|---|---|",
    *[f"| {a} | {b} | {c} |" for a, b, c in qa_rows], ""])
(DOCS / "qa_checklist.md").write_text(qa, encoding="utf-8")

# =============================================================================== GUIDE
CSS = (ROOT / "tools" / "guide.css").read_text(encoding="utf-8")


def table(head, rows):
    h = "".join(f"<th>{x}</th>" for x in head)
    body = "".join("<tr>" + "".join(f'<td class="n">{r[0]}</td>' + "".join(f"<td>{x}</td>" for x in r[1:])) + "</tr>"
                   for r in rows)
    return f"<table><tr>{h}</tr>{body}</table>"


def section(n, title, sub, img, parts):
    return (f'<div class="page"><h2>{n}. {title}</h2><div class="sub">{sub}</div>'
            f'<img class="shot" src="../screenshots/{img}"><div class="cap">{title} page as it appears in Power BI Desktop.</div>'
            + "".join(parts) + "</div>")


def h3(t):
    return f"<h3>{t}</h3>"


def box(t, kind=""):
    return f'<div class="box {kind}">{t}</div>'


cover = f"""
<div class="cover">
  <div><span class="tag">Power BI</span><span class="tag">6 pages</span><span class="tag">Real data, scaled</span></div>
  <h1>Tire Shop Sales Dashboard</h1>
  <p>Page-by-page guide: what every visual shows, how to read it, what the numbers say, and what to do about it.</p>
  <p style="margin-top:14px">Real POS data from a tire, battery and rim shop in Egypt. Money values are scaled for
  confidentiality; percentages, counts and patterns are real.</p>
</div>
{h3("Contents")}
<table class="toc"><tr><td>1.</td><td><b>Overview</b> - the whole shop in one screen</td></tr>
<tr><td>2.</td><td><b>Tires</b> - margin by size, selling price, origin and brand</td></tr>
<tr><td>3.</td><td><b>Batteries &amp; Services</b> - battery lines, service jobs and rims</td></tr>
<tr><td>4.</td><td><b>Pricing Alerts</b> - products sold below cost</td></tr>
<tr><td>5.</td><td><b>Sales Activity</b> - days, weekdays, hours, ticket sizes</td></tr>
<tr><td>6.</td><td><b>Data Notes</b> - sources, confidentiality and definitions</td></tr></table>
{h3("Where the numbers come from")}
{table(["Source", "What it contains", "Used on"], [
    ("Item profit report", f"{F['products']} products with quantity, revenue, cost and profit (all time). <b>No dates</b>.", "Overview (top), Tires, Batteries &amp; Services, Pricing Alerts"),
    ("Invoice list", f"{F['inv_n']:,} invoices, 1 Apr - 3 Nov 2026, with date, time and amount. <b>No products</b>.", "Overview (month chart), Sales Activity")])}
{box("The two exports cannot be joined, so a product filter does not change invoice visuals and a month filter does not change product visuals.")}
{h3("How to use the dashboard")}
<ul><li><b>Change page:</b> the tabs at the bottom of Power BI Desktop, or Ctrl + click the tabs in the dark header.</li>
<li><b>Slicers:</b> the drop-downs at the top-left of a page. Choose "All" to clear.</li>
<li><b>Cross-filter:</b> click a bar, table row or heat-map cell; click again to clear.</li>
<li><b>Details:</b> hover over any bar, dot or cell.</li></ul>
{h3("Colour code")}
{table(["Colour", "Meaning"], [
    ('<span class="chip" style="background:#2a78d6"></span>Blue', "Tires, and single-measure charts"),
    ('<span class="chip" style="background:#eb6834"></span>Orange', "Batteries"),
    ('<span class="chip" style="background:#1baf7a"></span>Green', "Rims"),
    ('<span class="chip" style="background:#eda100"></span>Yellow', "Services"),
    ('<span class="chip" style="background:#d03b3b"></span>Red', "Sold below cost / negative margin"),
    ('<span class="chip" style="background:#a35f00"></span>Amber text', "Margin below 8 % in tables")])}
{box("<b>Cost basis.</b> The POS values cost at the <b>last purchase price</b>, so margins are conservative when supplier prices rise.", "warn")}
"""

s1 = section(1, "Overview", "The whole shop in one screen. <b>Use it as a 30-second health check.</b>", "1-overview.png", [
    h3("Top row - six headline cards"),
    table(["Card", "What it means", "Value"], [
        ("Revenue (EGP)", "Sales value of all products and services (item report).", egp(F["revenue"])),
        ("Profit (EGP)", "Revenue minus cost (cost = last purchase price).", egp(F["profit"])),
        ("Margin", "Profit / Revenue.", pct(F["margin"])),
        ("Units sold", "Tires, batteries, rims and service jobs.", f"{F['units']:,}"),
        ("Invoices", "Invoices in the invoice export.", f"{F['inv_n']:,}"),
        ("Average ticket", "Invoice revenue / invoices.", f"{F['avg_ticket']:,.0f}")]),
    h3("Category charts and month chart"),
    table(["Visual", "How to read it", "What it says"], [
        ("Revenue by category", "Bar length = money taken in.", f"Tires bring {pct(F['Tire']['rev_share'], 0)} of revenue."),
        ("Profit by category", "Same categories, profit instead of revenue.", f"<b>Services make {pct(F['Service']['profit_share'], 0)} of profit</b>; tires {pct(F['Tire']['profit_share'], 0)}."),
        ("Margin by category", "Profit as % of revenue.", f"Tires {pct(F['Tire']['margin'])}, batteries {pct(F['Battery']['margin'])}, rims {pct(F['Rim']['margin'])}; services 100 % (costs already deducted)."),
        ("Invoice revenue by month", "One column per month (November = 3 days only).", f"{F['best_month']} is the peak; September-October are the weakest full months."),
        ("Key findings box", "Four plain-language conclusions.", "Services drive profit; thin goods margins; below-cost tires; evening business.")]),
])
s2 = section(2, "Tires", "Which tire sizes, prices, origins and brands earn money. Filtered to tires only.", "2-tires.png", [
    h3("Slicers, cards and charts"),
    table(["Visual", "How to read it", "What it says"], [
        ("Slicers", "Rim size, origin, brand, tire type - filter every visual on the page.", "-"),
        ("Cards", "Tire revenue, profit, margin, tires sold.", f"{egp(F['Tire']['rev'])} / {egp(F['Tire']['profit'])} / {pct(F['Tire']['margin'])} / {F['Tire']['units']:,}"),
        ("Margin by rim size", "One column per wheel size.", f"<b>Big sizes earn the least</b>: R17+ {pct(F['big_margin'])}. ({rims})"),
        ("Margin by selling price", "Tires grouped by average selling price.", f"Best volume band {F['best_band']}: {pct(F['best_band_margin'])}; 4K+: {pct(F['price_bands'][-1][1])}."),
        ("Price vs margin", "Each dot = one tire; dot size = tires sold; red = sold below cost.", f"The red dots under zero are the {F['loss_n']} below-cost products."),
        ("By country of origin", "Revenue, highest first.", f"Thailand {pct(o('Thailand')['margin'])}; <b>South Korea {pct(o('South Korea')['margin'])}</b>; China {pct(o('China')['margin'])}."),
        ("By brand", "Profit, highest first.", f"{', '.join(F['brands_top'])} lead; Hankook {pct(F['brands']['Hankook']['margin'])} (amber)."),
        ("Best-selling sizes", "Units, highest first.", ", ".join(f"{k} ({v['units']})" for k, v in F["sizes_top"].items()))]),
    box("<b>Use it for</b> pricing and buying: pick an origin or a size in the slicers to see which brands pull the margin down.", "good"),
])
s3 = section(3, "Batteries &amp; Services", "Batteries, the welding / rim-straightening services, and rims.", "3-batteries-services.png", [
    table(["Visual", "How to read it", "What it says"], [
        ("Cards", "Battery revenue / margin / units; service profit, jobs, profit per job; rim revenue.",
         f"{egp(F['Battery']['rev'])} / {pct(F['Battery']['margin'])} / {F['Battery']['units']}; {egp(F['Service']['profit'])} / {F['svc_jobs']:,} / {F['svc_profit_per_job']:,.0f}; {egp(F['Rim']['rev'])}"),
        ("Battery revenue by line", "Bars sorted by sales.", f"{', '.join(F['bat_top'])} are the biggest lines."),
        ("Battery margin by line", "Lines sorted by margin.", f"Egyptian brands lead: Nesr {pct(bl('Nesr')['margin'], 0)}, Chloride {pct(bl('Chloride Standard')['margin'], 0)}; Varta {pct(bl('Varta')['margin'])}, ACDelco {pct(bl('ACDelco')['margin'])}."),
        ("Services table", "Jobs, revenue, profit, average price per job.", f"Welding {F['weld_jobs']:,} jobs; rim straightening {F['straight_jobs']} jobs."),
        ("Batteries sold by model", "Units per battery model.", f"<b>TD-70 = {F['td70_share']:.0%} of batteries</b>."),
        ("Rims table", "Each rim with bolt pattern and margin.", f"{F['rims_n']} rims, each sold once; {pct(F['Rim']['margin'])} margin.")]),
])
s4 = section(4, "Pricing Alerts", "Products sold below their last purchase price.", "4-pricing-alerts.png", [
    table(["Visual", "How to read it", "What it says"], [
        ("Slicers", "Category; how far below cost (small < 5 %, medium 5-15 %, large > 15 %).", "-"),
        ("Cards", "Products below cost / amount lost / their revenue / products at 0-5 %.", f"{F['loss_n']} / {F['loss_amt']:,.0f} / {F['loss_rev']:,.0f} / {F['low_margin_n']}"),
        ("Loss by product", "Red bars = EGP lost, biggest first.", f"{loss0[0]} lost the most."),
        ("Margin bands", "Revenue and number of products per margin level.", ", ".join(f"{b} {n}" for b, n, _ in F["margin_bands"])),
        ("Below-cost table", "Each loss product with selling price vs last purchase price.", f"Example: {loss0[0].split(' - ')[0]} at {loss0[2]:,.0f} vs {loss0[3]:,.0f} ({pct(loss0[4])}).")]),
    box("<b>How to act on it.</b> Filter <i>Large</i> gaps and check purchase history: a supplier price jump after the sale is a cost effect, "
        "otherwise it was a pricing mistake. Going forward, update prices the day a more expensive batch arrives.", "warn"),
])
s5 = section(5, "Sales Activity", "When the shop sells, and how big the bills are (invoice list).", "5-sales-activity.png", [
    table(["Visual", "How to read it", "What it says"], [
        ("Cards", "Revenue, invoices, trading days, revenue per day, average ticket.", f"{egp(F['inv_rev'])} / {F['inv_n']:,} / {F['days']} / {egp(F['rev_per_day'])} / {F['avg_ticket']:,.0f}"),
        ("Daily revenue", "Grey = each day; blue = 7-day average.", f"Peak in {F['best_month']}; gap = Eid al-Adha closure (26 May - 2 Jun)."),
        ("Revenue per day by weekday", "Average day for each weekday.", f"<b>{F['best_wd'][0]} and {F['best_wd'][1]} are best</b>; {F['worst_wd']} weakest."),
        ("Heat map", "Weekday x hour; darker = more invoices.", f"Busiest: <b>{F['busiest_cell'][0]} {F['busiest_cell'][1]}</b>; mornings before 12:00 = {pct(F['morning_share'], 0)} of invoices."),
        ("Share of invoices vs revenue", "Grey = % of invoices, blue = % of revenue, per bill size.", f"Bills of 3K+ are {pct(F['big_inv'], 0)} of invoices but <b>{pct(F['big_rev_share'], 0)} of revenue</b>.")]),
])
s6 = section(6, "Data Notes", "Reference page: sources, confidentiality, definitions and limitations.", "6-data-notes.png", [
    box("Explains that the data is real but confidential (scaled money values), how cost is measured, what the cleaning "
        "did, and the definitions of every band and measure."),
])
html = (f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Tire Shop Sales Dashboard - Guide</title>'
        f"<style>{CSS}</style></head><body>{cover}{s1}{s2}{s3}{s4}{s5}{s6}"
        f'<div class="foot">Tire Shop Sales &amp; Profit Analytics - {GH}</div></body></html>')
(DOCS / "guide").mkdir(exist_ok=True)
(DOCS / "guide" / "Dashboard_Guide.html").write_text(html, encoding="utf-8")
print("docs written: README.md, insights, qa_checklist, guide html")
