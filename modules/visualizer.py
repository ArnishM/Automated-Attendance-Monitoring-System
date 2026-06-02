"""
visualizer.py
=============
Generates bar charts, pie charts, and trend graphs from attendance data.

PL-2 Concepts: Data Visualization (Matplotlib, Seaborn)
"""

import os
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import numpy as np
from datetime import datetime

from modules.report_analyzer import ReportAnalyzer


# ── Global style ──────────────────────────────────────────────────────────────
sns.set_theme(style="darkgrid", palette="muted")
ACCENT   = "#4FC3F7"
WARN_CLR = "#FF7043"
BG_CLR   = "#1a1a2e"
TXT_CLR  = "#e0e0e0"


def _style_axis(ax, title: str):
    """Applies consistent dark-theme styling to an axis."""
    ax.set_facecolor("#16213e")
    ax.set_title(title, color=TXT_CLR, fontsize=13, fontweight="bold", pad=12)
    ax.tick_params(colors=TXT_CLR)
    for spine in ax.spines.values():
        spine.set_edgecolor("#2a2a4a")
    ax.xaxis.label.set_color(TXT_CLR)
    ax.yaxis.label.set_color(TXT_CLR)


class Visualizer:
    """
    Creates and saves attendance charts to the reports/ directory.
    """

    def __init__(self, analyzer: ReportAnalyzer, reports_dir: str = "reports"):
        self.analyzer    = analyzer
        self.reports_dir = reports_dir
        os.makedirs(self.reports_dir, exist_ok=True)

    def _save(self, fig, filename: str) -> str:
        """Saves a figure and returns its path."""
        path = os.path.join(self.reports_dir, filename)
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG_CLR)
        plt.close(fig)
        print(f"  Saved: {path}")
        return path

    # -----------------------------------------------------------------------
    # 1. Bar chart — per-student attendance %
    # -----------------------------------------------------------------------
    def bar_chart_attendance(self) -> str:
        """
        Generates a bar chart showing attendance % for each student.
        Bars below threshold are highlighted in red.
        """
        percentages = self.analyzer.get_all_percentages()
        if not percentages:
            print("  [Visualizer] No data for bar chart.")
            return ""

        names  = list(percentages.keys())
        values = [percentages[n] for n in names]
        colors = [WARN_CLR if v < self.analyzer.threshold else ACCENT for v in values]

        fig, ax = plt.subplots(figsize=(max(8, len(names) * 1.2), 5))
        fig.patch.set_facecolor(BG_CLR)

        bars = ax.bar(names, values, color=colors, edgecolor="#2a2a4a", zorder=3)

        # Threshold line
        ax.axhline(y=self.analyzer.threshold, color="#FFD54F", linestyle="--",
                   linewidth=1.5, label=f"Threshold ({self.analyzer.threshold}%)", zorder=4)

        # Value labels on bars
        for bar, val in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1.5,
                f"{val:.0f}%",
                ha="center", va="bottom",
                color=TXT_CLR, fontsize=9, fontweight="bold"
            )

        ax.set_ylim(0, 115)
        ax.set_xlabel("Student Name", fontsize=10)
        ax.set_ylabel("Attendance (%)", fontsize=10)
        ax.yaxis.set_major_formatter(mticker.PercentFormatter())
        ax.legend(facecolor="#16213e", edgecolor="#2a2a4a", labelcolor=TXT_CLR)
        ax.tick_params(axis="x", rotation=15)
        _style_axis(ax, "Student Attendance Percentage")

        return self._save(fig, "bar_chart_attendance.png")

    # -----------------------------------------------------------------------
    # 2. Pie chart — Present vs Absent totals
    # -----------------------------------------------------------------------
    def pie_chart_distribution(self) -> str:
        """
        Generates a pie chart showing overall Present vs Absent split.
        """
        records = self.analyzer.manager.get_all_records()
        if not records:
            print("  [Visualizer] No data for pie chart.")
            return ""

        # All registered students × all class dates = total slots
        all_dates  = self.analyzer._get_all_dates()
        all_names  = self.analyzer._get_student_names()
        total_slots = len(all_dates) * len(all_names) if all_names and all_dates else 1

        present_count = sum(1 for r in records if r["status"] == "Present")
        absent_count  = max(0, total_slots - present_count)

        sizes  = [present_count, absent_count]
        labels = [f"Present\n({present_count})", f"Absent\n({absent_count})"]
        colors = [ACCENT, WARN_CLR]
        explode = (0.05, 0)

        fig, ax = plt.subplots(figsize=(6, 6))
        fig.patch.set_facecolor(BG_CLR)

        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            explode=explode,
            autopct="%1.1f%%",
            startangle=140,
            wedgeprops={"edgecolor": "#1a1a2e", "linewidth": 2},
            textprops={"color": TXT_CLR, "fontsize": 11}
        )
        for at in autotexts:
            at.set_fontsize(11)
            at.set_color(BG_CLR)
            at.set_fontweight("bold")

        ax.set_facecolor(BG_CLR)
        ax.set_title("Overall Attendance Distribution", color=TXT_CLR,
                     fontsize=13, fontweight="bold")

        return self._save(fig, "pie_chart_distribution.png")

    # -----------------------------------------------------------------------
    # 3. Trend graph — date-wise attendance count
    # -----------------------------------------------------------------------
    def trend_graph(self) -> str:
        """
        Generates a line graph showing how many students were present each day.
        """
        trend = self.analyzer.attendance_trend()
        if not trend:
            print("  [Visualizer] No data for trend graph.")
            return ""

        dates_raw = list(trend.keys())
        counts    = list(trend.values())

        # Format x-axis labels as "Apr 11"
        # Auto-detect date format: handles both YYYY-MM-DD and DD-MM-YYYY
        def parse_date_label(d):
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
                try:
                    return datetime.strptime(d, fmt).strftime("%b %d")
                except ValueError:
                    continue
            return d   # fallback: show raw string if no format matches

        date_labels = [parse_date_label(d) for d in dates_raw]

        fig, ax = plt.subplots(figsize=(max(8, len(dates_raw) * 0.9), 5))
        fig.patch.set_facecolor(BG_CLR)

        ax.plot(date_labels, counts, marker="o", color=ACCENT,
                linewidth=2.5, markersize=8, markerfacecolor="#FFD54F",
                markeredgewidth=2, zorder=5)
        ax.fill_between(date_labels, counts, alpha=0.18, color=ACCENT)

        # Annotate each point
        for x, y in zip(date_labels, counts):
            ax.annotate(str(y), (x, y), textcoords="offset points",
                        xytext=(0, 10), ha="center", color=TXT_CLR, fontsize=9)

        ax.set_ylim(0, max(counts) + 3)
        ax.set_xlabel("Date", fontsize=10)
        ax.set_ylabel("Students Present", fontsize=10)
        ax.tick_params(axis="x", rotation=20)
        _style_axis(ax, "📈 Daily Attendance Trend")

        return self._save(fig, "trend_graph.png")

    # -----------------------------------------------------------------------
    # Convenience: generate all charts at once
    # -----------------------------------------------------------------------
    def generate_all(self):
        """Generates and saves all three charts."""
        print("\n Generating visualizations...")
        self.bar_chart_attendance()
        self.pie_chart_distribution()
        self.trend_graph()
        print(f"\n  All charts saved to: {os.path.abspath(self.reports_dir)}/")
