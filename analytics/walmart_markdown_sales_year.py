#!/usr/bin/env python
from ..utilities.snowflake_connector import snowflake_conn
from os import getcwd
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.widgets import Button
from matplotlib.gridspec import GridSpec

#Path to the graphs folder
graph_folder_path = getcwd() + "/Wallmart/graphs/"

conn = snowflake_conn()

class MarkdownDashboard:
    """
    Interactive Matplotlib dashboard:
      Left  – filtered data table  (store-level breakdown for selected year)
      Right – grouped bar chart    (MarkDown1-5 totals per year)
      Bottom-left – year filter buttons
    """
 
    def __init__(self, df: pd.DataFrame):
        self.df_all = df.copy()
        self.selected_year = "All"
        self._build_layout()
 
    # ── layout ──────────────────────────────────────────────────────────────
 
    def _build_layout(self):
        self.fig = plt.figure(figsize=(16, 8), facecolor="#F5F5F5")
 
        # Main title
        self.fig.suptitle(
            "Walmart - Markdown sales by year and store",
            fontsize=18, fontweight="bold", y=0.97, color="#1A1A1A"
        )
 
        gs = GridSpec(
            nrows=2, ncols=2,
            figure=self.fig,
            height_ratios=[4, 1],
            width_ratios=[1, 1.4],
            hspace=0.35,
            wspace=0.3,
            left=0.05, right=0.97,
            top=0.91, bottom=0.06,
        )
 
        self.ax_table  = self.fig.add_subplot(gs[0, 0])   # top-left:  data table
        self.ax_bar    = self.fig.add_subplot(gs[0, 1])   # top-right: bar chart
        self.ax_filter = self.fig.add_subplot(gs[1, 0])   # bottom-left: buttons
 
        # Filter panel styling
        self.ax_filter.set_facecolor("#E8E8E8")
        for spine in self.ax_filter.spines.values():
            spine.set_edgecolor("#CCCCCC")
        self.ax_filter.tick_params(left=False, bottom=False,
                                   labelleft=False, labelbottom=False)
        self.ax_filter.set_title("select year for markdown sales",
                                 fontsize=9, loc="left", pad=6, color="#555")
        self.ax_filter.text(0.01, 0.72, "Year", transform=self.ax_filter.transAxes,
                            fontsize=8, color="#333")
 
        self._add_filter_buttons()
        self._refresh_plot()
 
    # ── filter buttons ───────────────────────────────────────────────────────
 
    def _add_filter_buttons(self):
        available_years = sorted(self.df_all["SALES_YEAR"].unique())
        button_labels   = ["Select All"] + [str(y) for y in available_years]
        n = len(button_labels)
        gap = 0.04
        btn_w = (1 - gap * (n + 1)) / n
 
        self._buttons = []
        for i, lbl in enumerate(button_labels):
            ax_btn = self.ax_filter.inset_axes(
                (gap + i * (btn_w + gap), 0.15, btn_w, 0.65)
            )
            btn = Button(
                ax_btn, lbl,
                color="#DCDCDC", hovercolor="#B0B8CC"
            )
            btn.label.set_fontsize(9)
            btn.on_clicked(lambda _, y=lbl: self._on_year_select(y))
            self._buttons.append(btn)
 
    def _on_year_select(self, year_label: str):
        self.selected_year = year_label
        self._refresh_plot()
        self.fig.canvas.draw_idle()
 
    # ── main draw ────────────────────────────────────────────────────────────
 
    def _refresh_plot(self):
        # ── filter dataframe ──────────────────────────────────────────────
        if self.selected_year == "Select All" or self.selected_year == "All":
            df_filtered = self.df_all.copy()
            table_year  = "All Years"
        else:
            yr = int(self.selected_year)
            df_filtered = self.df_all[self.df_all["SALES_YEAR"] == yr].copy()
            table_year  = str(yr)
 
        self._draw_table(df_filtered, table_year)
        self._draw_bar_chart()
 
    # ── left: data table ─────────────────────────────────────────────────────
 
    def _draw_table(self, df: pd.DataFrame, year_label: str):
        ax = self.ax_table
        ax.clear()
        ax.axis("off")
 
        # Aggregate by store for the selected year
        agg = (
            df.groupby("STORE_ID")[MARKDOWN_COLS]
            .sum()
            .reset_index()
        )
        agg.columns = ["Store"] + MARKDOWN_LABELS
 
        # Totals row
        totals = pd.DataFrame(
            [["Total"] + [agg[c].sum() for c in MARKDOWN_LABELS]],
            columns=agg.columns,
        )
 
        # Format for display
        display = pd.concat([agg, totals], ignore_index=True)
        display_fmt = display.copy()
        for col in MARKDOWN_LABELS:
            display_fmt[col] = display_fmt[col].apply(_table_fmt)
 
        # Title row
        ax.set_title(
            f"markdown sales by year and store\nYear:  {year_label}",
            fontsize=8, loc="left", color="#333", pad=4
        )
 
        tbl = ax.table(
            cellText  = display_fmt.values.tolist(),
            colLabels = display_fmt.columns.tolist(),
            cellLoc   = "right",
            loc       = "center",
        )
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(7)
        tbl.scale(1, 1.25)
 
        # Header styling
        for col_idx in range(len(display_fmt.columns)):
            cell = tbl[0, col_idx]
            cell.set_facecolor("#595959")
            cell.set_text_props(color="white", fontweight="bold")
 
        # Totals row styling
        total_row = len(display_fmt)
        for col_idx in range(len(display_fmt.columns)):
            cell = tbl[total_row, col_idx]
            cell.set_facecolor("#2F2F2F")
            cell.set_text_props(color="white", fontweight="bold")
 
        # Alternating row colours
        for row_idx in range(1, len(display)):
            fc = "#F9F9F9" if row_idx % 2 == 0 else "white"
            for col_idx in range(len(display_fmt.columns)):
                tbl[row_idx, col_idx].set_facecolor(fc)
 
    # ── right: grouped bar chart ──────────────────────────────────────────────
 
    def _draw_bar_chart(self):
        ax = self.ax_bar
        ax.clear()
 
        years = sorted(self.df_all["SALES_YEAR"].unique())
        yearly = (
            self.df_all.groupby("SALES_YEAR")[MARKDOWN_COLS]
            .sum()
        )
 
        n_groups = len(years)
        n_bars   = len(MARKDOWN_COLS)
        bar_w    = 0.14
        x_base   = range(n_groups)
 
        yearly_reset = yearly.reset_index()
        yearly_dict: dict[int, dict[str, float]] = {
            int(float(str(row["SALES_YEAR"]))): {col: float(str(row[col])) for col in MARKDOWN_COLS}
            for _, row in yearly_reset.iterrows()
        }

        for i, (col, lbl, color) in enumerate(zip(MARKDOWN_COLS, MARKDOWN_LABELS, BAR_COLORS)):
            offsets = [x + (i - n_bars / 2 + 0.5) * bar_w for x in x_base]
            vals = np.array(
                [yearly_dict[int(yr)][col] if int(yr) in yearly_dict else 0.0 for yr in years],
                dtype=np.float64
            )
            bars = ax.bar(offsets, vals, width=bar_w, color=color, label=lbl, zorder=3)
 
            # Value labels on top of each bar
            for bar, val in zip(bars, vals):
                fval = float(val)
                if fval > 0:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() * 1.01,
                        _bn_fmt(val),
                        ha="center", va="bottom",
                        fontsize=6, color="#222"
                    )
 
        # Axes decoration
        ax.set_xticks(list(x_base))
        ax.set_xticklabels([str(y) for y in years], fontsize=9)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(_bn_fmt))
        ax.set_title(
            "MarkDown1, MarkDown2, MarkDown3, MarkDown4 and MarkDown5 by Year",
            fontsize=8, loc="left", color="#333", pad=4
        )
        ax.set_ylabel("")
        ax.set_facecolor("white")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
        ax.legend(
            loc="upper left",
            fontsize=7,
            frameon=True,
            framealpha=0.9,
            ncol=len(MARKDOWN_LABELS),
        )
 
    # ── show ─────────────────────────────────────────────────────────────────
 
    def show(self):
        filename = f"walmart_markdown_sales_year_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(graph_folder_path+filename, dpi=300)
        plt.show()


