#!/usr/bin/env python
from ..utilities.snowflake_connector import snowflake_conn
from os import getcwd
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.widgets import Button
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Rectangle as MplRectangle

#Path to the graphs folder
graph_folder_path = getcwd() + "/Wallmart/graphs/"

conn = snowflake_conn()

class WeeklySalesDashboard:
    def __init__(self, df: pd.DataFrame):
        self.df_all = df.copy()
        self.df_all["STORE_TYPE"] = self.df_all["STORE_TYPE"].str.strip().str.upper()
        self.selected_type = "All"
        self._build_layout()
 
    # ── layout ───────────────────────────────────────────────────────────────
 
    def _build_layout(self):
        self.fig = plt.figure(figsize=(18, 9), facecolor="white")
        self.fig.suptitle(
            "weekly sales by store type",
            fontsize=20, fontweight="normal", y=0.97, color="#1A1A1A",
            fontfamily="serif"
        )
 
        gs = GridSpec(
            nrows=2, ncols=2,
            figure=self.fig,
            height_ratios=[1, 2.5],
            width_ratios=[1, 1.8],
            hspace=0.25,
            wspace=0.25,
            left=0.04, right=0.97,
            top=0.91, bottom=0.05,
        )
 
        self.ax_filter = self.fig.add_subplot(gs[0, 0])   # top-left:    buttons
        self.ax_pie    = self.fig.add_subplot(gs[1, 0])   # bottom-left: pie
        self.ax_bar    = self.fig.add_subplot(gs[:, 1])   # right (full height): hbar
 
        # Filter panel
        self.ax_filter.set_facecolor("#F0F0F0")
        for sp in self.ax_filter.spines.values():
            sp.set_edgecolor("#CCCCCC")
        self.ax_filter.tick_params(left=False, bottom=False,
                                   labelleft=False, labelbottom=False)
        self.ax_filter.set_title("select store type", fontsize=9,
                                  loc="left", pad=5, color="#555")
        self.ax_filter.text(0.01, 0.72, "Type",
                            transform=self.ax_filter.transAxes,
                            fontsize=8, color="#333")
 
        self._add_filter_buttons()
        self._refresh_plot()
 
    # ── filter buttons ───────────────────────────────────────────────────────
 
    def _add_filter_buttons(self):
        labels = ["Select All", "A", "B", "C"]
        n   = len(labels)
        gap = 0.04
        btn_w = (1 - gap * (n + 1)) / n
 
        self._buttons: list[Button] = []
        for i, lbl in enumerate(labels):
            ax_btn = self.ax_filter.inset_axes(
                (gap + i * (btn_w + gap), 0.15, btn_w, 0.60)
            )
            btn = Button(ax_btn, lbl, color="#DCDCDC", hovercolor="#B0B8CC")
            btn.label.set_fontsize(9)
            btn.on_clicked(lambda _, y=lbl: self._on_type_select(y))
            self._buttons.append(btn)
 
    def _on_type_select(self, label: str):
        self.selected_type = label
        self._refresh_plot()
        self.fig.canvas.draw_idle()
 
    # ── refresh ───────────────────────────────────────────────────────────────
 
    def _refresh_plot(self):
        if self.selected_type in ("Select All", "All"):
            df = self.df_all.copy()
        else:
            df = self.df_all[self.df_all["STORE_TYPE"] == self.selected_type].copy()
 
        self._draw_pie(df)
        self._draw_hbar(df)
 
    # ── pie chart ─────────────────────────────────────────────────────────────
 
    def _draw_pie(self, df: pd.DataFrame):
        ax = self.ax_pie
        ax.clear()
        ax.set_facecolor("white")
        for sp in ax.spines.values():
            sp.set_edgecolor("#DDDDDD")
 
        type_totals = (
            df.groupby("STORE_TYPE")["WEEKLY_SALES"]
            .sum()
            .sort_index()
        )
 
        if type_totals.empty:
            ax.text(0.5, 0.5, "No data", ha="center", va="center",
                    transform=ax.transAxes, fontsize=10)
            return
 
        labels  = type_totals.index.tolist()
        sizes   = [float(v) for v in type_totals.values]
        colors  = [TYPE_COLORS.get(str(lbl), "#AAAAAA") for lbl in labels]
        explode = [0.04] * len(labels)
 
        pie_result = ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            explode=explode,
            startangle=140,
            wedgeprops={"linewidth": 0.8, "edgecolor": "white"},
        )
        wedges = pie_result[0]
        texts  = pie_result[1]

        for t in texts:
            t.set_fontsize(9)
 
        # Legend
        ax.legend(
            wedges, [f"Type  {l}" for l in labels],
            loc="upper left", fontsize=8, frameon=False,
            title="Type", title_fontsize=8,
        )
        ax.set_title("Weekly_Sales by store Type", fontsize=9,
                     loc="left", pad=4, color="#333")
 
    # ── horizontal bar chart ──────────────────────────────────────────────────
 
    def _draw_hbar(self, df: pd.DataFrame):
        ax = self.ax_bar
        ax.clear()
        ax.set_facecolor("white")
 
        if df.empty:
            ax.text(0.5, 0.5, "No data", ha="center", va="center",
                    transform=ax.transAxes, fontsize=12)
            return
 
        types = sorted(df["STORE_TYPE"].unique())
 
        # Build rows: one bar per (type, store), grouped by type
        bar_labels:  list[str]   = []
        bar_values:  list[float] = []
        bar_colors:  list[str]   = []
        group_ticks: dict[str, list[int]] = {}   # type → y positions
 
        y = 0
        group_mid: dict[str, float] = {}
        type_sep = 1.5   # gap between type groups
 
        for store_type in types:
            sub = (
                df[df["STORE_TYPE"] == store_type]
                .sort_values("STORE_ID")
                .reset_index(drop=True)
            )
            start_y = y
            for idx, row in sub.iterrows():
                store_id = int(float(str(row["STORE_ID"])))
                sales    = float(str(row["WEEKLY_SALES"]))
                color_idx = (store_id - 1) % len(STORE_PALETTE)
                bar_labels.append(f"{store_type}-{store_id}")
                bar_values.append(sales)
                bar_colors.append(STORE_PALETTE[color_idx])
                group_ticks.setdefault(store_type, []).append(y)
                y += 1
            group_mid[store_type] = (start_y + y - 1) / 2
            y += type_sep   # gap before next group
 
        y_pos = list(range(len(bar_values)))
        # Remap y positions respecting gaps
        actual_y: list[float] = []
        cursor = 0.0
        prev_type = ""
        for lbl in bar_labels:
            t = lbl.split("-")[0]
            if prev_type and t != prev_type:
                cursor += type_sep
            actual_y.append(cursor)
            cursor += 1
            prev_type = t
 
        bars = ax.barh(
            actual_y, bar_values,
            height=0.65,
            color=bar_colors,
            edgecolor="none",
            zorder=3,
        )
 
        # Value labels at end of each bar
        for bar, val in zip(bars, bar_values):
            ax.text(
                float(bar.get_width()) + float(ax.get_xlim()[1]) * 0.005,
                float(bar.get_y()) + float(bar.get_height()) / 2,
                _m_fmt(val),
                va="center", ha="left",
                fontsize=6.5, color="#333"
            )
 
        # Type group labels on y-axis
        ax.set_yticks([])
        type_positions: dict[str, float] = {}
        cursor = 0.0
        prev_t = ""
        type_counts = df.groupby("STORE_TYPE")["STORE_ID"].count().to_dict()
        for t in types:
            count = int(str(type_counts.get(t, 0)))
            mid = cursor + (count - 1) / 2
            type_positions[t] = mid
            cursor += count + type_sep
 
        for t, mid in type_positions.items():
            ax.text(
                -ax.get_xlim()[1] * 0.015, mid, t,
                va="center", ha="right",
                fontsize=10, fontweight="bold", color="#333"
            )
 
        # X-axis formatting
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(_m_fmt))
        ax.set_xlabel("")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.grid(axis="x", linestyle="--", alpha=0.4, zorder=0)
        ax.set_xlim(left=0)
        ax.invert_yaxis()
 
        # Title + legend for individual stores
        all_stores = sorted(df["STORE_ID"].unique())
        legend_handles = [
            MplRectangle(
                (0, 0), 1, 1,
                color=STORE_PALETTE[(int(float(str(s))) - 1) % len(STORE_PALETTE)]
            )
            for s in all_stores
        ]
        ax.set_title(
            "Weekly_Sales by Type and Store - Copy",
            fontsize=9, loc="left", pad=4, color="#333"
        )
        ax.legend(
            legend_handles,
            [str(int(float(str(s)))) for s in all_stores],
            loc="upper right",
            fontsize=6,
            ncol=min(len(all_stores), 12),
            frameon=True,
            framealpha=0.9,
            title="Store - Copy",
            title_fontsize=7,
            handlelength=0.8,
            handleheight=0.8,
            columnspacing=0.5,
            borderpad=0.4,
        )
    # ── show ─────────────────────────────────────────────────────────────────
 
    def show(self):
        filename = f"walmart_weekly_sales_store_type_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(graph_folder_path+filename, dpi=300)
        plt.show()

