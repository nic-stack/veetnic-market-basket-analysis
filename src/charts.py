"""Step 5: portfolio-styled charts from results/*.csv."""
from pathlib import Path
import pandas as pd, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[1]; R = ROOT/"results"; C = ROOT/"charts"
TERRA, BROWN, SAND, GREY = "#B85C45", "#3D2E1E", "#E8D9C5", "#8A7F73"
plt.rcParams.update({"font.family":"DejaVu Sans","axes.spines.top":False,"axes.spines.right":False,
    "axes.edgecolor":GREY,"axes.labelcolor":BROWN,"xtick.color":BROWN,"ytick.color":BROWN,"text.color":BROWN})
NOTE = "Synthetic data generated for this project. Patterns were planted on purpose to test the method."

def finish(fig, title, sub):
    fig.text(0.01, 0.97, title, fontsize=14, weight="bold", va="top")
    fig.text(0.01, 0.915, sub, fontsize=9.5, color=GREY, va="top")
    fig.text(0.01, 0.01, NOTE, fontsize=8, color=GREY)

# 1. top pairs by lift
p = pd.read_csv(R/"pair_rules.csv"); p["pair"] = p.product_a+" + "+p.product_b
t = p.sort_values("lift").tail(8)
fig, ax = plt.subplots(figsize=(9,5.2)); fig.subplots_adjust(top=.82, bottom=.13, left=.27)
SMALL = 100   # pairs seen in fewer orders than this are shown in grey: lift on a small count is unreliable
ax.barh(t.pair, t.lift, color=[GREY if n<SMALL else TERRA if l>=1.75 else SAND for l,n in zip(t.lift, t.orders_together)],
        edgecolor=BROWN, linewidth=.5)
ax.axvline(1, color=BROWN, ls="--", lw=1); ax.text(1.02, 7.45, "lift = 1: no link beyond chance", fontsize=8, color=BROWN)
for y,(l,n) in enumerate(zip(t.lift, t.orders_together)): ax.text(l+.03, y, f"{l:.2f}  ({n} orders)", va="center", fontsize=9)
ax.set_xlim(0, 2.6); ax.set_xlabel("Lift")
finish(fig, "Floor and wall cleaner are bought together twice as often as chance",
       "Top 8 pairs by lift (pairs in fewer than 30 orders excluded). Grey = under 100 orders, likely noise."); fig.savefig(C/"top_pairs_lift.png", dpi=160); plt.close()

# 2. support vs lift
fig, ax = plt.subplots(figsize=(9,5.2)); fig.subplots_adjust(top=.82, bottom=.13)
ax.scatter(p.support*100, p.lift, s=p.orders_together/4, color=TERRA, alpha=.7, edgecolor=BROWN, linewidth=.4)
ax.axhline(1, color=BROWN, ls="--", lw=1)
for r in p.sort_values("lift").tail(4).itertuples(): ax.annotate(r.pair, (r.support*100, r.lift), xytext=(6,4), textcoords="offset points", fontsize=8)
ax.set_xlabel("Support: % of all orders containing both"); ax.set_ylabel("Lift")
finish(fig, "The strongest pairs are also among the most common", "Each dot is a product pair. Dot size = number of orders containing both."); fig.savefig(C/"support_vs_lift.png", dpi=160); plt.close()

# 3. category revenue and margin
c = pd.read_csv(R/"category_sales.csv")
fig, ax = plt.subplots(figsize=(9,4.6)); fig.subplots_adjust(top=.8, bottom=.15, left=.28)
ax.barh(c.category[::-1], c.revenue[::-1], color=TERRA, edgecolor=BROWN, linewidth=.5)
for y,(r,m) in enumerate(zip(c.revenue[::-1], c.margin_pct[::-1])): ax.text(r+200, y, f"${r:,.0f}  |  {m}% margin", va="center", fontsize=9)
ax.set_xlim(0, c.revenue.max()*1.55); ax.set_xlabel("Revenue (USD, 2024)")
finish(fig, "Breakfast leads revenue; cleaning earns the best margin", "Revenue and gross margin by category."); fig.savefig(C/"category_revenue.png", dpi=160); plt.close()

# 4. monthly revenue
m = pd.read_csv(R/"monthly_sales.csv")
fig, ax = plt.subplots(figsize=(9,4.6)); fig.subplots_adjust(top=.8, bottom=.17)
ax.plot(m.month.str[5:], m.revenue, color=TERRA, lw=2.4, marker="o", ms=5); ax.set_ylim(0, m.revenue.max()*1.2)
ax.set_xlabel("Month, 2024"); ax.set_ylabel("Revenue (USD)")
finish(fig, "Monthly revenue is steady with no clear seasonal swing", "Generated orders were spread evenly across the year, so flat is expected."); fig.savefig(C/"monthly_revenue.png", dpi=160); plt.close()
