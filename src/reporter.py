"""
reporter.py
-----------
Turns the raw dicts from analyzer.analyze() and anomaly_detector.analyze_anomalies()
into two human-readable reports written to the reports/ directory:

  reports/bike_ride_quality_report.txt   — dataset health, usage patterns, ride stats
  reports/anomaly_report.txt             — operational anomalies and follow-up actions

Both reports are also printed to stdout unless quiet=True is passed to generate_reports().
"""

import os
from datetime import datetime

# ── formatting helpers ────────────────────────────────────────────────────────

def _header(title: str, width: int = 60) -> str:
    return f"\n{'=' * width}\n{title.upper()}\n{'=' * width}\n"

def _section(title: str, width: int = 60) -> str:
    return f"\n{title}\n{'-' * min(len(title), width)}\n"

def _pct(part: int, total: int) -> str:
    if total == 0:
        return "0.0%"
    return f"{part / total * 100:.1f}%"

def _fmt_num(n) -> str:
    """Format an integer with thousands separators."""
    if n is None:
        return "N/A"
    return f"{int(n):,}"

def _fmt_float(n, decimals: int = 1) -> str:
    if n is None:
        return "N/A"
    return f"{n:.{decimals}f}"

def _bar(value: int, max_value: int, width: int = 20) -> str:
    """Simple ASCII bar proportional to max_value."""
    if max_value == 0:
        return "░" * width
    filled = round(value / max_value * width)
    return "█" * filled + "░" * (width - filled)

def _rank(items, label_fn=str, count_fn=None, top: int = 5) -> str:
    """Format a ranked list from a list of tuples or dicts."""
    lines = []
    for i, item in enumerate(items[:top], 1):
        if isinstance(item, tuple):
            label, count = label_fn(item[0]), item[1]
        elif isinstance(item, dict):
            label = label_fn(item)
            count = count_fn(item) if count_fn else "?"
        else:
            label, count = str(item), ""
        lines.append(f"  {i:>2}. {label:<38} {_fmt_num(count)} rides")
    return "\n".join(lines) if lines else "  None recorded."

# ── quality report ────────────────────────────────────────────────────────────

