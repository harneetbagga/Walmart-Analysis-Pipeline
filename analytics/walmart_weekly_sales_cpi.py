#!/usr/bin/env python
from ..utilities.snowflake_connector import snowflake_conn
from os import getcwd
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.gridspec import GridSpec
from matplotlib.axes import Axes
from os import getcwd
from datetime import datetime

#Path to the graphs folder
graph_folder_path = getcwd() + "/Wallmart/graphs/"

conn = snowflake_conn()

class WeeklySalesCPIDashboard:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.df.columns = [c.lower() for c in self.df.columns]
        self._build()
 
    def _build(self) -> None:
        fig, ax = plt.subplots(figsize=(16, 8), facecolor="white")
        self.fig = fig
        self.ax  = ax
 
        fig.suptitle(
            "weekly sales by CPI",
            fontsize=20, fontweight="normal", y=0.97,
            color="#1A1A1A", fontfamily="serif"
        )
 
        self._draw_chart(ax)
 
    def _draw_chart(self, ax: Axes) -> None:
        cpi   = np.array([float(str(v)) for v in self.df["cpi"]])
        sales = np.array([float(str(v)) for v in self.df["store_weekly_sales"]])
 
        # ── scatter dots (main visual) ────────────────────────────────────────
        ax.scatter(
            cpi, sales,
            color="#1BA1E2",
            s=4,
            alpha=0.55,
            linewidths=0,
            zorder=3,
        )
 
        # ── dotted trend line (rolling median binned by CPI) ─────────────────
        bin_edges = np.linspace(cpi.min(), cpi.max(), 120)
        bin_idx   = np.digitize(cpi, bin_edges)
        bin_cpi:   list[float] = []
        bin_med:   list[float] = []
        for b in range(1, len(bin_edges)):
            mask = bin_idx == b
            if mask.sum() >= 3:
                bin_cpi.append(float(bin_edges[b]))
                bin_med.append(float(np.median(sales[mask])))
 
        ax.plot(
            bin_cpi, bin_med,
            color="#1BA1E2",
            linewidth=1.0,
            linestyle="dotted",
            zorder=2,
            alpha=0.8,
        )
 
        # ── peak annotations ──────────────────────────────────────────────────
        _annotate_peaks(ax, cpi, sales)
 
        # ── axes styling ──────────────────────────────────────────────────────
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(_m_fmt))
        ax.set_xlim(cpi.min() - 2, cpi.max() + 2)
        ax.set_ylim(0, sales.max() * 1.12)
        ax.set_facecolor("white")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="y", linestyle="-", alpha=0.25, zorder=0)
        ax.tick_params(axis="both", labelsize=9)
        ax.set_title(
            "Weekly_Sales by CPI",
            fontsize=9, loc="left", color="#333", pad=6
        )
 
        plt.tight_layout(rect=(0, 0, 1, 0.95))
 
    # ── show ─────────────────────────────────────────────────────────────────
 
    def show(self):
        filename = f"walmart_weekly_sales_cpi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(graph_folder_path+filename, dpi=300)
        plt.show()


with conn.cursor() as cur:
    try:
        cur.execute("""
                SELECT
                    F.CPI,
                    F.STORE_WEEKLY_SALES
                FROM WALMART_FACT_TABLE F
                WHERE F.VRSN_END_DATE IS NULL
                AND F.CPI IS NOT NULL
                AND F.STORE_WEEKLY_SALES IS NOT NULL
                ORDER BY F.CPI;
            """)
        
        cpi_weekly_sales = cur.fetch_pandas_all()

        def _m_fmt(x: float, _: object = None) -> str:
            return f"{x / 1e6:.0f}M"
 
 
        def _annotate_peaks(ax: Axes, cpi: np.ndarray, sales: np.ndarray) -> None:
            """
            Annotate the highest-sales points in each CPI band,
            matching the reference image label positions.
            """
            bands = [
                (120, 130),
                (130, 134),
                (134, 138),
                (138, 142),
                (142, 160),
                (160, 205),
                (205, 215),
                (215, 226),
            ]
            seen_cpi: list[float] = []
        
            for lo, hi in bands:
                mask = (cpi >= lo) & (cpi < hi)
                if not mask.any():
                    continue
                band_sales = sales[mask]
                band_cpi   = cpi[mask]
        
                # Find top-3 peaks in band to avoid overlapping labels
                top_idx = np.argsort(band_sales)[-3:]
                for i in top_idx:
                    cx = float(band_cpi[i])
                    cy = float(band_sales[i])
                    # Skip if too close to an already-labelled point
                    if any(abs(cx - sc) < 1.5 for sc in seen_cpi):
                        continue
                    ax.annotate(
                        _m_fmt(cy),
                        xy=(cx, cy),
                        xytext=(cx + 0.4, cy + 150_000),
                        fontsize=6.5,
                        color="#222",
                        arrowprops=None,
                    )
                    seen_cpi.append(cx)
 
        dashboard = WeeklySalesCPIDashboard(cpi_weekly_sales)
        dashboard.show()

    finally:
        cur.close()