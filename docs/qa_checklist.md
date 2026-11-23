# Dashboard QA checklist

## Automated checks

| Check | Result |
|---|---|
| Cleaning: totals reconcile with both POS report footers (21 checks) | PASS - `cleaning_report.md` |
| Report JSON validated against Microsoft's PBIR schemas | PASS - 0 errors (`tools/dashboard/validate_pbir.py`) |
| Every formatting property valid for its visual type (Power BI Desktop's own schema) | PASS (`tools/dashboard/check_props.py`) |
| Every table / column / measure used by a visual exists in the model | PASS |

## Expected values (computed in Python from data/clean)

| Page | Item | Expected |
|---|---|---|
| Overview | Revenue / Profit / Margin | 3.76M / 903K / 24.0% |
| Overview | Units sold / Invoices / Average ticket | 3,189 / 2,036 / 1,698 |
| Overview | Tire: revenue / profit / margin | 2,285,925 / 266,675 / 11.7% |
| Overview | Battery: revenue / profit / margin | 691,785 / 92,035 / 13.3% |
| Overview | Rim: revenue / profit / margin | 276,645 / 36,040 / 13.0% |
| Overview | Service: revenue / profit / margin | 507,575 / 507,575 / 100.0% |
| Overview | Monthly invoice revenue | Apr 428K, May 488K, Jun 465K, Jul 680K, Aug 548K, Sep 410K, Oct 414K |
| Tires | Margin by rim size | R12 23.2%, R13 13.9%, R14 13.3%, R15 13.7%, R16 11.7%, R17 8.9%, R18 7.9%, R19 9.3%, R20 9.1% |
| Tires | Margin by price band | < 1.5K 14.2%, 1.5K-2K 14.7%, 2K-2.5K 10.4%, 2.5K-3K 9.6%, 3K-4K 11.1%, 4K+ 3.7% |
| Batteries & Services | Battery revenue / margin / units | 692K / 13.3% / 334 |
| Batteries & Services | Service profit / jobs / profit per job | 508K / 1,706 / 298 |
| Pricing Alerts | Below cost / lost / revenue on them / 0-5 % products | 21 / 10,920 / 101,690 / 26 |
| Pricing Alerts | Products by margin band | Below cost 21, 0-5% 26, 5-10% 62, 10-15% 117, 15-20% 65, 20%+ 50, Service 2 |
| Sales Activity | Revenue / trading days / revenue per day | 3.46M / 208 / 17K |
| Sales Activity | Busiest heat-map cell | Saturday 21:00 (46 invoices) |
