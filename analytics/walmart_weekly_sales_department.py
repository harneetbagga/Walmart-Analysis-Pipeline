#!/usr/bin/env python
from ..utilities.snowflake_connector import snowflake_conn
from os import getcwd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.gridspec import GridSpec
from matplotlib.axes import Axes
from matplotlib.patches import Rectangle as MplRectangle
from os import getcwd
from datetime import datetime

#Path to the graphs folder
graph_folder_path = getcwd() + "/Wallmart/graphs/"

conn = snowflake_conn()

class DeptWeeklySalesDashboard:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.df.columns = [c.lower() for c in self.df.columns]
        self.df["department_id"]      = [int(float(str(v))) for v in self.df["department_id"]]
        self.df["weekly_sales"] = [float(str(v)) for v in self.df["weekly_sales"]]
        self._build()
 
    def _build(self) -> None:
        self.fig = plt.figure(figsize=(18, 10), facecolor="white")
        self.fig.suptitle(
            "department wise weekly sales",
            fontsize=20, fontweight="normal", y=0.98,
            color="#1A1A1A", fontfamily="serif"
        )
 
        gs = GridSpec(
            nrows=2, ncols=3,
            figure=self.fig,
            height_ratios=[1, 1.4],
            width_ratios=[1, 1, 1],
            hspace=0.40,
            wspace=0.30,
            left=0.04, right=0.97,
            top=0.92, bottom=0.06,
        )
 
        ax_table   = self.fig.add_subplot(gs[0, 0])
        ax_kpi     = self.fig.add_subplot(gs[0, 1])
        ax_top5    = self.fig.add_subplot(gs[0, 2])
        ax_bar     = self.fig.add_subplot(gs[1, :])
 
        self._draw_dept_table(ax_table)
        self._draw_kpi(ax_kpi)
        self._draw_top5(ax_top5)
        self._draw_bar(ax_bar)
 
    # ── top-left: dept table ──────────────────────────────────────────────────
 
    def _draw_dept_table(self, ax: Axes) -> None:
        ax.axis("off")
 
        # Show first 10 rows (simulate scroll)
        display = self.df[["department_id", "weekly_sales"]].head(10).copy()
        display["weekly_sales"] = [_comma_fmt(v) for v in display["weekly_sales"]]
        display["department_id"]      = [str(v) for v in display["department_id"]]
 
        tbl = ax.table(
            cellText  = display.values.tolist(),
            colLabels = ["Dept - Copy", "Weekly_Sales"],
            cellLoc   = "right",
            loc       = "center",
        )
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(8)
        tbl.scale(1, 1.4)
 
        n_cols = 2
        n_rows = len(display)
 
        # Header
        for c in range(n_cols):
            cell = tbl[0, c]
            cell.set_facecolor("#404040")
            cell.set_text_props(color="white", fontweight="bold")
 
        # Alternating rows
        for r in range(1, n_rows + 1):
            for c in range(n_cols):
                tbl[r, c].set_facecolor("#D0D0D0" if r % 2 == 0 else "white")
 
    # ── top-centre: KPI card ──────────────────────────────────────────────────
 
    def _draw_kpi(self, ax: Axes) -> None:
        ax.axis("off")
        for sp in ax.spines.values():
            sp.set_visible(True)
            sp.set_edgecolor("#CCCCCC")
        ax.set_facecolor("#FAFAFA")
 
        total = float(self.df["weekly_sales"].sum())
        # Format as X.XXXbn
        total_str = f"{total / 1e9:.3f}bn"
 
        ax.text(
            0.5, 0.58, total_str,
            transform=ax.transAxes,
            ha="center", va="center",
            fontsize=30, fontweight="bold", color="#1A1A1A",
        )
        ax.text(
            0.5, 0.32, "Weekly_Sales",
            transform=ax.transAxes,
            ha="center", va="center",
            fontsize=12, color="#555",
        )
 
    # ── top-right: top 5 table ────────────────────────────────────────────────
 
    def _draw_top5(self, ax: Axes) -> None:
        ax.axis("off")
 
        top5 = (
            self.df.nlargest(5, "weekly_sales")[["department_id", "weekly_sales"]]
            .reset_index(drop=True)
        )
 
        cell_text: list[list[str]] = []
        for _, row in top5.iterrows():
            dept  = str(int(float(str(row["department_id"]))))
            sales = _comma_fmt(float(str(row["weekly_sales"])))
            cell_text.append([dept, sales])
 
        tbl = ax.table(
            cellText  = cell_text,
            colLabels = ["Dept", "Weekly_Sales"],
            cellLoc   = "right",
            loc       = "center",
        )
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(8)
        tbl.scale(1, 1.55)
 
        # Header
        for c in range(2):
            cell = tbl[0, c]
            cell.set_facecolor("#404040")
            cell.set_text_props(color="white", fontweight="bold")
 
        # Left blue bar accent per row (mimics Tableau bar indicator)
        for r in range(1, 6):
            tbl[r, 0].set_facecolor("white")
            tbl[r, 1].set_facecolor("white")
 
        ax.set_title("top 5 department wise sales",
                     fontsize=9, loc="left", color="#333", pad=4)
 
    # ── bottom: bar chart per dept ────────────────────────────────────────────
 
    def _draw_bar(self, ax: Axes) -> None:
        df_sorted = self.df.sort_values("department_id")
        dept_ids  = [int(float(str(v))) for v in df_sorted["department_id"]]
        sales     = [float(str(v)) for v in df_sorted["weekly_sales"]]
        colors    = [DEPT_PALETTE[i % len(DEPT_PALETTE)] for i in range(len(dept_ids))]
 
        ax.bar(dept_ids, sales, color=colors, width=0.75, zorder=3)
 
        # Colour-coded legend (dept numbers)
        legend_handles = [
            MplRectangle((0, 0), 1, 1, color=DEPT_PALETTE[i % len(DEPT_PALETTE)])
            for i in range(len(dept_ids))
        ]
        ax.legend(
            legend_handles,
            [str(d) for d in dept_ids],
            loc="upper right",
            fontsize=5,
            ncol=min(len(dept_ids), 40),
            frameon=True,
            framealpha=0.9,
            title="Dept - Copy",
            title_fontsize=7,
            handlelength=0.7,
            handleheight=0.7,
            columnspacing=0.3,
            borderpad=0.3,
        )
 
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(_bn_fmt))
        ax.set_xlim(0, max(dept_ids) + 2)
        ax.set_facecolor("white")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)
        ax.tick_params(axis="both", labelsize=8)
        ax.set_title(
            "Weekly_Sales by Dept - Copy and Dept - Copy",
            fontsize=9, loc="left", color="#333", pad=4
        )
        ax.axhline(0, color="#999", linewidth=0.8)
 
    # ── show ─────────────────────────────────────────────────────────────────
 
    def show(self):
        filename = f"walmart_weekly_sales_department_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(graph_folder_path+filename, dpi=300)
        plt.show()