with conn.cursor() as cur:
    try:
        cur.execute("""
                SELECT 
                    YEAR(D.STORE_DATE) AS SALES_YEAR,
                    F.STORE_ID,
                    SUM(F.MARKDOWN1) AS MARKDOWN1_SALES,
                    SUM(F.MARKDOWN2) AS MARKDOWN2_SALES,
                    SUM(F.MARKDOWN3) AS MARKDOWN3_SALES,
                    SUM(F.MARKDOWN4) AS MARKDOWN4_SALES,
                    SUM(F.MARKDOWN5) AS MARKDOWN5_SALES,
                    SUM(COALESCE(F.MARKDOWN1,0) + COALESCE(F.MARKDOWN2,0) + COALESCE(F.MARKDOWN3,0)
                    + COALESCE(F.MARKDOWN4,0) + COALESCE(F.MARKDOWN5,0))  AS TOTAL_MARKDOWN_ALL
                FROM WALLMART_DB.GOLD.WALMART_FACT_TABLE F
                JOIN WALLMART_DB.GOLD.WALMART_STORE_DIM S
                    ON F.STORE_ID = S.STORE_ID 
                AND F.DEPARTMENT_ID = S.DEPARTMENT_ID
                JOIN WALLMART_DB.GOLD.WALMART_DATE_DIM D
                    ON F.DATE_ID = D.DATE_ID
                WHERE F.VRSN_END_DATE IS NULL
                GROUP BY YEAR(D.STORE_DATE), F.STORE_ID
                ORDER BY YEAR(D.STORE_DATE), F.STORE_ID;
            """)
        
        markdown_sales = cur.fetch_pandas_all()

        MARKDOWN_COLS = ["MARKDOWN1_SALES", "MARKDOWN2_SALES", "MARKDOWN3_SALES", "MARKDOWN4_SALES", "MARKDOWN5_SALES"]
        MARKDOWN_LABELS = ["MarkDown1", "MarkDown2", "MarkDown3", "MarkDown4", "MarkDown5"]
 
        # Colours matching the reference image bar chart
        BAR_COLORS = ["#4472C4", "#404040", "#FF0000", "#7D3C27", "#595959"]
 
        def _bn_fmt(x: float, _=None) -> str:
            """Format axis tick labels as '0.00bn'."""
            return f"{x / 1e9:.2f}bn"
        
        
        def _table_fmt(val) -> str:
            """Format table cell numbers with commas."""
            if pd.isna(val):
                return "N/A"
            return f"{val:,.2f}"
 
        dashboard = MarkdownDashboard(markdown_sales)
        dashboard.show()

    finally:
        cur.close()