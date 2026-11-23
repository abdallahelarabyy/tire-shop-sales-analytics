# Phase 2 - Cleaning report

Generated 2026-11-23 03:04 by `cleaning/clean_data.py`.
Item report printed by DEXEF: الأحد, 22 نوفمبر, 2026 11:03 م

## Output tables

| File | Rows | Grain |
|---|---|---|
| dim_product.csv | 343 | one row per POS product |
| fact_item_sales.csv | 343 | all-time totals per product (no dates) |
| fact_invoices.csv | 2036 | one row per invoice (source: 2039) |
| dim_date.csv | 244 | one row per day 2026-04-01 to 2026-11-30 |

## Validation checks

| Check | Result | Detail |
|---|---|---|
| Every product classified into a category | PASS |  |
| Every product mapped to an English brand | PASS |  |
| English product names are unique | PASS |  |
| Row profit = revenue - cost (source) | PASS |  |
| Item qty_sold total matches report footer | PASS | 3,189.00 vs 3,189.00 |
| Item revenue total matches report footer | PASS | 3,762,220.00 vs 3,762,220.00 |
| Item cost total matches report footer | PASS | 2,859,715.00 vs 2,859,715.00 |
| Item profit total matches report footer | PASS | 902,505.00 vs 902,505.00 |
| All quantities positive | PASS |  |
| Time column is a copy of the date column | PASS |  |
| Invoice numbers unique after de-duplication | PASS |  |
| Corrected timestamps never go backwards | PASS |  |
| Invoice gross_amount total = footer - removed duplicates | PASS | 3,456,440.00 vs 3,456,440.00 |
| Invoice discount total = footer - removed duplicates | PASS | 35.00 vs 35.00 |
| Invoice tax total = footer - removed duplicates | PASS | 0.00 vs 0.00 |
| Invoice net_amount total = footer - removed duplicates | PASS | 3,456,405.00 vs 3,456,405.00 |
| Invoice paid_amount total = footer - removed duplicates | PASS | 3,449,540.00 vs 3,449,540.00 |
| Invoice due_amount total = footer - removed duplicates | PASS | 6,865.00 vs 6,865.00 |
| gross - discount + tax = net on every invoice | PASS |  |
| net = paid + due on every invoice | PASS |  |
| No negative amounts | PASS |  |

## Data flags

**Products entered twice in the POS (same name after normalising spelling)** (2)
- #32 `13-70-185 ليو تايلاندى`
- #35 `13-70-185ليو تايلاندي`

**Tires/batteries with unknown country of origin (most rims have none, not listed)** (3)
- #10 `13-70-165 صن وايد` -> 165/70 R13 Sunwide - Unknown
- #30 `13-70-185 اي بلس` -> 185/70 R13 E-Plus - Unknown
- #343 `هوجل DIN-44` -> Hugel DIN-44 - Unknown

**Duplicate invoice rows removed** (3)
- #1794 2026-10-06 13:13 115 EGP
- #1656 2026-09-15 00:18 365 EGP
- #481 2026-05-16 00:21 440 EGP

**Invoice numbers missing from the export (deleted/voided in POS?)** (9)
- #133
- #134
- #300
- #967
- #975
- #1101
- #1313
- #1340
- #1935

**Invoice timestamps corrected (POS kept the previous shift date)**
- 117 invoices moved forward by 1 day(s): 105, 2 day(s): 7, 3 day(s): 3, 5 day(s): 1, 17 day(s): 1

**Invoices whose clock time is impossible (time estimated from the next invoice)** (1)
- #1133 stamped 2026-07-22 15:01 -> 2026-07-23 12:18

**Large date corrections (> 2 days, check in POS)** (5)
- #552 stamped 2026-05-19 19:19 -> 2026-05-24 19:19
- #1086 stamped 2026-07-16 17:40 -> 2026-07-19 17:40
- #1088 stamped 2026-07-16 18:43 -> 2026-07-19 18:43
- #1093 stamped 2026-07-16 21:42 -> 2026-07-19 21:42
- #1474 stamped 2026-08-09 20:34 -> 2026-08-26 20:34

**Near-zero invoices (kept, flagged is_near_zero)** (1)
- #992 0 EGP

**Brand transliterations to confirm with the shop**

- AC Power, Actron, Adler, Avantech, E-Plus, Enforged, Flow Stark, Fosin, Hugel, Kinto, Kristal, Laiken, Linstone, Lionlord, Matrix, Maxxen, Nesr, Orio, Polo, Tarzano

## Known limitations

- The item report has no dates or invoice numbers, so product sales cannot be split by month or linked to invoices.
- Services (welding, rim straightening) have zero recorded cost (`is_zero_cost`). The owner confirmed their costs are small and already deducted from the service revenue, so the recorded service profit is used as-is.
- Cost is DEXEF's **last purchase price** (replacement cost), not the price paid for the units sold; when supplier prices rise, margins look lower and some sales show as losses.
- Item revenue (3,762,220) exceeds invoice net (3,456,405); the invoice export ends 2026-11-03 while the item report covers all time up to its print date.