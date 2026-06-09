"""
pdf_reporter.py
---------------
Generates a polished PDF version of both reports (quality + anomaly) with
embedded matplotlib charts.

Dependencies (only for this file):
    pip install reportlab matplotlib

Output:
    reports/bike_ride_report.pdf

Usage:
    Called from main.py via:
        from pdf_reporter import generate_pdf_report
        generate_pdf_report(analysis, anomalies)

    Or standalone:
        python pdf_reporter.py
"""

import os
import io
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # non-interactive backend — no display needed
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, HRFlowable, PageBreak, KeepTogether,
)
from reportlab.platypus.flowables import Flowable


# ── Colour palette ────────────────────────────────────────────────────────────

C_BRAND      = colors.HexColor("#1A6B9A")   # header blue
C_ACCENT     = colors.HexColor("#2ECC71")   # green highlight
C_WARN       = colors.HexColor("#E67E22")   # amber warning
C_DANGER     = colors.HexColor("#E74C3C")   # red / beyond-repair
C_LIGHT_BG   = colors.HexColor("#F4F8FB")   # subtle row tint
C_MID_GREY   = colors.HexColor("#BDC3C7")
C_DARK_TEXT  = colors.HexColor("#2C3E50")

# Matching hex strings for matplotlib
M_BRAND   = "#1A6B9A"
M_ACCENT  = "#2ECC71"
M_WARN    = "#E67E22"
M_DANGER  = "#E74C3C"
M_CLEAN   = "#2ECC71"
M_FIXED   = "#3498DB"
M_SUSP    = "#E67E22"
M_BEYOND  = "#E74C3C"
M_BG      = "#F4F8FB"


# ── Style sheet ───────────────────────────────────────────────────────────────

def _styles():
    base = getSampleStyleSheet()

    def add(name, **kw):
        if name not in base:
            base.add(ParagraphStyle(name=name, **kw))
        return base[name]

    add("ReportTitle",
        fontSize=26, leading=32, textColor=C_BRAND,
        fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=4)

    add("ReportSubtitle",
        fontSize=11, leading=14, textColor=C_MID_GREY,
        fontName="Helvetica", alignment=TA_CENTER, spaceAfter=20)

    add("SectionHeader",
        fontSize=13, leading=16, textColor=colors.white,
        fontName="Helvetica-Bold", alignment=TA_LEFT,
        spaceAfter=6, spaceBefore=14,
        backColor=C_BRAND, leftIndent=-6, rightIndent=-6,
        borderPadding=(4, 6, 4, 6))

    add("SubHeader",
        fontSize=10, leading=13, textColor=C_BRAND,
        fontName="Helvetica-Bold", spaceBefore=8, spaceAfter=4)

    add("Body",
        fontSize=9, leading=13, textColor=C_DARK_TEXT,
        fontName="Helvetica", spaceAfter=3)

    add("SmallGrey",
        fontSize=8, leading=11, textColor=C_MID_GREY,
        fontName="Helvetica")

    add("KPIValue",
        fontSize=22, leading=26, textColor=C_BRAND,
        fontName="Helvetica-Bold", alignment=TA_CENTER)

    add("KPILabel",
        fontSize=8, leading=10, textColor=C_MID_GREY,
        fontName="Helvetica", alignment=TA_CENTER)

    add("WarnBody",
        fontSize=9, leading=13, textColor=C_WARN,
        fontName="Helvetica-Bold", spaceAfter=3)

    add("DangerBody",
        fontSize=9, leading=13, textColor=C_DANGER,
        fontName="Helvetica-Bold", spaceAfter=3)

    return base


# ── Helper: matplotlib chart → ReportLab Image ───────────────────────────────

