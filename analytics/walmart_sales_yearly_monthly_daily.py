"""
walmart_weekly_sales_year_month_day.py
=======================================
Renders a 3-panel Matplotlib dashboard:
  - Top-left    : Bar chart  – Weekly Sales by Year
  - Top-right   : Bar chart  – Weekly Sales by Month
  - Bottom      : Bar chart  – Weekly Sales by Day-of-Month

Usage:
    python walmart_weekly_sales_year_month_day.py
"""
 
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.gridspec import GridSpec
from matplotlib.axes import Axes
from ..utilities.snowflake_connector import snowflake_conn
from os import getcwd
from datetime import datetime

#Path to the graphs folder
graph_folder_path = getcwd() + "/Wallmart/graphs/"

conn = snowflake_conn()

 
QUERY_YEAR = """
SELECT
    YEAR(D.STORE_DATE) AS SALES_YEAR,
    SUM(F.STORE_WEEKLY_SALES) AS YEARLY_SALES
FROM WALMART_FACT_TABLE F
JOIN WALMART_DATE_DIM D ON F.DATE_ID = D.DATE_ID
WHERE F.VRSN_END_DATE IS NULL
GROUP BY YEAR(D.STORE_DATE)
ORDER BY SALES_YEAR;
"""
 
QUERY_MONTH = """
SELECT
    MONTH(D.STORE_DATE) AS MONTH_NUM,
    MONTHNAME(D.STORE_DATE) AS SALES_MONTH,
    SUM(F.STORE_WEEKLY_SALES) AS MONTHLY_SALES
FROM WALMART_FACT_TABLE F
JOIN WALMART_DATE_DIM D ON F.DATE_ID = D.DATE_ID
WHERE F.VRSN_END_DATE IS NULL
GROUP BY MONTH(D.STORE_DATE), MONTHNAME(D.STORE_DATE)
ORDER BY MONTH_NUM;
"""
 
QUERY_DAY = """
SELECT
    DAY(D.STORE_DATE) AS SALES_DAY,
    SUM(F.STORE_WEEKLY_SALES) AS DAILY_SALES
FROM WALMART_FACT_TABLE F
JOIN WALMART_DATE_DIM D ON F.DATE_ID = D.DATE_ID
WHERE F.VRSN_END_DATE IS NULL
GROUP BY DAY(D.STORE_DATE)
ORDER BY SALES_DAY;
"""
 
# ─────────────────────────────────────────────────────────────────────────────
# 1. DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────
 
def _normalise(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.lower() for c in df.columns]
    return df
 
 
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    try:
        cursor = conn.cursor()

        cursor.execute(QUERY_YEAR)
        df_year  = _normalise(pd.DataFrame(cursor.fetchall(), columns=[d[0] for d in cursor.description]))

        cursor.execute(QUERY_MONTH)
        df_month = _normalise(pd.DataFrame(cursor.fetchall(), columns=[d[0] for d in cursor.description]))

        cursor.execute(QUERY_DAY)
        df_day   = _normalise(pd.DataFrame(cursor.fetchall(), columns=[d[0] for d in cursor.description]))

        cursor.close()
        conn.close()
        return df_year, df_month, df_day
    except ImportError:
        print("[WARN] snowflake-connector-python not installed – using synthetic data.")
        return _synthetic_data()
 
 
