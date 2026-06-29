"""
Warehouse Capacity Planner — Streamlit Web App
Run:  streamlit run streamlit_app.py
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import copy, sys, os

sys.path.insert(0, os.path.dirname(__file__))

from config import (
    StorageArea, OrderType,
    StorageSplit, CustomerSplit, KittingSplit,
    ZONE_NAMES, ZONE_FLOW_ORDER,
    DEFAULT_AREAS, DEFAULT_ORDER_TYPES,
)
from engine import WarehouseEngine

st.set_page_config(
    page_title="Warehouse Capacity Planner",
    page_icon="⬡", layout="wide",
    initial_sidebar_state="expanded",
)

ZONE_COLORS = {
    "600": "#4f6ef7", "SMART_BULK": "#7c5cfc",
    "400": "#06b6d4", "300": "#10b981",
    "200": "#f59e0b", "100": "#ef4444",
}

def status_color(pct):
    if pct >= 100: return "#ef4444"
    if pct >= 85:  return "#f59e0b"
    if pct >= 70:  return "#f97316"
    return "#22c55e"

def status_label(pct):
    if pct >= 100: return "🔴 OVER CAPACITY"
    if pct >= 85:  return "🟡 CRITICAL"
    if pct >= 70:  return "🟠 WARNING"
    return "🟢 OK"

if "areas" not in st.session_state:
    st.session_state.areas       = [copy.deepcopy(a) for a in DEFAULT_AREAS]
    st.session_state.order_types = [copy.deepcopy(o) for o in DEFAULT_ORDER_TYPES]

def get_engine():
    return WarehouseEngine(
        areas=[copy.deepcopy(a) for a in st.session_state.areas],
        order_types=[copy.deepcopy(o) for o in st.session_state.order_types],
    )

# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⬡ Warehouse Planner")
    st.markdown("---")
    page = st.radio("Navigate",
        ["📊 Analysis", "🔄 Material flow", "⚙️ Settings"],
        label_visibility="collapsed")
    st.markdown("---")
    st.markdown("**Quick status at x1.0**")
    _snap = get_engine().snapshot(1.0)
    nb, nw = len(_snap.bottlenecks), len(_snap.warnings)
    if nb:   st.error(f"⚠️ {nb} area(s) over capacity")
    elif nw: st.warning(f"△ {nw} area(s) near limit")
    else:    st.success("✓ All areas OK")
    st.markdown("---")
    st.caption("**Zone legend**")
    for zone, name in [("600","Paper"),("SMART_BULK","Smart Bulk"),
                        ("400","Consumables"),("300","Cust. Spec 1"),
                        ("200","Cust. Spec 2"),("100","Final")]:
        c = ZONE_COLORS.get(zone, "#888")
        st.markdown(
            '<span style="display:inline-block;width:10px;height:10px;'
            'border-radius:2px;background:' + c + ';margin-right:6px"></span>'
            '<small>' + zone + ' – ' + name + '</small>',
            unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  MATERIAL FLOW PAGE
# ═══════════════════════════════════════════════════════════════════════════════

if page == "🔄 Material flow":
    st.title("🔄 Material flow")
    st.caption("How material moves through the warehouse — from inbound to final shipment.")

    def make_flow_diagram(engine):
        snap = engine.snapshot(1.0)
        fl   = snap.flow
        fig  = go.Figure()

        # nodes: x, y, label, sublabel, text_color, bg_color, border_color
        nodes = [
            (0.50, 0.95, "Inbound Orders",      "",                  "#a0a8f0", "#1e2235", "#4f6ef7"),
            (0.18, 0.75, "600 - Paper",          "Raw paper storage", "#a0a8f0", "#1a2040", "#4f6ef7"),
            (0.82, 0.75, "400 - Consumables",    "Raw consumables",   "#67d8f0", "#0a2025", "#06b6d4"),
            (0.18, 0.55, "Smart Bulk",           "Paper staging",     "#b8a8f8", "#1e1540", "#7c5cfc"),
            (0.50, 0.55, "300 - Cust. Spec 1",  "Customer area 1",   "#6ee7b7", "#0a2018", "#10b981"),
            (0.82, 0.55, "200 - Cust. Spec 2",  "Customer area 2",   "#fcd34d", "#2a1800", "#f59e0b"),
            (0.50, 0.35, "Kitting (300 path)",  "Custom kits",       "#9ca3af", "#111827", "#6b7280"),
            (0.82, 0.35, "Kitting (200 path)",  "Custom kits",       "#9ca3af", "#111827", "#6b7280"),
            (0.50, 0.10, "100 - Final/Packout", "Ready to ship",     "#fca5a5", "#2a0a0a", "#ef4444"),
        ]
        for x, y, label, sub, tc, bg, bc in nodes:
            body = "<b>" + label + "</b>"
            if sub:
                body = body + "<br><span style='font-size:11px;color:#9ca3af'>" + sub + "</span>"
            fig.add_annotation(
                x=x, y=y, text=body, showarrow=False, align="center",
                font=dict(size=13, color=tc), bgcolor=bg,
                bordercolor=bc, borderwidth=2, borderpad=10,
                xref="paper", yref="paper")

        # arrows: x0, y0, x1, y1, color
        arrows = [
            (0.50, 0.93, 0.18, 0.78, "#4f6ef7"),
            (0.50, 0.93, 0.82, 0.78, "#06b6d4"),
            (0.18, 0.72, 0.18, 0.58, "#7c5cfc"),
            (0.18, 0.52, 0.18, 0.16, "#7c5cfc"),
            (0.18, 0.13, 0.40, 0.13, "#7c5cfc"),
            (0.82, 0.72, 0.50, 0.58, "#10b981"),
            (0.82, 0.72, 0.82, 0.58, "#f59e0b"),
            (0.50, 0.52, 0.50, 0.38, "#10b981"),
            (0.82, 0.52, 0.82, 0.38, "#f59e0b"),
            (0.43, 0.35, 0.43, 0.52, "#6b7280"),
            (0.89, 0.35, 0.89, 0.52, "#6b7280"),
            (0.50, 0.52, 0.47, 0.13, "#10b981"),
            (0.82, 0.52, 0.53, 0.13, "#f59e0b"),
        ]
        for x0, y0, x1, y1, color in arrows:
            fig.add_shape(type="line",
                x0=x0, y0=y0, x1=x1, y1=y1,
                xref="paper", yref="paper",
                line=dict(color=color, width=2))
            fig.add_annotation(
                x=x1, y=y1, ax=0, ay=0,
                xref="paper", yref="paper",
                showarrow=True, arrowhead=2, arrowsize=1.2,
                arrowwidth=2, arrowcolor=color, text="")

        # edge labels: x, y, text, color
        elabels = [
            (0.28, 0.87, "Paper % (Split 1)",      "#4f6ef7"),
            (0.72, 0.87, "Consumable % (Split 1)", "#06b6d4"),
            (0.07, 0.34, "Direct to packout",      "#7c5cfc"),
            (0.61, 0.67, "Cust 1 % (Split 2)",     "#10b981"),
            (0.88, 0.66, "Cust 2 % (Split 2)",     "#f59e0b"),
            (0.57, 0.46, "Kitting % (Split 3)",    "#10b981"),
            (0.88, 0.46, "Kitting % (Split 3)",    "#f59e0b"),
            (0.33, 0.44, "back to 300",             "#6b7280"),
            (0.93, 0.44, "back to 200",             "#6b7280"),
        ]
        for lx, ly, ltxt, lc in elabels:
            fig.add_annotation(
                x=lx, y=ly, text="<i>" + ltxt + "</i>",
                showarrow=False, font=dict(size=10, color=lc),
                xref="paper", yref="paper", align="center")

        # rule labels on left: y, title, detail
        rules = [
            (0.90, "SPLIT 1", "600 vs 400 storage"),
            (0.64, "RULE 2",  "Paper to SmartBulk, direct to 100"),
            (0.57, "SPLIT 2", "300 vs 200 customer"),
            (0.38, "SPLIT 3", "Kitting loop returns to zone"),
            (0.11, "RULE 5",  "All paths converge at 100"),
        ]
        for ry, rtitle, rdetail in rules:
            fig.add_annotation(
                x=-0.01, y=ry,
                text="<b>" + rtitle + "</b><br>"
                     + "<span style='color:#9ca3af;font-size:10px'>" + rdetail + "</span>",
                showarrow=False, font=dict(size=11, color="#6b7280"),
                xref="paper", yref="paper", align="right", xanchor="right")

        # live volume callouts
        fig.add_annotation(
            x=0.50, y=1.02,
            text="Smart Bulk: " + str(int(fl.paper_to_smart_bulk)) + " boxes/day",
            showarrow=False, font=dict(size=11, color="#7c5cfc"),
            xref="paper", yref="paper", align="center")
        fig.add_annotation(
            x=0.70, y=0.63,
            text="Zn300: " + str(int(fl.consumables_to_300))
                 + "  |  Zn200: " + str(int(fl.consumables_to_200)) + " boxes/day",
            showarrow=False, font=dict(size=11, color="#06b6d4"),
            xref="paper", yref="paper", align="center")

        fig.update_layout(
            height=700, margin=dict(l=170, r=20, t=40, b=20),
            paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
            xaxis=dict(visible=False, range=[0, 1]),
            yaxis=dict(visible=False, range=[0, 1]))
        return fig

    st.plotly_chart(make_flow_diagram(get_engine()), use_container_width=True)
    st.markdown("---")

    engine = get_engine()
    snap   = engine.snapshot(1.0)
    fl     = snap.flow

    st.subheader("Live flow volumes at x1.0")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Paper to Smart Bulk",    str(int(fl.paper_to_smart_bulk))  + " boxes/day")
    c2.metric("Consumables total",      str(int(fl.consumables_total))    + " boxes/day")
    c3.metric("Consumables to Zn 300",  str(int(fl.consumables_to_300))   + " boxes/day")
    c4.metric("Consumables to Zn 200",  str(int(fl.consumables_to_200))   + " boxes/day")

    st.markdown("#### Per order type")
    for ot in engine.order_types:
        with st.expander("**" + ot.name + "**", expanded=True):
            r1, r2, r3 = st.columns(3)
            r1.metric("Daily orders",    ot.daily_volume)
            r2.metric("Avg units/order", ot.avg_units_per_order)
            r3.metric("Total units/day", str(int(ot.total_units())))

            st.caption("Split 1 - Storage")
            s1a, s1b = st.columns(2)
            s1a.metric("600 Paper %",        str(int(ot.storage_split.paper_pct))      + "%")
            s1b.metric("400 Consumables %",  str(int(ot.storage_split.consumable_pct)) + "%")

            st.caption("Split 2 - Customer (of the Consumables portion)")
            s2a, s2b = st.columns(2)
            s2a.metric("to Zone 300 %", str(int(ot.customer_split.cust1_pct)) + "%")
            s2b.metric("to Zone 200 %", str(int(ot.customer_split.cust2_pct)) + "%")

            st.caption("Split 3 - Kitting (of 300/200 material)")
            s3a, s3b, s3c = st.columns(3)
            s3a.metric("Direct to packout %", str(int(ot.kitting_split.packout_pct)) + "%")
            s3b.metric("to Kitting %",        str(int(ot.kitting_split.kitting_pct)) + "%")
            kit_boxes = sum(
                ot.boxes_in_area(a, 1.0) * (ot.kitting_split.kitting_pct / 100)
                for a in engine.areas if a.zone in ("300", "200")
            )
            s3c.metric("Kitting boxes/day", str(round(kit_boxes, 1)))

    st.markdown("---")
    st.markdown("#### Flow rules reference")
    st.markdown("""