with conn.cursor() as cur:
    try:
        cur.execute("""
                SELECT
                    DEPARTMENT_ID,
                    SUM(STORE_WEEKLY_SALES) AS WEEKLY_SALES
                FROM WALLMART_DB.GOLD.WALMART_FACT_TABLE F
                WHERE F.VRSN_END_DATE IS NULL
                GROUP BY DEPARTMENT_ID
                ORDER BY DEPARTMENT_ID;
            """)
        
        dept_weekly_sales = cur.fetch_pandas_all()

        # Distinct colour palette for each department bar (Tableau-style)
        DEPT_PALETTE = [
            "#4e79a7","#f28e2b","#e15759","#76b7b2","#59a14f","#edc948","#b07aa1",
            "#ff9da7","#9c755f","#bab0ac","#499894","#86bcb6","#d37295","#fabfd2",
            "#b6992d","#f1ce63","#a0cbe8","#ffbe7d","#8cd17d","#d4a6c8","#79706e",
            "#4e79a7","#f28e2b","#e15759","#76b7b2","#59a14f","#edc948","#b07aa1",
            "#ff9da7","#9c755f","#bab0ac","#499894","#86bcb6","#d37295","#fabfd2",
            "#b6992d","#f1ce63","#a0cbe8","#ffbe7d","#8cd17d","#d4a6c8","#79706e",
            "#4e79a7","#f28e2b","#e15759","#76b7b2","#59a14f","#edc948","#b07aa1",
            "#ff9da7","#9c755f","#bab0ac","#499894","#86bcb6","#d37295","#fabfd2",
            "#b6992d","#f1ce63","#a0cbe8","#ffbe7d","#8cd17d","#d4a6c8","#79706e",
            "#4e79a7","#f28e2b","#e15759","#76b7b2","#59a14f","#edc948","#b07aa1",
            "#ff9da7","#9c755f","#bab0ac","#499894","#86bcb6","#d37295","#fabfd2",
            "#b6992d","#f1ce63","#a0cbe8","#ffbe7d","#8cd17d","#d4a6c8","#79706e",
            "#4e79a7","#f28e2b","#e15759","#76b7b2","#59a14f","#edc948","#b07aa1",
            "#ff9da7","#9c755f","#bab0ac","#499894","#86bcb6","#d37295","#fabfd2",
            "#b6992d",
        ]

        def _bn_fmt(x: float, _: object = None) -> str:
            if abs(x) >= 1e9:
                return f"{x / 1e9:.2f}bn"
            if abs(x) >= 1e6:
                return f"{x / 1e6:.1f}M"
            return f"{x:,.0f}"
        
        def _comma_fmt(x: float) -> str:
            return f"{x:,.2f}"
 
        dashboard = DeptWeeklySalesDashboard(dept_weekly_sales)
        dashboard.show()

    finally:
        cur.close()