with conn.cursor() as cur:
    try:
        cur.execute("""
                SELECT 
                S.STORE_TYPE,
                S.STORE_ID,
                SUM(F.STORE_WEEKLY_SALES) AS WEEKLY_SALES
            FROM WALLMART_DB.GOLD.WALMART_FACT_TABLE F
            JOIN WALLMART_DB.GOLD.WALMART_STORE_DIM S
                ON F.STORE_ID = S.STORE_ID 
            AND F.DEPARTMENT_ID = S.DEPARTMENT_ID
            WHERE F.VRSN_END_DATE IS NULL
            GROUP BY S.STORE_TYPE, S.STORE_ID
            ORDER BY S.STORE_TYPE, S.STORE_ID;
            """)
        
        weekly_sales = cur.fetch_pandas_all()

        # Colours per store type matching reference image
        TYPE_COLORS = {"A": "#7293CB", "B": "#404040", "C": "#E15759"}
        
        # Many distinct colours for individual store bars (like Tableau's palette)
        STORE_PALETTE = [
            "#4e79a7","#f28e2b","#e15759","#76b7b2","#59a14f",
            "#edc948","#b07aa1","#ff9da7","#9c755f","#bab0ac",
            "#499894","#86bcb6","#d37295","#fabfd2","#b6992d",
            "#f1ce63","#a0cbe8","#ffbe7d","#8cd17d","#b6992d",
            "#79706e","#d4a6c8",
        ]
        
        def _m_fmt(x: float, _=None) -> str:
            """Format as '123M'."""
            return f"{x / 1e6:.0f}M"

 
        dashboard = WeeklySalesDashboard(weekly_sales)
        dashboard.show()

    finally:
        cur.close()