| Rule | Logic |
|---|---|
| **Split 1 - Storage** | 600% + 400% = 100% — where the order draws its units from |
| **Rule 2 - Paper path** | 600 to Smart Bulk (same volume staged) then direct to 100 Final — bypasses 300/200 |
| **Split 2 - Customer** | 300% + 200% = 100% — how the 400 consumable portion divides between customers |
| **Split 3 - Kitting** | Packout% + Kitting% = 100% — how 300/200 material routes onward |
| **Rule 4 - Kitting loop** | Kitting returns to same zone (300 or 200) then flows to 100 normally |
| **Rule 5 - Final** | All paths converge at 100 Final/Packout before shipping |
    """)


# ═══════════════════════════════════════════════════════════════════════════════
#  SETTINGS PAGE
# ═══════════════════════════════════════════════════════════════════════════════

if page == "⚙️ Settings":
    st.title("⚙️ Settings")
    st.caption("Update area dimensions and order type splits, then click Save.")

    st.subheader("Storage areas")
    area_updates = {}
    cols = st.columns(2)
    for i, area in enumerate(st.session_state.areas):
        with cols[i % 2]:
            zone_str = "Staging" if area.is_staging else "Zone " + area.zone
            with st.expander("**" + area.name + "** — " + zone_str, expanded=True):
                v_vol = st.number_input("Volume (cu ft)",       value=float(area.volume_cuft),       step=100.0, key="vol_" + area.id)
                v_box = st.number_input("Avg box size (cu ft)", value=float(area.avg_box_size_cuft), step=0.1,   key="box_" + area.id)
                v_eff = st.number_input("Efficiency (0-1)",     value=float(area.efficiency),        step=0.01,  min_value=0.1, max_value=1.0, key="eff_" + area.id)
                v_upb = st.number_input("Units per box",        value=float(area.units_per_box),     step=1.0,   min_value=1.0, key="upb_" + area.id)
                cap_boxes = int((v_vol * v_eff) / v_box) if v_box > 0 else 0
                cap_units = int(cap_boxes * v_upb)
                st.info("Capacity: " + str(cap_boxes) + " boxes  |  " + str(cap_units) + " units")
                area_updates[area.id] = dict(
                    volume_cuft=v_vol, avg_box_size_cuft=v_box,
                    efficiency=v_eff,  units_per_box=v_upb)

    st.markdown("---")
    st.subheader("Order types")
    st.caption("Configure volume and three independent splits for each order type.")

    order_updates = {}
    for ot in st.session_state.order_types:
        with st.expander("**" + ot.name + "**", expanded=True):
            c1, c2 = st.columns(2)
            v_vol = c1.number_input("Daily volume (orders)", value=int(ot.daily_volume),        step=1, min_value=1, key="ovol_" + ot.id)
            v_qty = c2.number_input("Avg units / order",     value=int(ot.avg_units_per_order), step=1, min_value=1, key="oqty_" + ot.id)

            st.markdown("---")
            st.markdown("**Split 1 - Storage** | 600% + 400% must total 100%")
            s1c1, s1c2 = st.columns(2)
            v_paper = s1c1.number_input("600 Paper %",       value=float(ot.storage_split.paper_pct),      step=1.0, min_value=0.0, max_value=100.0, key="paper_" + ot.id)
            v_cons  = s1c2.number_input("400 Consumables %", value=float(ot.storage_split.consumable_pct), step=1.0, min_value=0.0, max_value=100.0, key="cons_"  + ot.id)
            s1t = v_paper + v_cons
            if abs(s1t - 100) > 0.5:
                st.warning("Storage split totals " + str(int(s1t)) + "% — must be 100%")
            else:
                st.success("Storage split OK: " + str(int(v_paper)) + "% Paper + " + str(int(v_cons)) + "% Consumables = 100%")

            st.markdown("---")
            st.markdown("**Split 2 - Customer** | 300% + 200% must total 100%  *(applied to Consumables portion only)*")
            s2c1, s2c2 = st.columns(2)
            v_c1 = s2c1.number_input("to Zone 300 %", value=float(ot.customer_split.cust1_pct), step=1.0, min_value=0.0, max_value=100.0, key="c1_" + ot.id)
            v_c2 = s2c2.number_input("to Zone 200 %", value=float(ot.customer_split.cust2_pct), step=1.0, min_value=0.0, max_value=100.0, key="c2_" + ot.id)
            s2t = v_c1 + v_c2
            if abs(s2t - 100) > 0.5:
                st.warning("Customer split totals " + str(int(s2t)) + "% — must be 100%")
            else:
                st.success("Customer split OK: " + str(int(v_c1)) + "% Zone 300 + " + str(int(v_c2)) + "% Zone 200 = 100%")

            st.markdown("---")
            st.markdown("**Split 3 - Kitting** | Packout% + Kitting% must total 100%  *(of 300/200 material)*")
            s3c1, s3c2 = st.columns(2)
            v_pack = s3c1.number_input("Direct to packout %", value=float(ot.kitting_split.packout_pct), step=1.0, min_value=0.0, max_value=100.0, key="pack_" + ot.id)
            v_kit  = s3c2.number_input("to Kitting %",        value=float(ot.kitting_split.kitting_pct), step=1.0, min_value=0.0, max_value=100.0, key="kit_"  + ot.id)
            s3t = v_pack + v_kit
            if abs(s3t - 100) > 0.5:
                st.warning("Kitting split totals " + str(int(s3t)) + "% — must be 100%")
            else:
                st.success("Kitting split OK: " + str(int(v_pack)) + "% direct + " + str(int(v_kit)) + "% kitting = 100%")

            order_updates[ot.id] = dict(
                daily_volume=v_vol, avg_units_per_order=v_qty,
                paper_pct=v_paper, consumable_pct=v_cons,
                cust1_pct=v_c1,    cust2_pct=v_c2,
                packout_pct=v_pack, kitting_pct=v_kit)

    st.markdown("---")
    if st.button("Save & recalculate", type="primary", use_container_width=True):
        area_map = {a.id: a for a in st.session_state.areas}
        for aid, u in area_updates.items():
            a = area_map[aid]
            a.volume_cuft       = u["volume_cuft"]
            a.avg_box_size_cuft = u["avg_box_size_cuft"]
            a.efficiency        = u["efficiency"]
            a.units_per_box     = u["units_per_box"]

        ot_map = {o.id: o for o in st.session_state.order_types}
        for oid, u in order_updates.items():
            ot = ot_map[oid]
            ot.daily_volume        = u["daily_volume"]
            ot.avg_units_per_order = u["avg_units_per_order"]
            ot.storage_split  = StorageSplit(paper_pct=u["paper_pct"],      consumable_pct=u["consumable_pct"])
            ot.customer_split = CustomerSplit(cust1_pct=u["cust1_pct"],     cust2_pct=u["cust2_pct"])
            ot.kitting_split  = KittingSplit(packout_pct=u["packout_pct"],  kitting_pct=u["kitting_pct"])

        st.success("Settings saved.")
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
#  ANALYSIS PAGE
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "📊 Analysis":
    st.title("📊 Analysis")

    multiplier = st.slider(
        "Volume multiplier", min_value=1.0, max_value=10.0,
        value=1.0, step=0.1, format="x%.1f")

    engine = get_engine()
    snap   = engine.snapshot(multiplier=multiplier)

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Capacity (boxes)", str(snap.total_capacity_boxes))
    k2.metric("Capacity (units)", str(snap.total_capacity_units))
    k3.metric("Load (boxes)",     str(int(snap.total_load_boxes)))
    k4.metric("Overall util.",    str(round(snap.overall_utilization, 1)) + "%")
    k5.metric("Over capacity",    len(snap.bottlenecks))
    k6.metric("Near limit",       len(snap.warnings))

    for a in snap.bottlenecks:
        st.error("BOTTLENECK — " + a.area.name + " at " + str(round(a.utilization_pct, 1)) + "%")
    for a in snap.warnings:
        st.warning("WARNING — " + a.area.name + " at " + str(round(a.utilization_pct, 1)) + "%")
    if not snap.bottlenecks and not snap.warnings:
        st.success("All areas within capacity at x" + str(multiplier))

    st.markdown("---")
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Overview", "Area detail", "Growth table", "Bottlenecks", "BOM breakdown"])

    with tab1:
        st.subheader("Area utilization")
        area_names = [a.area.name for a in snap.areas]
        utils      = [round(a.utilization_pct, 1) for a in snap.areas]
        colors     = [status_color(p) for p in utils]

        fig = go.Figure(go.Bar(
            y=area_names, x=utils, orientation="h",
            marker_color=colors,
            text=[str(p) + "%" for p in utils], textposition="outside",
            customdata=list(zip(
                [round(a.load_boxes, 0) for a in snap.areas],
                [a.capacity_boxes       for a in snap.areas],
                [round(a.load_units, 0) for a in snap.areas],
                [a.capacity_units       for a in snap.areas],
                [a.area.units_per_box   for a in snap.areas],
            )),
            hovertemplate=(
                "<b>%{y}</b><br>Util: %{x:.1f}%<br>"
                "Boxes: %{customdata[0]:,.0f} / %{customdata[1]:,}<br>"
                "Units: %{customdata[2]:,.0f} / %{customdata[3]:,}<br>"
                "Units/box: %{customdata[4]:.0f}<extra></extra>"
            ),
        ))
        fig.add_vline(x=85,  line_dash="dot", line_color="#f59e0b", annotation_text="85%")
        fig.add_vline(x=100, line_dash="dot", line_color="#ef4444", annotation_text="100%")
        fig.update_layout(
            xaxis=dict(title="Utilization %", range=[0, 115]),
            yaxis=dict(autorange="reversed"),
            height=320, margin=dict(l=10, r=60, t=20, b=40),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

        rows = []
        for a in snap.areas:
            rows.append({
                "Area":         a.area.name,
                "Zone":         a.area.zone,
                "Units/box":    int(a.area.units_per_box),
                "Load (boxes)": str(int(a.load_boxes)),
                "Cap (boxes)":  str(a.capacity_boxes),
                "Load (units)": str(int(a.load_units)),
                "Cap (units)":  str(a.capacity_units),
                "Util %":       str(round(a.utilization_pct, 1)) + "%",
                "Status":       status_label(a.utilization_pct),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.subheader("Zone summary")
        zone_df = engine.zone_summary(multiplier)
        zcols = st.columns(len(zone_df))
        for i, (_, row) in enumerate(zone_df.iterrows()):
            pct = row["utilization_pct"]
            zc  = ZONE_COLORS.get(row["zone_code"], "#888")
            with zcols[i]:
                st.markdown(
                    "<div style='text-align:center;padding:10px;border:1px solid #2e3250;"
                    "border-radius:10px;border-left:4px solid " + zc + "'>"
                    "<div style='font-size:11px;color:#6b7280'>Zone " + str(row["zone_code"]) + "</div>"
                    "<div style='font-weight:600;font-size:12px'>" + str(row["zone_name"]) + "</div>"
                    "<div style='font-size:22px;font-weight:700;color:" + status_color(pct) + "'>" + str(pct) + "%</div>"
                    "<div style='font-size:11px;color:#6b7280'>" + str(row["capacity_boxes"]) + " box cap</div>"
                    "</div>", unsafe_allow_html=True)

    with tab2:
        st.subheader("Area detail — order contributions")
        for a in snap.areas:
            with st.expander(
                a.area.name + " — " + str(round(a.utilization_pct, 1)) + "%  |  "
                + str(int(a.load_boxes)) + "/" + str(a.capacity_boxes) + " boxes  |  "
                + str(int(a.load_units)) + "/" + str(a.capacity_units) + " units  |  "
                + str(int(a.area.units_per_box)) + " u/box  " + status_label(a.utilization_pct),
                expanded=True):
                st.progress(min(a.utilization_pct / 100, 1.0))
                if a.contributing_orders:
                    rows = []
                    for oid, boxes in sorted(
                        a.contributing_orders.items(), key=lambda x: x[1], reverse=True):
                        rows.append({
                            "Order":     oid,
                            "Boxes":     str(round(boxes, 1)),
                            "Units":     str(int(boxes * a.area.units_per_box)),
                            "% of area": str(round(boxes / a.load_boxes * 100, 1)) + "%" if a.load_boxes else "—",
                        })
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                else:
                    st.caption("No orders currently load this area.")

    with tab3:
        st.subheader("Growth table")
        df = engine.growth_table(max_multiplier=10.0, steps=18)
        pivot = df.pivot_table(
            index="multiplier", columns="area",
            values="utilization_pct", aggfunc="first").reset_index()
        area_names_list = [a.name for a in engine.areas]

        fig3 = go.Figure(data=go.Heatmap(
            z=[[row.get(n, 0) for n in area_names_list] for _, row in pivot.iterrows()],
            x=area_names_list,
            y=["x" + str(round(row["multiplier"], 1)) for _, row in pivot.iterrows()],
            colorscale=[[0,"#1a3a2a"],[0.70,"#22c55e"],[0.85,"#f59e0b"],[1,"#ef4444"]],
            zmin=0, zmax=110,
            text=[[str(int(row.get(n, 0))) + "%" for n in area_names_list] for _, row in pivot.iterrows()],
            texttemplate="%{text}",
            hovertemplate="Area: %{x}<br>Mult: %{y}<br>Util: %{z:.1f}%<extra></extra>",
        ))
        fig3.update_layout(height=500, margin=dict(l=10,r=10,t=20,b=10),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(tickangle=-30))
        st.plotly_chart(fig3, use_container_width=True)

        def color_cell(val):
            try:
                v = float(str(val).replace("%", ""))
                if v >= 100: return "background-color:#7f1d1d;color:#fca5a5"
                if v >= 85:  return "background-color:#78350f;color:#fde68a"
                if v >= 70:  return "background-color:#431407;color:#fed7aa"
                return "background-color:#052e16;color:#86efac"
            except:
                return ""

        dp = pivot.copy()
        dp["multiplier"] = dp["multiplier"].apply(lambda x: "x" + str(round(x, 1)))
        dp = dp.rename(columns={"multiplier": "Mult."})
        for col in area_names_list:
            if col in dp.columns:
                dp[col] = dp[col].apply(lambda x: str(int(x)) + "%")
        st.dataframe(dp.style.map(color_cell, subset=area_names_list),
                     use_container_width=True, hide_index=True)

    with tab4:
        st.subheader("Bottleneck sequence")
        seq_100 = engine.bottleneck_sequence(threshold_pct=100.0, max_mult=20.0)
        seq_85  = engine.bottleneck_sequence(threshold_pct=85.0,  max_mult=20.0)

        if not seq_100:
            st.success("No areas hit 100% within x20 volume.")
        else:
            for rank, (mult, area_name, _) in enumerate(seq_100, 1):
                icon = "🔴" if rank == 1 else "🟡" if rank == 2 else "🟠"
                note = " — Address first" if rank == 1 else ""
                st.markdown(
                    "#" + str(rank) + " " + icon + " **" + area_name
                    + "** hits capacity at **x" + str(mult) + "**" + note)

        st.markdown("---")
        st.subheader("85% warning threshold")
        if seq_85:
            st.dataframe(
                pd.DataFrame([{"Area": n, "Reaches 85% at": "x" + str(m)} for m, n, _ in seq_85]),
                use_container_width=True, hide_index=True)
            fig4 = go.Figure()
            for mult, name, _ in reversed(seq_85):
                fig4.add_trace(go.Bar(
                    y=[name], x=[mult], orientation="h",
                    marker_color=status_color(85),
                    text=["x" + str(mult)], textposition="outside",
                    showlegend=False))
            fig4.add_vline(x=multiplier, line_dash="dash", line_color="#4f6ef7",
                           annotation_text="Current x" + str(multiplier))
            fig4.update_layout(
                xaxis=dict(title="Multiplier", range=[0, 22]),
                yaxis=dict(autorange="reversed"),
                height=280, margin=dict(l=10,r=60,t=40,b=40),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                barmode="overlay")
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.success("No areas reach 85% within x20 volume.")

    with tab5:
        st.subheader("BOM breakdown")
        bom_df = engine.order_bom_summary(multiplier)
        if not bom_df.empty:
            fig5 = px.bar(
                bom_df, x="order", y="boxes", color="zone_name", barmode="group",
                labels={"boxes":"Boxes/day","order":"Order type","zone_name":"Zone"},
                title="Daily boxes by zone and order type",
                color_discrete_map={
                    ZONE_NAMES["600"]: ZONE_COLORS["600"],
                    ZONE_NAMES["400"]: ZONE_COLORS["400"],
                    ZONE_NAMES["300"]: ZONE_COLORS["300"],
                    ZONE_NAMES["200"]: ZONE_COLORS["200"],
                })
            fig5.update_layout(height=320, margin=dict(l=10,r=10,t=40,b=40),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig5, use_container_width=True)

            disp = bom_df[["order_name","zone_name","pct_of_total","units","units_per_box","boxes"]].copy()
            disp.columns = ["Order","Zone","% of total","Units/day","Units per box","Boxes/day"]
            st.dataframe(disp, use_container_width=True, hide_index=True)
