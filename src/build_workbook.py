"""Step 6: Excel workbook with live formulas. Counts come from SQL; support, confidence and lift are Excel formulas."""
from pathlib import Path
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.chart import BarChart, Reference
ROOT = Path(__file__).resolve().parents[1]; R = ROOT/"results"
wb = Workbook(); F = "Arial"
H = Font(name=F, bold=True, color="FFFFFF"); HF = PatternFill("solid", fgColor="3D2E1E")
B = Font(name=F); BL = Font(name=F, color="0000FF"); BD = Font(name=F, bold=True)
YEL = PatternFill("solid", fgColor="FFFF00")
def head(ws, row, cols):
    for i, c in enumerate(cols, 1):
        x = ws.cell(row, i, c); x.font, x.fill = H, HF; x.alignment = Alignment(wrap_text=True, vertical="center")
def widths(ws, w):
    for i, v in enumerate(w, 1): ws.column_dimensions[chr(64+i)].width = v

# README sheet
ws = wb.active; ws.title = "Read me"
lines = ["VEETNIC market basket analysis (SYNTHETIC DATA)", "",
 "All data in this workbook was generated for the project. It is not real VEETNIC data.",
 "Order counts come from the SQL pipeline (sql/ folder). Support, confidence and lift are live Excel formulas.",
 "Blue = value from SQL. Black = formula. Yellow = change me.",
 "Sheets: Pair rules (change the minimum-orders cell), Category sales, Monthly sales, Data quality log."]
for i, t in enumerate(lines, 1): ws.cell(i, 1, t).font = BD if i == 1 else B
ws.column_dimensions["A"].width = 110

# Pair rules
p = pd.read_csv(R/"pair_rules.csv").sort_values("lift", ascending=False).reset_index(drop=True)
ws = wb.create_sheet("Pair rules")
ws["A1"], ws["B1"] = "Total orders", int(p.total_orders.iloc[0]); ws["A2"], ws["B2"] = "Minimum orders together", 30
for c in ("A1", "A2"): ws[c].font = BD
ws["B1"].font = BL; ws["B2"].font = BL; ws["B2"].fill = YEL
ws["C2"] = "Assumption: pairs seen in fewer orders than this are ignored as noise. Change it and column K updates."; ws["C2"].font = B
cols = ["Product A", "Product B", "Orders with A", "Orders with B", "Orders together", "Support", "Confidence A→B", "Confidence B→A", "Lift", "Strong link? (lift ≥ 1.5)", "Counts as a rule?"]
head(ws, 4, cols); ws.row_dimensions[4].height = 32
for i, r in enumerate(p.itertuples(), 5):
    ws.cell(i, 1, r.product_a); ws.cell(i, 2, r.product_b)
    for j, v in zip((3, 4, 5), (r.orders_a, r.orders_b, r.orders_together)): ws.cell(i, j, int(v)).font = BL
    ws.cell(i, 6, f"=E{i}/$B$1").number_format = "0.0%"
    ws.cell(i, 7, f"=E{i}/C{i}").number_format = "0.0%"
    ws.cell(i, 8, f"=E{i}/D{i}").number_format = "0.0%"
    ws.cell(i, 9, f"=(E{i}/C{i})/(D{i}/$B$1)").number_format = "0.00"
    ws.cell(i, 10, f'=IF(I{i}>=1.5,"Yes","No")')
    ws.cell(i, 11, f'=IF(E{i}>=$B$2,"Yes","No")')
    for j in (1, 2, 6, 7, 8, 9, 10, 11): ws.cell(i, j).font = B
n = len(p) + 4
ws.cell(n + 2, 1, "Rules counted").font = BD; ws.cell(n + 2, 5, f'=COUNTIF(K5:K{n},"Yes")').font = B
ws.cell(n + 3, 1, "Strong links among counted rules").font = BD; ws.cell(n + 3, 5, f'=COUNTIFS(K5:K{n},"Yes",J5:J{n},"Yes")').font = B
widths(ws, [18, 18, 13, 13, 14, 10, 14, 14, 8, 16, 14]); ws.freeze_panes = "A5"

