# Data dictionary - data/clean/

All files are UTF-8 CSV produced by `cleaning/clean_data.py`. Money is in EGP.
**Cost = DEXEF last purchase price** (replacement cost), so profit and margin are "at last purchase price".

## Model

```
dim_product (product_id) 1 ──── 1 fact_item_sales (product_id)

dim_date (date) 1 ──── * fact_invoices (business_date)
```

The two fact tables are **not** connected: the DEXEF item report has no dates or
invoice numbers. Product pages use `fact_item_sales`; time pages use `fact_invoices`.

## dim_product - one row per POS product (343)

| Column | Description |
|---|---|
| product_id | Row number in the DEXEF item report (key) |
| product_name_ar | Original Arabic name from the POS |
| product_name_en | English display name, e.g. `185/65 R15 Crosswind - Europe (unspecified)` |
| category | Tire, Battery, Rim, Service, Accessory |
| brand | English brand (services: `Shop Service`) |
| product_line | Brand plus line where relevant (`Chloride Gold` vs `Chloride Standard`) |
| origin_country | Country of manufacture as written in the name; `Unknown` if absent |
| origin_region | East Asia, Southeast Asia, South Asia, Europe, Middle East & Africa |
| tire_width_mm / tire_aspect_ratio / rim_diameter_in | Tire size parts (185 / 65 / 15). `rim_diameter_in` is also filled for rims |
| rim_size_label | `R15` (tires and rims), sorted by rim_diameter_in |
| tire_size | `185/65 R15`; light-truck sizes without aspect show as `195 R14` |
| tire_type | Passenger or Light Truck |
| load_index / speed_rating | When written in the name (e.g. 88 / H) |
| is_xl / is_run_flat / ply_rating | Reinforced, run-flat, ply count (10PR) |
| rim_bolt_count / rim_pcd | Bolt pattern, e.g. `4x100/114.3` |
| rim_width_in / rim_offset_et / rim_finish / is_oem | Rim width (inch), ET offset, colour/style, original-equipment flag |
| battery_model / battery_family | e.g. `TD-70` / `TD`, `DIN-74L` / `DIN` |
| tags | New model, Line, White line, Rim protector, Light truck, Run-flat, ... |
| is_possible_duplicate | Same product entered twice in the POS |

## fact_item_sales - all-time totals per product (343)

| Column | Description |
|---|---|
| product_id | Key to dim_product |
| qty_sold, revenue, cost, profit | From the DEXEF report (profit = revenue - cost) |
| unit_price, unit_cost, unit_profit | Per-unit averages |
| margin_pct | profit / revenue (0.12 = 12 %) |
| revenue_share, profit_share | Share of shop total |
| is_loss | profit < 0 |
| is_zero_cost | No cost recorded (the two services). Owner confirmed service costs are small and already deducted from service revenue |
| price_band / price_band_order | Tires only: average selling price band `< 1.5K` ... `4K+` |
| margin_band / margin_band_order | `Below cost`, `0-5%`, `5-10%`, `10-15%`, `15-20%`, `20%+`, `Service` |
| loss_gap_band / loss_gap_order | Loss products only: how far below cost - `Small (<5%)`, `Medium (5-15%)`, `Large (>15%)` |
| sale_status | `Profitable` or `Sold below cost` |
| abc_class | A = products making the first 80 % of profit, B = next 15 %, C = rest |
| profit_rank | 1 = most profitable product |

## fact_invoices - one row per invoice (2,036)

| Column | Description |
|---|---|
| invoice_no | POS invoice number (key) |
| invoice_datetime | Corrected real date-time (see cleaning report) |
| invoice_date | Calendar date of invoice_datetime |
| business_date | Trading day: sales before 05:00 count for the previous day. **Use this for the date relationship** |
| invoice_hour | 0-23 from invoice_datetime |
| hour_label / hour_sort | `21:00`; sort puts 00:00 and 01:00 after 23:00 (business-day order) |
| is_after_midnight | Sold between 00:00 and 04:59 |
| is_date_corrected / days_shifted | POS date was fixed and by how many days |
| is_time_estimated | POS clock time impossible; time copied from the next invoice (exclude from hour charts) |
| customer_type / customer_id | Walk-in or Named customer; names replaced by C001... |
| items_count | Number of lines on the invoice |
| gross_amount, discount, tax, net_amount, paid_amount, due_amount | Invoice money fields (net = gross - discount + tax = paid + due) |
| payment_status | Paid, Partially paid, Unpaid |
| has_discount | discount > 0 |
| ticket_band / ticket_band_order | `< 300`, `300-999`, `1K-2.9K`, `3K-9.9K`, `10K+` |
| is_near_zero | net < 1 EGP (one 0.005 EGP invoice) |

## dim_date - one row per day, 2026-04-01 to 2026-11-30

| Column | Description |
|---|---|
| date | Key |
| year, quarter, month_num, month_name, month_short, year_month, month_start | Month attributes (sort month_name by month_num) |
| day_of_month | 1-31 |
| weekday_name, weekday_short, weekday_num | Saturday = 1 ... Friday = 7 (Egyptian week) |
| week_start | Saturday that starts the week |
| is_friday | Weekend flag |
