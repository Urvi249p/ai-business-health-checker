import io
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from reportlab.platypus.flowables import HRFlowable, PageBreak
from reportlab.platypus import Image
from .styles import USABLE_W

def _make_swot_radar(business_profile: dict) -> Image | None:
    """Generate a SWOT radar chart from business profile data."""
    try:
        categories = ["Strengths", "Weaknesses\n(inverted)", "Opportunities", "Threats\n(inverted)"]
        labels_short = ["Strengths", "Weaknesses", "Opportunities", "Threats"]

        # Score based on profile richness
        strengths_score = min(10, (
            (2 if business_profile.get("years_in_business", 0) and
                int(business_profile.get("years_in_business", 0)) > 2 else 0) +
            (2 if business_profile.get("team_size", 0) and
                int(business_profile.get("team_size", 1)) > 1 else 0) +
            (2 if len(business_profile.get("customer_sources", [])) > 1 else 1) +
            (2 if len(business_profile.get("current_marketing_channels", [])) > 1 else 1) +
            (2 if business_profile.get("additional_notes") else 0)
        ))
        challenges = len(business_profile.get(
            "biggest_challenges", []))
        goals = len(business_profile.get("goals", []))
        channels = len(business_profile.get(
            "current_marketing_channels", []))
        sources = len(business_profile.get(
            "customer_sources", []))

        # Weaknesses: more challenges = higher score
        # (shows area of concern on radar)
        weaknesses_score = min(10, max(2, challenges * 1.5 + 1))

        # Opportunities: more goals + channels = higher
        opportunities_score = min(10, max(3, goals * 1.5 + 
            channels * 0.5 + 2))

        # Threats: moderate — driven by challenges
        # but capped lower than weaknesses
        threats_score = min(8, max(2, challenges * 0.8 + 2))

        values = [strengths_score, weaknesses_score, opportunities_score, threats_score]
        N = 4
        angles = [n / float(N) * 2 * math.pi for n in range(N)]
        angles += angles[:1]
        values_plot = values + values[:1]

        fig, ax = plt.subplots(figsize=(4.5, 4.5), subplot_kw=dict(polar=True),
            facecolor="white")

        ax.set_facecolor("#F8FAFC")
        ax.plot(angles, values_plot, "o-", linewidth=2,
            color="#059669", markersize=6)
        ax.fill(angles, values_plot, alpha=0.15, color="#059669")

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels_short, size=10, fontweight="bold",
            color="#1E293B")
        ax.set_ylim(0, 10)
        ax.set_yticks([2, 4, 6, 8, 10])
        ax.set_yticklabels(["2", "4", "6", "8", "10"], size=7, color="#94A3B8")
        ax.grid(color="#CBD5E1", linewidth=0.6)
        ax.spines["polar"].set_color("#CBD5E1")

        ax.set_title("Business Position Overview", size=11,
            fontweight="bold", color="#1E293B", pad=16)

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
            facecolor="white", edgecolor="none")
        plt.close(fig)
        buf.seek(0)

        img = Image(buf, width=220, height=220)
        return img
    except Exception:
        return None


def _make_timeline_chart(business_profile: dict) -> Image | None:
    """Generate a 90-day growth timeline chart."""
    try:
        fig, ax = plt.subplots(figsize=(8, 2.8), facecolor="white")
        ax.set_facecolor("white")

        phases = [
            ("Phase 1\nDays 1–30", "#059669", "Quick Wins & Foundation"),
            ("Phase 2\nDays 31–60", "#0891B2", "Growth Experiments"),
            ("Phase 3\nDays 61–90", "#7C3AED", "Scale & Measure"),
        ]

        bar_height = 0.5
        y_positions = [0.75, 0.45, 0.15]

        for i, ((label, color, desc), y) in enumerate(zip(phases, y_positions)):
            start = i * 30
            width = 30

            # Background track
            ax.barh(y, 90, left=0, height=bar_height * 0.4,
                color="#F1F5F9", zorder=1)

            # Phase bar
            ax.barh(y, width, left=start, height=bar_height * 0.7,
                color=color, alpha=0.85, zorder=2,
                linewidth=0)

            # Phase label on bar
            ax.text(start + width/2, y, label.split("\n")[0],
                ha="center", va="center",
                fontsize=8, fontweight="bold", color="white", zorder=3)

            # Description to right — moved further 
            # right with slightly smaller font
            ax.text(93, y, desc,
                ha="left", va="center",
                fontsize=7.5, color="#475569")

        ax.set_xlim(-2, 200)
        ax.set_ylim(-0.05, 1.0)
        ax.set_xticks([0, 30, 60, 90])
        ax.set_xticklabels(["Day 0", "Day 30", "Day 60", "Day 90"],
            fontsize=8, color="#64748B")
        ax.set_yticks([])

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_color("#CBD5E1")
        ax.tick_params(axis="x", colors="#94A3B8", length=3)

        ax.set_title("90-Day Growth Roadmap", fontsize=10,
            fontweight="bold", color="#1E293B", pad=10, loc="left")

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
            facecolor="white", edgecolor="none")
        plt.close(fig)
        buf.seek(0)

        img = Image(buf, width=USABLE_W, height=110)
        return img
    except Exception:
        return None


__all__ = ['_make_swot_radar', '_make_timeline_chart']