# Category sales
c = pd.read_csv(R/"category_sales.csv"); ws = wb.create_sheet("Category sales")
head(ws, 1, ["Category", "Units", "Revenue (USD)", "Gross profit (USD)", "Gross margin"])
for i, r in enumerate(c.itertuples(), 2):
    ws.cell(i, 1, r.category).font = B
    for j, v in zip((2, 3, 4), (r.units, r.revenue, r.gross_profit)): x = ws.cell(i, j, float(v)); x.font = BL
    ws.cell(i, 2).number_format = "#,##0"; ws.cell(i, 3).number_format = ws.cell(i, 4).number_format = "$#,##0"
    ws.cell(i, 5, f"=D{i}/C{i}").number_format = "0.0%"; ws.cell(i, 5).font = B
t = len(c) + 2
ws.cell(t, 1, "Total").font = BD
for j, L in ((2, "B"), (3, "C"), (4, "D")): ws.cell(t, j, f"=SUM({L}2:{L}{t-1})").font = BD
ws.cell(t, 2).number_format = "#,##0"; ws.cell(t, 3).number_format = ws.cell(t, 4).number_format = "$#,##0"
ws.cell(t, 5, f"=D{t}/C{t}").number_format = "0.0%"; ws.cell(t, 5).font = BD
ws.cell(t + 2, 1, "Gross profit = revenue minus product cost. Rent, wages and other operating costs are not in this data.").font = B
widths(ws, [26, 10, 16, 18, 14])
ch = BarChart(); ch.type = "bar"; ch.title = "Revenue by category (USD)"; ch.legend = None; ch.roundedCorners = False
ch.add_data(Reference(ws, min_col=3, min_row=1, max_row=t - 1), titles_from_data=True); ch.set_categories(Reference(ws, min_col=1, min_row=2, max_row=t - 1))
ch.x_axis.delete = False; ch.y_axis.delete = False; ch.height, ch.width = 7, 14; ch.series[0].graphicalProperties.solidFill = "B85C45"
ws.add_chart(ch, "G2")

# Monthly
m = pd.read_csv(R/"monthly_sales.csv"); ws = wb.create_sheet("Monthly sales")
head(ws, 1, ["Month", "Orders", "Revenue (USD)", "Gross profit (USD)", "Gross margin"])
for i, r in enumerate(m.itertuples(), 2):
    ws.cell(i, 1, r.month).font = B
    for j, v in zip((2, 3, 4), (r.orders, r.revenue, r.gross_profit)): ws.cell(i, j, float(v)).font = BL
    ws.cell(i, 3).number_format = ws.cell(i, 4).number_format = "$#,##0"
    ws.cell(i, 5, f"=D{i}/C{i}").number_format = "0.0%"; ws.cell(i, 5).font = B
widths(ws, [12, 10, 16, 18, 14])

# DQ log
d = pd.read_csv(R/"dq_log.csv"); ws = wb.create_sheet("Data quality log")
head(ws, 1, ["Step", "Check", "Lines", "Treatment"])
for i, r in enumerate(d.itertuples(), 2):
    ws.cell(i, 1, int(r.step)).font = B; ws.cell(i, 2, r.check_name).font = B; ws.cell(i, 3, int(r.n)).font = BL; ws.cell(i, 4, r.treatment).font = B
ws.cell(len(d) + 3, 1, "Check").font = BD
ws.cell(len(d) + 3, 2, "Raw lines minus repeat scans minus zero-quantity lines = clean lines?").font = B
ws.cell(len(d) + 3, 3, '=IF(C2-C6-C8=C10,"OK","MISMATCH")').font = BD
widths(ws, [7, 52, 10, 70])
wb.save(ROOT/"VEETNIC_Market_Basket_Synthetic.xlsx")
