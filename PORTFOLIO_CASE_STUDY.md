# Case study: VEETNIC market basket analysis

**Note:** all data is synthetic and was generated for this project.

**Background.** As a Data Analyst at VEETNIC Enterprises (2024), I combined monthly sales from two retail systems. The real data belongs to the business, so this project rebuilds the method on synthetic data.

**The problem.** A small retail business sells through two systems that export differently. The owner wants to know where money is made and which products belong together on the shelf.

**What I did.** I generated two realistic raw exports with known data problems, then cleaned and combined them in SQL with a logged rule for every change. I measured revenue, gross profit and discounts, then ran a market basket analysis using support, confidence and lift. I rebuilt the pair results in pandas to confirm the SQL, and built an Excel workbook where the metrics are live formulas.

**What I found.** Gross margin was 30.7% on $37.8K of revenue. Cleaning products earned the best margin, and Breakfast brought in the most revenue. The strongest pair was Floor Cleaner and Wall Cleaner, bought together about twice as often as chance (lift 2.03). Because I planted these patterns, finding them confirms the method works. Two unplanted pairs also showed high lift on fewer than 40 orders each. That is a useful reminder that a high lift on a small count can be pure noise.

**What I would recommend.** Bundle the cleaning products, keep the breakfast staples together, and test any bundle on real orders first.

**What I would do with real data.** Check the cleaning rules against the real exports, add a time-of-week view, and test whether the pairs hold on a held-out month.

**Skills shown.** Excel, SQL (CTEs, window functions, joins), data cleaning and reconciliation, market basket analysis, Python, validation, and clear charts.