def _build_quality_report(analysis: dict) -> str:
    lines = []

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines.append(_header("City Bike Ride Quality Report"))
    lines.append(f"  Generated : {now}")
    lines.append(f"  Source    : data/bike_rides_cleaned.csv\n")

    # ── Dataset Summary ──────────────────────────────────────────────────────
    sc = analysis["status_counts"]
    total       = sc["total"]
    clean       = sc["clean"]
    fixed       = sc["fixed"]
    suspicious  = sc["suspicious"]
    beyond      = sc["beyond_repair"]
    usable      = clean + fixed + suspicious   # mirrors _usable() in analyzer

    lines.append(_section("1. Dataset Summary"))
    lines.append(f"  Total records read         : {_fmt_num(total)}")
    lines.append(f"  Clean (no changes needed)  : {_fmt_num(clean)}  ({_pct(clean,  total)})")
    lines.append(f"  Fixed (cleaned & repaired) : {_fmt_num(fixed)}  ({_pct(fixed,  total)})")
    lines.append(f"  Suspicious (flagged)       : {_fmt_num(suspicious)}  ({_pct(suspicious, total)})")
    lines.append(f"  Beyond repair (excluded)   : {_fmt_num(beyond)}  ({_pct(beyond, total)})")
    lines.append(f"\n  ► Usable for analysis      : {_fmt_num(usable)}  ({_pct(usable, total)})")

    # ── Rider Breakdown ──────────────────────────────────────────────────────
    rut = analysis["rides_by_user_type"]
    lines.append(_section("2. Rider Breakdown"))
    lines.append(f"  Total usable rides         : {_fmt_num(usable)}")
    for utype in ["member", "casual", "tourist"]:
        count = rut.get(utype, 0)
        lines.append(f"  {utype.capitalize():<10}                 : {_fmt_num(count)}  ({_pct(count, usable)})")

    # ── Duration Summary ─────────────────────────────────────────────────────
    avg_dur = analysis["avg_duration"]
    avg_dur_by_type = analysis["avg_duration_by_type"]
    lines.append(_section("3. Duration Summary"))
    lines.append(f"  Average ride duration      : {_fmt_float(avg_dur)} minutes")
    lines.append("")
    lines.append("  Average by rider type:")
    for utype, val in avg_dur_by_type.items():
        lines.append(f"    {utype.capitalize():<12}               : {_fmt_float(val)} min")

    # ── Distance Summary ─────────────────────────────────────────────────────
    avg_dist = analysis["avg_distance"]
    avg_dist_by_type = analysis["avg_distance_by_type"]
    lines.append(_section("4. Distance Summary"))
    lines.append(f"  Average ride distance      : {_fmt_float(avg_dist)} km")
    lines.append("")
    lines.append("  Average by rider type:")
    for utype, val in avg_dist_by_type.items():
        lines.append(f"    {utype.capitalize():<12}               : {_fmt_float(val)} km")

    # ── Station Summary ──────────────────────────────────────────────────────
    mps = analysis["most_popular_start"]
    mpe = analysis["most_popular_end"]
    lines.append(_section("5. Station Summary"))
    lines.append(f"  Most popular start station : {mps[0] if mps else 'N/A'}  ({_fmt_num(mps[1]) if mps else 'N/A'} rides)")
    lines.append(f"  Most popular end station   : {mpe[0] if mpe else 'N/A'}  ({_fmt_num(mpe[1]) if mpe else 'N/A'} rides)")
    lines.append(f"  Same-station round trips   : {_fmt_num(analysis['same_station_count'])}")

    # ── Popular Routes ───────────────────────────────────────────────────────
    lines.append(_section("6. Top 5 Routes"))
    top_routes = analysis["top_5_routes"]
    if top_routes:
        for i, (route, count) in enumerate(top_routes, 1):
            label = f"{route[0]} → {route[1]}"
            lines.append(f"  {i:>2}. {label:<42} {_fmt_num(count)} rides")
    else:
        lines.append("  No route data available.")

    # ── Top 5 Bikes ──────────────────────────────────────────────────────────
    lines.append(_section("7. Most Active Bikes"))
    top_bikes = analysis["top_5_bikes"]
    if top_bikes:
        for i, (bike, count) in enumerate(top_bikes, 1):
            lines.append(f"  {i:>2}. {bike:<38} {_fmt_num(count)} rides")
    else:
        lines.append("  No bike data available.")

    # ── Day-of-Week Pattern ──────────────────────────────────────────────────
    rbd = analysis["rides_by_day"]
    busiest_day  = analysis["busiest_day"]
    quietest_day = analysis["quietest_day"]
    max_day_val  = max(rbd.values()) if rbd else 1

    lines.append(_section("8. Day-of-Week Pattern"))
    lines.append(f"  Busiest day   : {busiest_day}")
    lines.append(f"  Quietest day  : {quietest_day}")
    lines.append("")
    for day, count in rbd.items():
        bar = _bar(count, max_day_val, width=25)
        marker = " ◄" if day == busiest_day else ""
        lines.append(f"  {day:<12} {bar}  {_fmt_num(count)}{marker}")

    # ── Hourly Pattern ───────────────────────────────────────────────────────
    rbh = analysis["rides_by_hour"]
    busiest_hour = analysis["busiest_hour"]
    max_hour_val = max(rbh.values()) if rbh else 1

    lines.append(_section("9. Hourly Pattern"))
    lines.append(f"  Busiest hour  : {busiest_hour:02d}:00 – {busiest_hour:02d}:59\n")
    for hour, count in rbh.items():
        bar = _bar(count, max_hour_val, width=20)
        marker = " ◄ peak" if hour == busiest_hour else ""
        lines.append(f"  {hour:02d}:00  {bar}  {_fmt_num(count)}{marker}")

    # ── Suspicious Flags ─────────────────────────────────────────────────────
    susp_bikes    = analysis["suspicious_bikes"]
    susp_stations = analysis["suspicious_stations"]

    lines.append(_section("10. Suspicious Activity Flags"))

    if susp_bikes:
        top_sb = susp_bikes.most_common(5)
        lines.append(f"  Bikes with most suspicious rides (top {len(top_sb)}):")
        for bike, count in top_sb:
            lines.append(f"    {bike:<20} {count} suspicious ride(s)")
    else:
        lines.append("  No suspicious bikes recorded.")

    lines.append("")

    if susp_stations:
        top_ss = susp_stations.most_common(5)
        lines.append(f"  Stations most often in suspicious rides (top {len(top_ss)}):")
        for station, count in top_ss:
            lines.append(f"    {station:<30} {count} occurrence(s)")
    else:
        lines.append("  No suspicious stations recorded.")

    lines.append("\n" + "=" * 60 + "\n  End of Quality Report\n" + "=" * 60)
    return "\n".join(lines)


