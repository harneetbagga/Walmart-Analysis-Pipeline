#!/usr/bin/env python
from ..utilities.snowflake_connector import snowflake_conn
from os import getcwd
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Rectangle as MplRectangle
from matplotlib.gridspec import GridSpec

#Path to the graphs folder
graph_folder_path = getcwd() + "/Wallmart/graphs/"

conn = snowflake_conn()

class FuelPriceDashboard:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.df.columns = [c.lower() for c in self.df.columns]
        self._build()
 
    def _build(self):
        self.fig = plt.figure(figsize=(16, 9), facecolor="white")
        self.fig.suptitle(
            "fuel price by year",
            fontsize=20, fontweight="normal", y=0.97,
            color="#1A1A1A", fontfamily="serif"
        )
 
        gs = GridSpec(
            nrows=2, ncols=2,
            figure=self.fig,
            height_ratios=[2, 1],
            width_ratios=[1.4, 1],
            hspace=0.15,
            wspace=0.25,
            left=0.04, right=0.97,
            top=0.91, bottom=0.04,
        )
 
        self.ax_table = self.fig.add_subplot(gs[:, 0])    # left  (full height): table
        self.ax_donut = self.fig.add_subplot(gs[0, 1])    # right-top:           donut
        self.ax_kpi   = self.fig.add_subplot(gs[1, 1])    # right-bottom:        KPI card
 
        self._draw_table()
        self._draw_donut()
        self._draw_kpi()
 
    # ── pivot table ───────────────────────────────────────────────────────────
 
    def _draw_table(self):
        ax = self.ax_table
        ax.axis("off")
        ax.set_facecolor("white")
 
        # Pivot: rows = store, cols = year
        pivot = self.df.pivot_table(
            index="store_id",
            columns="sales_year",
            values="yearly_fuel_price",
            aggfunc="sum",
        )
        pivot.index   = [int(float(str(i))) for i in pivot.index]
        pivot.columns = [int(float(str(c))) for c in pivot.columns]
        pivot = pivot.sort_index()
 
        years = sorted(pivot.columns.tolist())
 
        # Row totals
        pivot["Total"] = pivot[years].sum(axis=1)
 
        # Column totals row
        totals_row: dict[str, float] = {y: float(pivot[y].sum()) for y in years}
        totals_row["Total"] = float(pivot["Total"].sum())
        totals_df = pd.DataFrame([totals_row], index=["Total"])
        display = pd.concat([pivot, totals_df])
 
        # Format values
        col_order = years + ["Total"]
        fmt_data: list[list[str]] = []
        for _, row in display.iterrows():
            fmt_data.append([_comma_fmt(float(str(row[c]))) for c in col_order])
 
        row_labels = [str(i) for i in pivot.index] + ["Total"]
        col_labels = ["Store - Copy"] + [str(y) for y in years] + ["Total"]
 
        cell_text = [
            [label] + fmt_row
            for label, fmt_row in zip(row_labels, fmt_data)
        ]
 
        tbl = ax.table(
            cellText  = cell_text,
            colLabels = col_labels,
            cellLoc   = "right",
            loc       = "center",
        )
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(7.5)
        tbl.scale(1, 1.3)
 
        n_cols = len(col_labels)
        n_rows = len(cell_text)
 
        # Header row styling
        for c in range(n_cols):
            cell = tbl[0, c]
            cell.set_facecolor("#AAAAAA")
            cell.set_text_props(color="white", fontweight="bold")
 
        # Alternating rows + highlight Total column
        for r in range(1, n_rows + 1):
            is_total_row = (r == n_rows)
            for c in range(n_cols):
                cell = tbl[r, c]
                is_total_col = (c == n_cols - 1)
 
                if is_total_row:
                    cell.set_facecolor("#2F2F2F")
                    cell.set_text_props(color="white", fontweight="bold")
                elif is_total_col:
                    cell.set_facecolor("#E8E8E8")
                    cell.set_text_props(fontweight="bold")
                else:
                    # Alternating blue highlight (every other row like reference)
                    cell.set_facecolor("#D0E4F7" if r % 2 == 0 else "white")
 
        ax.set_title("Fuel Price by Store and Year",
                     fontsize=9, loc="left", pad=4, color="#333")
 
    # ── donut chart ───────────────────────────────────────────────────────────
 
    def _draw_donut(self):
        ax = self.ax_donut
        ax.clear()
        ax.set_facecolor("white")
 
        year_totals = (
            self.df.groupby("sales_year")["yearly_fuel_price"]
            .sum()
            .sort_index()
        )
 
        years  = [int(float(str(y))) for y in year_totals.index]
        sizes  = [float(str(v)) for v in year_totals.values]
        colors = [YEAR_COLORS.get(y, "#AAAAAA") for y in years]
 
        pie_result = ax.pie(
            sizes,
            colors=colors,
            startangle=90,
            wedgeprops={"width": 0.52, "edgecolor": "white", "linewidth": 1.5},
        )
        wedges = pie_result[0]
 
        # Year labels with leader lines
        total = sum(sizes)
        cumulative = 0.0
        for wedge, year, size in zip(wedges, years, sizes):
            angle = (wedge.theta1 + wedge.theta2) / 2
            mid_rad = np.deg2rad(angle)
            # label position outside the donut
            lx = 1.35 * np.cos(mid_rad)
            ly = 1.35 * np.sin(mid_rad)
            ax.annotate(
                str(year),
                xy=(0.75 * np.cos(mid_rad), 0.75 * np.sin(mid_rad)),
                xytext=(lx, ly),
                arrowprops={"arrowstyle": "-", "color": "#666", "lw": 0.8},
                fontsize=8, color="#333", ha="center", va="center",
            )
            cumulative += size
 
        ax.set_title("Fuel_Price by Year", fontsize=9, loc="left", pad=4, color="#333")
        ax.set_xlim(-1.8, 1.8)
        ax.set_ylim(-1.5, 1.5)
 
    # ── KPI card ──────────────────────────────────────────────────────────────
 
    def _draw_kpi(self):
        ax = self.ax_kpi
        ax.axis("off")
 
        # Card background
        for sp in ax.spines.values():
            sp.set_visible(True)
            sp.set_edgecolor("#DDDDDD")
            sp.set_linewidth(1)
        ax.set_facecolor("#FAFAFA")
 
        total = float(self.df["yearly_fuel_price"].sum())
        ax.text(
            0.5, 0.60,
            _m_fmt(total),
            transform=ax.transAxes,
            ha="center", va="center",
            fontsize=28, fontweight="bold", color="#1A1A1A",
        )
        ax.text(
            0.5, 0.28,
            "Fuel_Price",
            transform=ax.transAxes,
            ha="center", va="center",
            fontsize=11, color="#555",
        )
    # ── show ─────────────────────────────────────────────────────────────────
 
    def show(self):
        filename = f"walmart_fuel_price_year_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(graph_folder_path+filename, dpi=300)
        plt.show()


