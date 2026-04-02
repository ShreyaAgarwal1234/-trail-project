# Trail Project — SQL & Python Automation
### Submitted by: Shreya Agarwal

---

## Overview

This project demonstrates hands-on skills in MS SQL Server querying, stored procedures, Python scripting, REST API integration, and automated reporting — aligned with the trail assessment requirements.

---

## Project Structure

```
TrailProject/
├── northwind_queries.sql     → SQL queries + stored procedure
├── currency_report.py        → Python automation script
├── currency_report.csv       → Sample CSV output
├── currency_report.log       → Sample log file
└── README.md                 → Project documentation
```

---

## Part 1 — SQL: Northwind Database

**Database:** Northwind (Microsoft public sample database)  
**Server:** MS SQL Server 2022 Express — localhost\SQLEXPRESS  
**Tool:** SQL Server Management Studio (SSMS)

---

### Queries Written

**Query 1 — Total Revenue by Product Category (Highest to Lowest)**

Calculates revenue using `UnitPrice × Quantity × (1 - Discount)` across all order line items, grouped by category and sorted descending.

| # | Category | Total Revenue |
|---|---|---|
| 1 | Beverages | $267,868.18 |
| 2 | Dairy Products | $234,507.29 |
| 3 | Confections | $167,357.22 |
| 4 | Meat/Poultry | $163,022.36 |
| 5 | Seafood | $131,261.74 |
| 6 | Condiments | $106,047.08 |
| 7 | Produce | $99,984.58 |
| 8 | Grains/Cereals | $95,744.59 |

---

**Query 2 — Top 10 Customers by Lifetime Order Value**

Aggregates total spend per customer with their most recent order date.

| # | Customer | Lifetime Value | Last Order |
|---|---|---|---|
| 1 | QUICK-Stop | $110,277.30 | 1998-04-14 |
| 2 | Ernst Handel | $104,874.98 | 1998-05-05 |
| 3 | Save-a-lot Markets | $104,361.95 | 1998-05-01 |

---

**Query 3 — Delayed Orders (Shipped more than 7 Days After Order)**

Flags all orders where ShippedDate minus OrderDate exceeds 7 days. NULL shipped dates are excluded as unshipped orders cannot yet be confirmed delayed.

| Column | Description |
|---|---|
| OrderID | Order reference number |
| CompanyName | Customer company name |
| OrderDate | Date order was placed |
| ShippedDate | Date order was shipped |
| DaysToShip | Calculated day gap |
| ShipmentStatus | Flagged as DELAYED |

---

### Stored Procedure

`usp_NorthwindAnalyticsReport` wraps all three queries into a single callable unit with an optional parameter to adjust the delay threshold.

```sql
-- Run with default 7-day threshold:
EXEC dbo.usp_NorthwindAnalyticsReport;

-- Run with custom threshold (e.g. 10 days):
EXEC dbo.usp_NorthwindAnalyticsReport @DelayThresholdDays = 10;
```

---

## Part 2 — Python: Currency Exchange Rate Automation

**Script:** currency_report.py  
**API:** Frankfurter (api.frankfurter.app) — free, no API key required  
**Language:** Python 3.13  
**Dependency:** requests library

---

### What the Script Does

1. Fetches today's USD exchange rates from the Frankfurter API
2. Fetches yesterday's rates for day-over-day comparison
3. Calculates percentage change for each currency
4. Flags any move greater than 0.5% as Significant
5. Writes a clean CSV report with all results
6. Logs every run — timestamp, currencies fetched, errors

---

### Currencies Tracked

INR · AED · USD · EUR · GBP · BRL · MXN

> AED (UAE Dirham) is officially pegged to USD at 3.6725 and is added as a fixed rate since it does not fluctuate on the open market.

---

### Sample CSV Output

```
Currency,Today_Rate_USD,Yesterday_Rate_USD,Pct_Change,Significant
INR,83.8742,83.61,0.316,No
AED,3.6725,3.6725,0.0,No
USD,1.0,1.0,0.0,No
EUR,0.9187,0.905,1.5138,Yes
GBP,0.7923,0.7895,0.3547,No
BRL,5.0841,5.12,-0.7012,Yes
MXN,17.2314,17.19,0.2408,No
```

---

### Sample Log Output

```
2026-04-02 13:13:05 | INFO     | ============================================================
2026-04-02 13:13:05 | INFO     | Currency Report - run started
2026-04-02 13:13:05 | INFO     | Target currencies : ['INR', 'AED', 'USD', 'EUR', 'GBP', 'BRL', 'MXN']
2026-04-02 13:13:06 | INFO     | Fetching rates for 2026-04-02
2026-04-02 13:13:07 | INFO     | Rates received for: ['INR', 'USD', 'EUR', 'GBP', 'BRL', 'MXN', 'AED']
2026-04-02 13:13:07 | INFO     | Significant moves    : ['EUR', 'BRL']
2026-04-02 13:13:07 | INFO     | Errors this run      : None
2026-04-02 13:13:07 | INFO     | Currency Report - run complete
2026-04-02 13:13:07 | INFO     | ============================================================
```

---

### How to Run

```bash
# Step 1 - Install dependency
pip install requests

# Step 2 - Run the script
python currency_report.py
```

---

### Scheduling (Bonus)

**Windows Task Scheduler — every morning at 7:00 AM:**

```
schtasks /create /tn "CurrencyReport" /tr "python C:\TrailProject\currency_report.py" /sc DAILY /st 07:00
```

**Linux / Mac Cron:**

```
0 7 * * * /usr/bin/python3 /path/to/currency_report.py
```

---

## Tech Stack

| Tool | Purpose |
|---|---|
| MS SQL Server 2022 Express | Database engine |
| SQL Server Management Studio | Query and execution tool |
| Python 3.13 | Scripting language |
| requests library | REST API calls |
| Frankfurter API | Free public exchange rate data |
| VS Code | Code editor |
| Claude AI | AI-assisted development and debugging |

---

## Skills Demonstrated

- MS SQL Server — queries, multi-table joins, aggregations, stored procedures with parameters
- Python — REST API integration, CSV generation, logging, retry logic, error handling
- Automation — scheduled execution via Task Scheduler and cron
- Documentation — inline SQL comments, structured README, clean output files
- AI Workflow — used Claude AI for scripting, debugging, and workflow automation

---

*Shreya Agarwal — Trail Project Assessment — April 2026*