# ── anomaly report ────────────────────────────────────────────────────────────

def _build_anomaly_report(anomalies: dict) -> str:
    lines = []

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines.append(_header("City Bike Ride — Anomaly Report"))
    lines.append(f"  Generated : {now}")
    lines.append(f"  Source    : data/bike_rides_cleaned.csv\n")

    recommendations = []

    # ── Duplicate Ride IDs ───────────────────────────────────────────────────
    dup = anomalies.get("duplicate_ride_ids", {})
    dup_count = dup.get("total_duplicates", 0)
    lines.append(_section("1. Duplicate Ride IDs"))
    lines.append(f"  Total duplicate IDs found  : {_fmt_num(dup_count)}")
    if dup_count:
        lines.append("  Sample duplicates:")
        for entry in dup.get("duplicate_ride_ids", [])[:10]:
            lines.append(f"    {entry['ride_id']}  — appears {entry['count']}×")
        recommendations.append(
            "- Resolve duplicate ride IDs before any official usage count or billing report."
        )
    else:
        lines.append("  ✓ No duplicate ride IDs detected.")

    # ── Bike Overlaps ────────────────────────────────────────────────────────
    overlaps = anomalies.get("bike_overlaps", {})
    overlap_count = overlaps.get("total_bikes_with_overlap", 0)
    lines.append(_section("2. Bikes with Overlapping Rides"))
    lines.append(f"  Total overlap incidents    : {_fmt_num(overlap_count)}")
    lines.append(f"  Rides checked              : {_fmt_num(overlaps.get('total_rides_checked', 0))}")
    if overlap_count:
        lines.append("  Sample overlapping pairs:")
        for entry in overlaps.get("overlapping_bikes", [])[:8]:
            overlap_min = abs(entry.get("overlap_minutes", 0))
            lines.append(
                f"    {entry['bike_id']}  |  "
                f"{entry['ride1_id']} & {entry['ride2_id']}  |  "
                f"{overlap_min:.1f} min overlap"
            )
        recommendations.append(
            "- Check overlapping bikes for checkout-system sync errors or cloned ride records."
        )
    else:
        lines.append("  ✓ No bike overlap incidents detected.")

    # ── Zero-Duration Rides ──────────────────────────────────────────────────
    zd = anomalies.get("zero_duration", {})
    zd_count = zd.get("count", 0)
    lines.append(_section("3. Zero-Duration Rides (different start/end station)"))
    lines.append(f"  Rides with 0-minute duration : {_fmt_num(zd_count)}")
    if zd_count:
        recommendations.append(
            "- Zero-duration rides with different stations likely represent checkout errors; exclude from usage reporting."
        )
    else:
        lines.append("  ✓ No zero-duration rides with mismatched stations.")

    # ── Strange Distance / Duration ──────────────────────────────────────────
    sdd = anomalies.get("strange_distance_duration", {})
    sdd_count = sdd.get("total_suspicious", 0)
    lines.append(_section("4. Impossible Distance / Duration Combinations"))
    lines.append(f"  Total suspicious records   : {_fmt_num(sdd_count)}")
    if sdd_count:
        high_speed = [r for r in sdd.get("suspicious_combinations", []) if r["type"] == "high_distance_short_duration"]
        low_speed  = [r for r in sdd.get("suspicious_combinations", []) if r["type"] == "low_distance_long_duration"]
        lines.append(f"    High distance, short duration : {len(high_speed)}")
        lines.append(f"    Low distance, long duration   : {len(low_speed)}")
        lines.append("")
        lines.append("  Sample records:")
        for r in sdd.get("suspicious_combinations", [])[:6]:
            lines.append(
                f"    {r['ride_id']}  {r['distance_km']:.2f} km  "
                f"{r['duration_minutes']:.1f} min  "
                f"→ {r['speed_kph']:.1f} km/h  ({r['type']})"
            )
        recommendations.append(
            "- Verify sensor calibration on bikes producing impossible speed values (>60 km/h or <2 km/h)."
        )
    else:
        lines.append("  ✓ No impossible distance/duration pairs found.")

    # ── Station Spikes ───────────────────────────────────────────────────────
    spike = anomalies.get("station_spike", {})
    spiked_start = spike.get("spiked_start_stations", [])
    spiked_end   = spike.get("spiked_end_stations", [])
    lines.append(_section("5. Station Usage Spikes  (>3× average)"))
    lines.append(f"  Average start-station usage : {_fmt_float(spike.get('average_start_usage', 0))} rides")
    lines.append(f"  Average end-station usage   : {_fmt_float(spike.get('average_end_usage',   0))} rides")
    lines.append(f"  Spiked start stations        : {len(spiked_start)}")
    lines.append(f"  Spiked end stations          : {len(spiked_end)}")
    if spiked_start:
        lines.append("\n  Start station spikes:")
        for s in sorted(spiked_start, key=lambda x: -x["count"])[:8]:
            lines.append(f"    {s['station']:<30} {_fmt_num(s['count'])} rides  ({s['ratio']:.1f}× avg)")
    if spiked_end:
        lines.append("\n  End station spikes:")
        for s in sorted(spiked_end, key=lambda x: -x["count"])[:8]:
            lines.append(f"    {s['station']:<30} {_fmt_num(s['count'])} rides  ({s['ratio']:.1f}× avg)")
    if spiked_start or spiked_end:
        recommendations.append(
            "- Investigate spiked stations — cross-check with city-event calendars before attributing to data error."
        )
    else:
        lines.append("  ✓ No station spikes detected.")

    # ── Route Spikes ─────────────────────────────────────────────────────────
    rspike = anomalies.get("route_spike", {})
    spiked_routes = rspike.get("spiked_routes", [])
    lines.append(_section("6. Route Usage Spikes  (>3× average)"))
    lines.append(f"  Total unique routes        : {_fmt_num(rspike.get('total_routes', 0))}")
    lines.append(f"  Average rides per route    : {_fmt_float(rspike.get('average_route_usage', 0))}")
    lines.append(f"  Spiked routes              : {len(spiked_routes)}")
    if spiked_routes:
        lines.append("\n  Top spiked routes:")
        for r in spiked_routes[:10]:
            lines.append(f"    {r['route']:<44} {_fmt_num(r['count'])} rides  ({r['ratio']:.1f}× avg)")
        recommendations.append(
            "- High-frequency routes may reflect commuter demand; consider dedicated docking expansion there."
        )
    else:
        lines.append("  ✓ No route spikes detected.")

    # ── Unknown Stations ─────────────────────────────────────────────────────
    unk = anomalies.get("unknown_stations", {})
    unk_count = unk.get("total_unknown_stations", 0)
    lines.append(_section("7. Records with Missing / Unknown Stations"))
    lines.append(f"  Total records affected     : {_fmt_num(unk_count)}")
    if unk_count:
        unknown_list = unk.get("unknown_station_records", [])
        unique_unknown = sorted(set(s for s in unknown_list if s))
        if unique_unknown:
            lines.append("  Unknown station names encountered:")
            for name in unique_unknown:
                lines.append(f"    • {name}")
        recommendations.append(
            "- Records missing a station name cannot be mapped; review docking-terminal software at affected sites."
        )
    else:
        lines.append("  ✓ All records have valid station values.")

    # ── Bikes with Most Suspicious Records ───────────────────────────────────
    bws = anomalies.get("bikes_with_suspicious", {})
    lines.append(_section("8. Bikes with High Suspicious-Record Counts"))
    lines.append(f"  Bikes with ≥1 suspicious record : {_fmt_num(bws.get('total_bikes_with_suspicious', 0))}")
    top_sb = bws.get("top_suspicious_bikes", [])
    if top_sb:
        lines.append("\n  Top offenders:")
        for entry in top_sb[:10]:
            lines.append(f"    {entry['bike_id']:<20} {entry['suspicious_count']} suspicious record(s)")
        recommendations.append(
            "- Prioritise maintenance checks on the bikes listed above; broken sensors are a likely root cause."
        )
    else:
        lines.append("  ✓ No bikes with disproportionate suspicious records.")

    # ── Stations with Most Suspicious Records ────────────────────────────────
    sws = anomalies.get("stations_with_suspicious", {})
    lines.append(_section("9. Stations with High Suspicious-Record Involvement"))
    top_start_sus = sws.get("top_suspicious_start_stations", [])
    top_end_sus   = sws.get("top_suspicious_end_stations", [])
    if top_start_sus:
        lines.append("  Top suspicious start stations:")
        for entry in top_start_sus[:8]:
            lines.append(f"    {entry['station']:<30} {entry['suspicious_count']} record(s)")
    if top_end_sus:
        lines.append("\n  Top suspicious end stations:")
        for entry in top_end_sus[:8]:
            lines.append(f"    {entry['station']:<30} {entry['suspicious_count']} record(s)")
    if top_start_sus or top_end_sus:
        recommendations.append(
            "- Stations repeatedly appearing in suspicious records may have faulty docking or GPS hardware."
        )
    if not top_start_sus and not top_end_sus:
        lines.append("  ✓ No stations with disproportionate suspicious involvement.")

    # ── Recommended Follow-Up ────────────────────────────────────────────────
    lines.append(_section("Recommended Follow-Up"))
    if recommendations:
        for rec in recommendations:
            lines.append(f"  {rec}")
    else:
        lines.append("  ✓ No significant anomalies detected. Data quality looks healthy.")

    lines.append("\n" + "=" * 60 + "\n  End of Anomaly Report\n" + "=" * 60)
    return "\n".join(lines)


# ── public API ────────────────────────────────────────────────────────────────

def generate_reports(
    analysis: dict,
    anomalies: dict,
    quality_path: str = "reports/bike_ride_quality_report.txt",
    anomaly_path: str = "reports/anomaly_report.txt",
    quiet: bool = False,
) -> None:
    """
    Write both reports to disk and (unless quiet=True) print them to stdout.

    Args:
        analysis   : return value of analyzer.analyze()
        anomalies  : return value of anomaly_detector.analyze_anomalies()
        quality_path: output path for the quality report
        anomaly_path: output path for the anomaly report
        quiet      : suppress stdout printing
    """
    os.makedirs(os.path.dirname(quality_path), exist_ok=True)
    os.makedirs(os.path.dirname(anomaly_path), exist_ok=True)

    quality_text = _build_quality_report(analysis)
    anomaly_text = _build_anomaly_report(anomalies)

    with open(quality_path, "w", encoding="utf-8") as f:
        f.write(quality_text)

    with open(anomaly_path, "w", encoding="utf-8") as f:
        f.write(anomaly_text)

    if not quiet:
        print(quality_text)
        print()
        print(anomaly_text)

    print(f"\nReports written to:\n  {quality_path}\n  {anomaly_path}")