def _synthetic_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Synthetic data approximating the reference image values."""
    # Year totals: 2010→2.05bn, 2011→2.19bn, 2012→1.81bn
    df_year = pd.DataFrame({
        "sales_year":   [2010, 2011, 2012],
        "yearly_sales": [2_050_000_000.0, 2_190_000_000.0, 1_810_000_000.0],
    })
 
    # Monthly totals (Jan–Dec) matching reference image
    monthly_vals = [
        300_000_000, 500_000_000, 540_000_000, 590_000_000,
        510_000_000, 570_000_000, 600_000_000, 560_000_000,
        530_000_000, 530_000_000, 350_000_000, 480_000_000,
    ]
    month_names = [
        "January","February","March","April","May","June",
        "July","August","September","October","November","December"
    ]
    df_month = pd.DataFrame({
        "month_num":     list(range(1, 13)),
        "sales_month":   month_names,
        "monthly_sales": [float(v) for v in monthly_vals],
    })
 
    # Daily totals: day-of-month 1–31
    rng = np.random.default_rng(42)
    daily_vals = rng.uniform(80_000_000, 225_000_000, 31)
    daily_vals[30] = 82_000_000   # day 31 is sparse — few months have it
    df_day = pd.DataFrame({
        "sales_day":   list(range(1, 32)),
        "daily_sales": [float(v) for v in daily_vals],
    })
 
    return df_year, df_month, df_day
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 2. HELPERS
# ─────────────────────────────────────────────────────────────────────────────
 
BAR_COLOR     = "#1BA1E2"   # Walmart-style blue
HIGHLIGHT_CLR = "#0078D7"   # slightly darker for highlighted bars (Jul, Aug in ref)
 
HIGHLIGHT_MONTHS = {"July", "August"}   # darker bars in the reference image
 
 
def _bn_fmt(x: float, _: object = None) -> str:
    return f"{x / 1e9:.2f}bn"
 
 
def _m_fmt(x: float, _: object = None) -> str:
    return f"{x / 1e6:.0f}M"
 
 
def _bar_label(ax: Axes, bars: list, fmt_fn: object, inside: bool = False) -> None:
    """Add value labels above (or inside top of) each bar."""
    for bar in bars:
        h = float(bar.get_height())
        if h <= 0:
            continue
        label = fmt_fn(h)  # type: ignore[operator]
        if inside:
            y = h * 0.92
            va = "top"
            color = "white"
        else:
            y = h * 1.01
            va = "bottom"
            color = "#222"
        ax.text(
            float(bar.get_x()) + float(bar.get_width()) / 2,
            y, label,
            ha="center", va=va,
            fontsize=7.5, color=color, fontweight="bold"
        )
 
 
def _style_ax(ax: Axes) -> None:
    ax.set_facecolor("white")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)
    ax.tick_params(axis="both", labelsize=8)
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 3. DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
 
class SalesYearMonthDayDashboard:
    def __init__(
        self,
        df_year:  pd.DataFrame,
        df_month: pd.DataFrame,
        df_day:   pd.DataFrame,
    ):
        self.df_year  = _normalise(df_year.copy())
        self.df_month = _normalise(df_month.copy())
        self.df_day   = _normalise(df_day.copy())
        self._build()
 
    def _build(self) -> None:
        self.fig = plt.figure(figsize=(18, 10), facecolor="white")
        self.fig.suptitle(
            "weekly sales by year, month and date",
            fontsize=20, fontweight="normal", y=0.97,
            color="#1A1A1A", fontfamily="serif"
        )
 
        gs = GridSpec(
            nrows=2, ncols=2,
            figure=self.fig,
            height_ratios=[1, 1],
            width_ratios=[1, 2],
            hspace=0.45,
            wspace=0.25,
            left=0.06, right=0.97,
            top=0.91, bottom=0.08,
        )
 
        ax_year  = self.fig.add_subplot(gs[0, 0])
        ax_month = self.fig.add_subplot(gs[0, 1])
        ax_day   = self.fig.add_subplot(gs[1, :])   # full-width bottom
 
        self._draw_year(ax_year)
        self._draw_month(ax_month)
        self._draw_day(ax_day)
 
    # ── top-left: by year ─────────────────────────────────────────────────────
 
    def _draw_year(self, ax: Axes) -> None:
        df = self.df_year.sort_values("sales_year")
        x  = [str(int(float(str(v)))) for v in df["sales_year"]]
        y  = [float(str(v)) for v in df["yearly_sales"]]
 
        bars = ax.bar(x, y, color=BAR_COLOR, width=0.5, zorder=3)
        _bar_label(ax, list(bars), _bn_fmt, inside=False)
 
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(_bn_fmt))
        ax.set_title("Weekly_Sales by Year", fontsize=9, loc="left", color="#333", pad=4)
        _style_ax(ax)
 
    # ── top-right: by month ───────────────────────────────────────────────────
 
    def _draw_month(self, ax: Axes) -> None:
        df = self.df_month.sort_values("month_num")
        labels = [str(v) for v in df["sales_month"]]
        y      = [float(str(v)) for v in df["monthly_sales"]]
        colors = [
            HIGHLIGHT_CLR if lbl in HIGHLIGHT_MONTHS else BAR_COLOR
            for lbl in labels
        ]
 
        x_pos = list(range(len(labels)))
        bars  = ax.bar(x_pos, y, color=colors, width=0.6, zorder=3)
 
        # Labels inside bars (white) for highlighted, above for normal
        for bar, lbl, val in zip(bars, labels, y):
            inside = lbl in HIGHLIGHT_MONTHS
            color  = "white" if inside else "#222"
            ypos   = float(bar.get_height()) * (0.92 if inside else 1.01)
            va     = "top" if inside else "bottom"
            ax.text(
                float(bar.get_x()) + float(bar.get_width()) / 2,
                ypos, _bn_fmt(val),
                ha="center", va=va,
                fontsize=7, color=color, fontweight="bold"
            )
 
        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=7.5)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(_bn_fmt))
        ax.set_title("Weekly_Sales by Month", fontsize=9, loc="left", color="#333", pad=4)
        _style_ax(ax)
 
    # ── bottom: by day-of-month ───────────────────────────────────────────────
 
    def _draw_day(self, ax: Axes) -> None:
        df = self.df_day.sort_values("sales_day")
        x  = [int(float(str(v))) for v in df["sales_day"]]
        y  = [float(str(v)) for v in df["daily_sales"]]
 
        bars = ax.bar(x, y, color=BAR_COLOR, width=0.7, zorder=3)
        _bar_label(ax, list(bars), _m_fmt, inside=False)
 
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(_m_fmt))
        ax.set_xlabel("")
        ax.set_xlim(0, 35)
        ax.set_title("Weekly_Sales by Day", fontsize=9, loc="left", color="#333", pad=4)
        _style_ax(ax)
 
    def show(self) -> None:
        filename = f"walmart_sales_yearly_monthly_daily_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(graph_folder_path + filename, dpi=300)
        print(f"Dashboard saved to {graph_folder_path + filename}")
        plt.show()  # Commented out for headless execution
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 4. ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
 
if __name__ == "__main__":
    print("Loading data …")
    df_year, df_month, df_day = load_data()
    print(
        f"Year rows: {len(df_year)}  |  "
        f"Month rows: {len(df_month)}  |  "
        f"Day rows: {len(df_day)}"
    )
    dashboard = SalesYearMonthDayDashboard(df_year, df_month, df_day)
    dashboard.show()