def _fig_to_rl_image(fig, width_mm: float = 160) -> Image:
    """Convert a matplotlib figure to a ReportLab Image flowable."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    width_pt = width_mm * mm
    return Image(buf, width=width_pt, height=width_pt * 0.45)


# ── Charts ────────────────────────────────────────────────────────────────────

def _chart_status_donut(sc: dict) -> Image:
    labels  = ["Clean", "Fixed", "Suspicious", "Beyond repair"]
    values  = [sc["clean"], sc["fixed"], sc["suspicious"], sc["beyond_repair"]]
    clrs    = [M_CLEAN, M_FIXED, M_SUSP, M_BEYOND]
    # filter zero slices
    pairs   = [(l, v, c) for l, v, c in zip(labels, values, clrs) if v > 0]
    labels, values, clrs = zip(*pairs) if pairs else ([], [], [])

    fig, ax = plt.subplots(figsize=(4, 4), facecolor=M_BG)
    wedges, texts, autotexts = ax.pie(
        values, labels=None, colors=clrs,
        autopct="%1.1f%%", startangle=90,
        pctdistance=0.78, wedgeprops=dict(width=0.55, edgecolor="white", linewidth=2)
    )
    for at in autotexts:
        at.set_fontsize(8)
        at.set_color("white")
        at.set_fontweight("bold")
    ax.legend(wedges, labels, loc="lower center", ncol=2,
              fontsize=8, frameon=False,
              bbox_to_anchor=(0.5, -0.12))
    ax.set_title("Record Status Distribution", fontsize=10,
                 fontweight="bold", color=M_BRAND, pad=10)
    fig.tight_layout()
    return _fig_to_rl_image(fig, 90)


def _chart_rides_by_day(day_counts: dict) -> Image:
    days   = list(day_counts.keys())
    counts = list(day_counts.values())
    max_c  = max(counts) if counts else 1
    bar_colors = [M_BRAND if c < max_c else M_ACCENT for c in counts]

    fig, ax = plt.subplots(figsize=(8, 3), facecolor=M_BG)
    ax.set_facecolor(M_BG)
    bars = ax.bar(days, counts, color=bar_colors, width=0.6, zorder=3)
    ax.set_ylabel("Rides", fontsize=8, color="#555")
    ax.set_title("Rides by Day of Week", fontsize=10,
                 fontweight="bold", color=M_BRAND)
    ax.tick_params(axis="x", labelsize=8, rotation=20)
    ax.tick_params(axis="y", labelsize=8)
    ax.yaxis.grid(True, color='#BDC3C7', linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    # label peak bar
    peak_idx = counts.index(max_c)
    ax.text(peak_idx, max_c + max_c * 0.02, f"{max_c:,}",
            ha="center", va="bottom", fontsize=7,
            color=M_ACCENT, fontweight="bold")
    fig.tight_layout()
    return _fig_to_rl_image(fig, 160)


def _chart_rides_by_hour(hour_counts: dict) -> Image:
    hours  = list(hour_counts.keys())
    counts = list(hour_counts.values())
    max_c  = max(counts) if counts else 1

    fig, ax = plt.subplots(figsize=(8, 2.8), facecolor=M_BG)
    ax.set_facecolor(M_BG)
    bar_colors = [M_ACCENT if c == max_c else M_BRAND for c in counts]
    ax.bar(hours, counts, color=bar_colors, width=0.8, zorder=3)
    ax.set_xlabel("Hour of day", fontsize=8, color="#555")
    ax.set_ylabel("Rides", fontsize=8, color="#555")
    ax.set_title("Rides by Hour of Day", fontsize=10,
                 fontweight="bold", color=M_BRAND)
    ax.set_xticks(range(0, 24, 2))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 24, 2)], fontsize=7, rotation=40)
    ax.tick_params(axis="y", labelsize=8)
    ax.yaxis.grid(True, color='#BDC3C7', linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    return _fig_to_rl_image(fig, 160)


def _chart_user_type(by_user_type: dict) -> Image:
    labels = [k.capitalize() for k in by_user_type.keys()]
    values = list(by_user_type.values())
    clrs   = [M_BRAND, M_ACCENT, M_WARN][:len(labels)]

    fig, ax = plt.subplots(figsize=(4, 3), facecolor=M_BG)
    ax.set_facecolor(M_BG)
    bars = ax.barh(labels, values, color=clrs, height=0.5)
    ax.set_xlabel("Rides", fontsize=8)
    ax.set_title("Rides by User Type", fontsize=10,
                 fontweight="bold", color=M_BRAND)
    ax.tick_params(labelsize=9)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.xaxis.grid(True, color='#BDC3C7', linewidth=0.5)
    ax.set_axisbelow(True)
    for bar, val in zip(bars, values):
        ax.text(val + max(values) * 0.01, bar.get_y() + bar.get_height() / 2,
                f"{val:,}", va="center", fontsize=8, color='#2C3E50')
    fig.tight_layout()
    return _fig_to_rl_image(fig, 90)


def _chart_top_routes(top_routes: list) -> Image:
    if not top_routes:
        return None
    labels = [f"{r[0][0]} → {r[0][1]}" for r in top_routes]
    values = [r[1] for r in top_routes]

    fig, ax = plt.subplots(figsize=(8, 2.6), facecolor=M_BG)
    ax.set_facecolor(M_BG)
    bars = ax.barh(labels[::-1], values[::-1], color=M_BRAND, height=0.55)
    ax.set_xlabel("Rides", fontsize=8)
    ax.set_title("Top 5 Routes", fontsize=10, fontweight="bold", color=M_BRAND)
    ax.tick_params(labelsize=8)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.xaxis.grid(True, color='#BDC3C7', linewidth=0.5)
    ax.set_axisbelow(True)
    for bar, val in zip(bars, values[::-1]):
        ax.text(val + max(values) * 0.01, bar.get_y() + bar.get_height() / 2,
                f"{val:,}", va="center", fontsize=8)
    fig.tight_layout()
    return _fig_to_rl_image(fig, 160)


# ── Small reusable flowable helpers ──────────────────────────────────────────

def _section_header(title: str, styles) -> list:
    return [
        Spacer(1, 6),
        Paragraph(f"  {title}", styles["SectionHeader"]),
        Spacer(1, 4),
    ]


def _kpi_table(kpis: list[tuple], col_width: float = 40 * mm) -> Table:
    """
    kpis: list of (value_str, label_str) tuples.
    Renders as a single-row KPI card strip.
    """
    styles = _styles()
    cells = [[Paragraph(v, styles["KPIValue"]) for v, _ in kpis],
             [Paragraph(l, styles["KPILabel"])  for _, l in kpis]]
    t = Table([cells[0], cells[1]],
              colWidths=[col_width] * len(kpis),
              rowHeights=[28, 14])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_LIGHT_BG),
        ("ROUNDEDCORNERS", [4]),
        ("BOX",        (0, 0), (-1, -1), 0.5, C_MID_GREY),
        ("INNERGRID",  (0, 0), (-1, -1), 0.25, C_MID_GREY),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def _simple_table(rows: list[list], col_widths=None, zebra=True) -> Table:
    header, *data = rows
    styles_list = [
        ("BACKGROUND",    (0, 0), (-1, 0), C_BRAND),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("ROWBACKGROUND", (0, 1), (-1, -1), [C_LIGHT_BG, colors.white]),
        ("GRID",          (0, 0), (-1, -1), 0.25, C_MID_GREY),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
    ]
    if zebra:
        for i, _ in enumerate(data):
            bg = C_LIGHT_BG if i % 2 == 0 else colors.white
            styles_list.append(("BACKGROUND", (0, i + 1), (-1, i + 1), bg))

    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle(styles_list))
    return t


def _fmt(n, decimals=0) -> str:
    if n is None:
        return "N/A"
    if decimals:
        return f"{n:,.{decimals}f}"
    return f"{int(n):,}"


def _pct(part, total) -> str:
    if not total:
        return "0.0%"
    return f"{part / total * 100:.1f}%"


# ── Page template (header / footer) ──────────────────────────────────────────

def _make_page_template(canvas, doc):
    canvas.saveState()
    w, h = A4

    # top accent bar
    canvas.setFillColor(C_BRAND)
    canvas.rect(0, h - 8 * mm, w, 8 * mm, fill=1, stroke=0)

    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(15 * mm, h - 5.5 * mm, "City Bike Analytics")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(w - 15 * mm, h - 5.5 * mm,
                           datetime.now().strftime("%Y-%m-%d"))

    # footer
    canvas.setFillColor(C_MID_GREY)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(15 * mm, 8 * mm, "Confidential — City Mobility Operations")
    canvas.drawRightString(w - 15 * mm, 8 * mm, f"Page {doc.page}")
    canvas.setStrokeColor(C_MID_GREY)
    canvas.setLineWidth(0.5)
    canvas.line(15 * mm, 12 * mm, w - 15 * mm, 12 * mm)

    canvas.restoreState()


# ── Quality report section builders ──────────────────────────────────────────

def _section_cover(analysis: dict, story: list, styles):
    sc = analysis["status_counts"]
    total  = sc["total"]
    usable = sc["clean"] + sc["fixed"] + sc["suspicious"]

    story.append(Spacer(1, 20 * mm))
    story.append(Paragraph("City Bike Ride", styles["ReportTitle"]))
    story.append(Paragraph("Quality &amp; Anomaly Report", styles["ReportTitle"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"Generated {datetime.now().strftime('%d %B %Y at %H:%M')}  ·  "
        f"Source: data/bike_rides_cleaned.csv",
        styles["ReportSubtitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=C_MID_GREY, spaceAfter=14))

    # KPI strip
    story.append(_kpi_table([
        (_fmt(total),       "Total records"),
        (_fmt(usable),      "Usable for analysis"),
        (_fmt(sc["beyond_repair"]), "Excluded"),
        (_pct(usable, total), "Usable rate"),
    ]))
    story.append(Spacer(1, 10))

    # donut + user-type side by side
    donut = _chart_status_donut(sc)
    ut    = _chart_user_type(analysis["rides_by_user_type"])
    side  = Table([[donut, ut]], colWidths=[95 * mm, 95 * mm])
    side.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                               ("LEFTPADDING",  (0, 0), (-1, -1), 0),
                               ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    story.append(side)
    story.append(PageBreak())


def _section_dataset_summary(analysis: dict, story: list, styles):
    sc     = analysis["status_counts"]
    total  = sc["total"]
    usable = sc["clean"] + sc["fixed"] + sc["suspicious"]

    story += _section_header("1 · Dataset Summary", styles)

    rows = [
        ["Status", "Count", "% of total", "Notes"],
        ["Clean",         _fmt(sc["clean"]),        _pct(sc["clean"],        total), "No changes required"],
        ["Fixed",         _fmt(sc["fixed"]),         _pct(sc["fixed"],        total), "Cleaned and repaired"],
        ["Suspicious",    _fmt(sc["suspicious"]),    _pct(sc["suspicious"],   total), "Flagged — included in analysis"],
        ["Beyond repair", _fmt(sc["beyond_repair"]), _pct(sc["beyond_repair"], total), "Excluded from all analysis"],
        ["Usable total",  _fmt(usable),              _pct(usable, total),              "Clean + Fixed + Suspicious"],
    ]
    cw = [45 * mm, 28 * mm, 28 * mm, 65 * mm]
    t  = _simple_table(rows, col_widths=cw)
    # colour the beyond-repair row red-ish
    beyond_row = 4
    t.setStyle(TableStyle([
        ("TEXTCOLOR", (0, beyond_row), (-1, beyond_row), C_DANGER),
        ("FONTNAME",  (0, beyond_row), (-1, beyond_row), "Helvetica-Bold"),
    ]))
    story.append(t)
    story.append(Spacer(1, 6))


def _section_ride_stats(analysis: dict, story: list, styles):
    story += _section_header("2 · Ride Statistics", styles)

    avg_dur  = analysis["avg_duration"]
    avg_dist = analysis["avg_distance"]
    same_st  = analysis["same_station_count"]

    story.append(_kpi_table([
        (_fmt(avg_dur,  1) + " min", "Avg. duration"),
        (_fmt(avg_dist, 2) + " km",  "Avg. distance"),
        (_fmt(same_st),              "Same-station trips"),
    ], col_width=55 * mm))
    story.append(Spacer(1, 8))

    # avg by user type table
    story.append(Paragraph("Average metrics by rider type", styles["SubHeader"]))
    dur_by  = analysis["avg_duration_by_type"]
    dist_by = analysis["avg_distance_by_type"]
    all_types = sorted(set(list(dur_by.keys()) + list(dist_by.keys())))
    rows = [["Rider type", "Avg. duration (min)", "Avg. distance (km)"]]
    for ut in all_types:
        rows.append([
            ut.capitalize(),
            _fmt(dur_by.get(ut),  1),
            _fmt(dist_by.get(ut), 2),
        ])
    story.append(_simple_table(rows, col_widths=[60 * mm, 60 * mm, 60 * mm]))
    story.append(Spacer(1, 6))


def _section_stations_routes(analysis: dict, story: list, styles):
    story += _section_header("3 · Stations &amp; Routes", styles)

    mps = analysis["most_popular_start"]
    mpe = analysis["most_popular_end"]

    story.append(Paragraph("Most active stations", styles["SubHeader"]))
    rows = [
        ["Direction", "Station", "Rides"],
        ["Start", mps[0] if mps else "N/A", _fmt(mps[1]) if mps else "N/A"],
        ["End",   mpe[0] if mpe else "N/A", _fmt(mpe[1]) if mpe else "N/A"],
    ]
    story.append(_simple_table(rows, col_widths=[35 * mm, 100 * mm, 35 * mm]))
    story.append(Spacer(1, 8))

    chart = _chart_top_routes(analysis["top_5_routes"])
    if chart:
        story.append(chart)
    story.append(Spacer(1, 6))


def _section_time_patterns(analysis: dict, story: list, styles):
    story += _section_header("4 · Time Patterns", styles)

    busiest_day  = analysis["busiest_day"]
    quietest_day = analysis["quietest_day"]
    busiest_hour = analysis["busiest_hour"]

    story.append(_kpi_table([
        (busiest_day,           "Busiest day"),
        (quietest_day,          "Quietest day"),
        (f"{busiest_hour:02d}:00", "Peak hour"),
    ], col_width=55 * mm))
    story.append(Spacer(1, 8))
    story.append(_chart_rides_by_day(analysis["rides_by_day"]))
    story.append(Spacer(1, 6))
    story.append(_chart_rides_by_hour(analysis["rides_by_hour"]))
    story.append(Spacer(1, 6))


def _section_top_bikes(analysis: dict, story: list, styles):
    story += _section_header("5 · Most Active Bikes", styles)
    top = analysis["top_5_bikes"]
    if top:
        rows = [["Rank", "Bike ID", "Rides"]]
        for i, (bike, count) in enumerate(top, 1):
            rows.append([str(i), bike, _fmt(count)])
        story.append(_simple_table(rows, col_widths=[20 * mm, 100 * mm, 50 * mm]))
    else:
        story.append(Paragraph("No bike data available.", styles["Body"]))
    story.append(Spacer(1, 6))


# ── Anomaly section builders ──────────────────────────────────────────────────

def _section_anomaly_summary(anomalies: dict, story: list, styles):
    story += _section_header("6 · Anomaly Overview", styles)

    dup      = anomalies.get("duplicate_ride_ids",    {}).get("total_duplicates", 0)
    overlaps = anomalies.get("bike_overlaps",         {}).get("total_bikes_with_overlap", 0)
    zd       = anomalies.get("zero_duration",         {}).get("count", 0)
    dm       = anomalies.get("duration_mismatch",     {}).get("count", 0)
    sdd      = anomalies.get("strange_distance_duration", {}).get("total_suspicious", 0)
    unk      = anomalies.get("unknown_stations",      {}).get("total_unknown_stations", 0)

    def _status_color(v):
        return C_ACCENT if v == 0 else C_DANGER

    rows = [
        ["Anomaly type", "Count", "Severity"],
        ["Duplicate ride IDs",                   _fmt(dup),      "High"   if dup      else "OK"],
        ["Bikes with overlapping rides",          _fmt(overlaps), "High"   if overlaps else "OK"],
        ["Zero-duration rides",                   _fmt(zd),       "Medium" if zd       else "OK"],
        ["Duration / timestamp mismatches",       _fmt(dm),       "Low"    if dm       else "OK"],
        ["Impossible distance+duration combos",   _fmt(sdd),      "Medium" if sdd      else "OK"],
        ["Unknown / missing stations",            _fmt(unk),      "Medium" if unk      else "OK"],
    ]
    t = _simple_table(rows, col_widths=[100 * mm, 30 * mm, 40 * mm])

    # colour severity column
    severity_map = {"High": C_DANGER, "Medium": C_WARN, "Low": C_BRAND, "OK": C_ACCENT}
    for row_i, row in enumerate(rows[1:], 1):
        sev = row[2]
        t.setStyle(TableStyle([
            ("TEXTCOLOR",  (2, row_i), (2, row_i), severity_map.get(sev, C_DARK_TEXT)),
            ("FONTNAME",   (2, row_i), (2, row_i), "Helvetica-Bold"),
        ]))
    story.append(t)
    story.append(Spacer(1, 6))


def _section_duplicate_ids(anomalies: dict, story: list, styles):
    dup = anomalies.get("duplicate_ride_ids", {})
    count = dup.get("total_duplicates", 0)
    story += _section_header("7 · Duplicate Ride IDs", styles)

    if not count:
        story.append(Paragraph("✓ No duplicate ride IDs detected.", styles["Body"]))
        return

    story.append(Paragraph(
        f"<font color='#{C_DANGER.hexval()}'>⚠ {_fmt(count)} duplicate ID(s) found.</font>  "
        "These must be resolved before any official billing or usage count.",
        styles["Body"]))
    story.append(Spacer(1, 4))

    sample = dup.get("duplicate_ride_ids", [])[:10]
    rows = [["Ride ID", "Occurrences"]]
    for entry in sample:
        rows.append([entry["ride_id"], str(entry["count"])])
    story.append(_simple_table(rows, col_widths=[100 * mm, 70 * mm]))
    story.append(Spacer(1, 6))


def _section_bike_overlaps(anomalies: dict, story: list, styles):
    data  = anomalies.get("bike_overlaps", {})
    count = data.get("total_bikes_with_overlap", 0)
    story += _section_header("8 · Bikes with Overlapping Rides", styles)

    if not count:
        story.append(Paragraph("✓ No bike overlap incidents detected.", styles["Body"]))
        return

    story.append(Paragraph(
        f"<font color='#{C_DANGER.hexval()}'>⚠ {_fmt(count)} overlap incident(s).</font>  "
        "A bike cannot be in two rides simultaneously — checkout-system sync error likely.",
        styles["Body"]))
    story.append(Spacer(1, 4))

    sample = data.get("overlapping_bikes", [])[:8]
    rows = [["Bike ID", "Ride 1", "Ride 2", "Overlap (min)"]]
    for e in sample:
        rows.append([
            e["bike_id"], e["ride1_id"], e["ride2_id"],
            f"{abs(e.get('overlap_minutes', 0)):.1f}",
        ])
    story.append(_simple_table(rows, col_widths=[35 * mm, 45 * mm, 45 * mm, 45 * mm]))
    story.append(Spacer(1, 6))


def _section_station_spikes(anomalies: dict, story: list, styles):
    spike = anomalies.get("station_spike", {})
    ss    = spike.get("spiked_start_stations", [])
    se    = spike.get("spiked_end_stations",   [])
    story += _section_header("9 · Station Usage Spikes  (&gt; 1.3× average)", styles)

    avg_s = spike.get("average_start_usage", 0)
    avg_e = spike.get("average_end_usage", 0)

    story.append(Paragraph(
        f"Average start-station usage: <b>{avg_s:.1f}</b> rides  ·  "
        f"Average end-station usage: <b>{avg_e:.1f}</b> rides",
        styles["Body"]))
    story.append(Spacer(1, 4))

    if not ss and not se:
        story.append(Paragraph("✓ No station spikes detected.", styles["Body"]))
        return

    if ss:
        story.append(Paragraph("Spiked start stations", styles["SubHeader"]))
        rows = [["Station", "Rides", "Ratio vs avg"]]
        for s in sorted(ss, key=lambda x: -x["count"])[:8]:
            rows.append([s["station"], _fmt(s["count"]), f"{s['ratio']:.1f}×"])
        story.append(_simple_table(rows, col_widths=[90 * mm, 40 * mm, 40 * mm]))
        story.append(Spacer(1, 4))

    if se:
        story.append(Paragraph("Spiked end stations", styles["SubHeader"]))
        rows = [["Station", "Rides", "Ratio vs avg"]]
        for s in sorted(se, key=lambda x: -x["count"])[:8]:
            rows.append([s["station"], _fmt(s["count"]), f"{s['ratio']:.1f}×"])
        story.append(_simple_table(rows, col_widths=[90 * mm, 40 * mm, 40 * mm]))
    story.append(Spacer(1, 6))


def _section_impossible_combos(anomalies: dict, story: list, styles):
    sdd   = anomalies.get("strange_distance_duration", {})
    count = sdd.get("total_suspicious", 0)
    story += _section_header("10 · Impossible Distance / Duration Combinations", styles)

    if not count:
        story.append(Paragraph("✓ No impossible distance/duration pairs found.", styles["Body"]))
        return

    combos = sdd.get("suspicious_combinations", [])
    hi = [r for r in combos if r["type"] == "high_distance_short_duration"]
    lo = [r for r in combos if r["type"] == "low_distance_long_duration"]
    story.append(Paragraph(
        f"Total suspicious: <b>{_fmt(count)}</b>  "
        f"(high-distance/short-duration: <b>{len(hi)}</b>  ·  "
        f"low-distance/long-duration: <b>{len(lo)}</b>)",
        styles["Body"]))
    story.append(Spacer(1, 4))

    rows = [["Ride ID", "Distance (km)", "Duration (min)", "Speed (km/h)", "Type"]]
    for r in combos[:10]:
        rows.append([
            r["ride_id"],
            f"{r['distance_km']:.2f}",
            f"{r['duration_minutes']:.1f}",
            f"{r['speed_kph']:.1f}",
            "Fast" if r["type"] == "high_distance_short_duration" else "Slow",
        ])
    story.append(_simple_table(rows, col_widths=[30 * mm, 32 * mm, 34 * mm, 34 * mm, 36 * mm]))
    story.append(Spacer(1, 6))


def _section_suspicious_bikes_stations(anomalies: dict, story: list, styles):
    bws = anomalies.get("bikes_with_suspicious", {})
    sws = anomalies.get("stations_with_suspicious", {})
    story += _section_header("11 · Top Suspicious Bikes &amp; Stations", styles)

    top_bikes = bws.get("top_suspicious_bikes", [])[:8]
    if top_bikes:
        story.append(Paragraph("Bikes with most suspicious records", styles["SubHeader"]))
        rows = [["Bike ID", "Suspicious records"]]
        for e in top_bikes:
            rows.append([e["bike_id"], _fmt(e["suspicious_count"])])
        story.append(_simple_table(rows, col_widths=[90 * mm, 80 * mm]))
        story.append(Spacer(1, 6))

    top_s_start = sws.get("top_suspicious_start_stations", [])[:6]
    top_s_end   = sws.get("top_suspicious_end_stations",   [])[:6]
    if top_s_start or top_s_end:
        story.append(Paragraph("Stations with most suspicious involvement", styles["SubHeader"]))
        combined = {}
        for e in top_s_start:
            combined[e["station"]] = combined.get(e["station"], 0) + e["suspicious_count"]
        for e in top_s_end:
            combined[e["station"]] = combined.get(e["station"], 0) + e["suspicious_count"]
        rows = [["Station", "Suspicious record involvements"]]
        for station, cnt in sorted(combined.items(), key=lambda x: -x[1])[:8]:
            rows.append([station, _fmt(cnt)])
        story.append(_simple_table(rows, col_widths=[90 * mm, 80 * mm]))
    story.append(Spacer(1, 6))


def _section_recommendations(anomalies: dict, story: list, styles):
    story += _section_header("12 · Recommended Follow-Up", styles)

    recs = []
    if anomalies.get("duplicate_ride_ids",        {}).get("total_duplicates", 0):
        recs.append(("High",   "Resolve duplicate ride IDs before any official usage count or billing report."))
    if anomalies.get("bike_overlaps",             {}).get("total_bikes_with_overlap", 0):
        recs.append(("High",   "Check overlapping bikes for checkout-system sync errors or cloned records."))
    if anomalies.get("zero_duration",             {}).get("count", 0):
        recs.append(("Medium", "Zero-duration rides with different stations likely represent checkout errors; exclude from usage reporting."))
    if anomalies.get("duration_mismatch",         {}).get("count", 0):
        recs.append(("Low",    "Duration/timestamp mismatches suggest clock drift or manual rounding; audit data collection at source."))
    if anomalies.get("strange_distance_duration", {}).get("total_suspicious", 0):
        recs.append(("Medium", "Verify sensor calibration on bikes producing impossible speed values (>60 km/h or <2 km/h)."))
    if anomalies.get("station_spike",             {}).get("spiked_start_stations"):
        recs.append(("Low",    "Cross-check spiked stations with city-event calendars before attributing to data error."))
    if anomalies.get("route_spike",               {}).get("spiked_routes"):
        recs.append(("Low",    "High-frequency routes may reflect commuter demand; consider dedicated docking expansion there."))
    if anomalies.get("unknown_stations",          {}).get("total_unknown_stations", 0):
        recs.append(("Medium", "Records missing a valid station name cannot be mapped; review docking-terminal software."))

    if not recs:
        story.append(Paragraph("✓ No significant anomalies detected. Data quality looks healthy.", styles["Body"]))
        return

    sev_color = {"High": C_DANGER, "Medium": C_WARN, "Low": C_BRAND}
    rows = [["Priority", "Action"]]
    for sev, text in recs:
        rows.append([sev, text])
    t = _simple_table(rows, col_widths=[25 * mm, 145 * mm])
    for i, (sev, _) in enumerate(recs, 1):
        t.setStyle(TableStyle([
            ("TEXTCOLOR", (0, i), (0, i), sev_color.get(sev, C_DARK_TEXT)),
            ("FONTNAME",  (0, i), (0, i), "Helvetica-Bold"),
        ]))
    story.append(t)
    story.append(Spacer(1, 6))


# ── Public entry point ────────────────────────────────────────────────────────

def generate_pdf_report(
    analysis: dict,
    anomalies: dict,
    output_path: str = "reports/bike_ride_report.pdf",
) -> str:
    """
    Generate a polished PDF report combining quality analysis and anomaly detection.

    Args:
        analysis    : return value of analyzer.analyze()
        anomalies   : return value of anomaly_detector.analyze_anomalies()
        output_path : where to write the PDF

    Returns:
        The output_path string so callers can print/log it.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="City Bike Ride Report",
        author="City Mobility Operations",
    )

    styles = _styles()
    story  = []

    # ── Quality sections ──────────────────────────────────────────────────────
    _section_cover(analysis, story, styles)
    _section_dataset_summary(analysis, story, styles)
    _section_ride_stats(analysis, story, styles)
    _section_stations_routes(analysis, story, styles)
    _section_time_patterns(analysis, story, styles)
    _section_top_bikes(analysis, story, styles)

    story.append(PageBreak())

    # ── Anomaly sections ──────────────────────────────────────────────────────
    story.append(Paragraph("Anomaly Detection Report", styles["ReportTitle"]))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1, color=C_MID_GREY, spaceAfter=10))

    _section_anomaly_summary(anomalies, story, styles)
    _section_duplicate_ids(anomalies, story, styles)
    _section_bike_overlaps(anomalies, story, styles)
    _section_station_spikes(anomalies, story, styles)
    _section_impossible_combos(anomalies, story, styles)
    _section_suspicious_bikes_stations(anomalies, story, styles)
    _section_recommendations(anomalies, story, styles)

    doc.build(story, onFirstPage=_make_page_template, onLaterPages=_make_page_template)
    print(f"PDF report written to: {output_path}")
    return output_path


# ── Standalone usage ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")

    import validator, cleaner, analyzer
    from anomaly_detector import analyze_anomalies

    validator.validate_records("data/bike_rides.csv")
    cleaned = cleaner.clean_data("data/bike_rides.csv", "data/bike_rides_cleaned.csv")
    anomalies = analyze_anomalies()
    analysis  = analyzer.analyze(cleaned)

    generate_pdf_report(analysis, anomalies)