with conn.cursor() as cur:
    try:
        cur.execute("""
                SELECT
                    YEAR(D.STORE_DATE) AS SALES_YEAR,
                    F.STORE_ID,
                    SUM(F.FUEL_PRICE) AS YEARLY_FUEL_PRICE
                FROM WALLMART_DB.GOLD.WALMART_FACT_TABLE F
                JOIN WALLMART_DB.GOLD.WALMART_DATE_DIM   D
                    ON F.DATE_ID = D.DATE_ID
                WHERE F.VRSN_END_DATE IS NULL
                GROUP BY YEAR(D.STORE_DATE), F.STORE_ID
                ORDER BY SALES_YEAR, F.STORE_ID;
            """)
        
        fuel_prices = cur.fetch_pandas_all()

        YEAR_COLORS = {2010: "#4472C4", 2011: "#5B8FA8", 2012: "#7F9FC0"}   # blue tones
 
        def _comma_fmt(x: float) -> str:
            return f"{x:,.2f}"
        
        
        def _m_fmt(x: float) -> str:
            if x >= 1_000_000:
                return f"{x / 1_000_000:.2f}M"
            if x >= 1_000:
                return f"{x / 1_000:.1f}K"
            return f"{x:.2f}"
 
        dashboard = FuelPriceDashboard(fuel_prices)
        dashboard.show()

    finally:
        cur.close()