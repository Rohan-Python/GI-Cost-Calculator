"""
GI Cost Calculator — Streamlit Web App
Author: Rohan Pokale
Version: 1.4 (native st.tabs → bulletproof auto-save)
"""
import streamlit as st
import streamlit_shadcn_ui as ui
import pandas as pd
import plotly.express as px
from io import BytesIO

from modules.rates_loader import load_rates, list_regions
from modules import calculator as calc


# ─────────────────────────  PAGE CONFIG  ─────────────────────────
st.set_page_config(
    page_title="GI Cost Calculator",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─────────────────────────  TAILWIND + CUSTOM CSS  ─────────────────────────
st.markdown(
    """
    https://cdn.tailwindcss.com
    <style>
        .block-container {padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1400px;}
        #MainMenu, footer {visibility: hidden;}
        h1 {color: #1f4e79; font-weight: 800; letter-spacing: -0.02em;}
        h2, h3 {color: #2c5f8d; font-weight: 700;}
        [data-testid="stMetric"] {
            background: linear-gradient(135deg, #f0f4f8 0%, #ffffff 100%);
            padding: 18px; border-radius: 12px;
            border-left: 5px solid #1f4e79;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
        }
        button[data-baseweb="tab"] {
            font-weight: 600 !important;
            font-size: 0.95rem !important;
        }
        /* Highlight active tab */
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #1f4e79 !important;
            border-bottom: 3px solid #1f4e79 !important;
        }
        [data-baseweb="slider"] > div > div > div {background: #1f4e79 !important;}
        button[kind="header"] {
            background: #1f4e79 !important; color: white !important;
            border-radius: 8px !important; padding: 6px !important;
        }
        button[kind="header"]:hover {background: #2c5f8d !important;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────  HEADER  ─────────────────────────
st.markdown(
    """
    <div class="bg-gradient-to-r from-blue-900 via-blue-700 to-indigo-700 text-white p-8 rounded-2xl shadow-xl mb-6">
        <div class="flex items-center justify-between">
            <div>
                <h1 class="text-4xl font-extrabold tracking-tight text-white">🛠️ GI Cost Calculator</h1>
                <p class="text-blue-100 mt-2 text-lg">Parametric Ground Investigation cost estimator — depth-banded model</p>
            </div>
            <div class="text-right">
                <span class="bg-white/20 px-3 py-1 rounded-full text-sm font-medium">v1.4 · Persistent</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


AUTOSAVE_BADGE = """
<div style="display:inline-flex; align-items:center; gap:6px;
            background:#ecfdf5; border:1px solid #a7f3d0; color:#047857;
            padding:4px 12px; border-radius:9999px; font-size:0.75rem;
            font-weight:600; margin-bottom:12px;">
    <span style="width:8px; height:8px; background:#10b981; border-radius:50%;"></span>
    Auto-saved
</div>
"""


# ─────────────────────────  SIDEBAR  ─────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Project Setup")

    region = st.selectbox("Rate library (region)", list_regions(), index=0, key="region")
    rates = load_rates(region)
    currency = rates["currency"]

    project_name = st.text_input("Project name", value="New GI Project", key="project_name")
    n_bh = st.number_input("Number of boreholes", min_value=1, value=30, step=1, key="n_bh")
    drilling_method = st.selectbox(
        "Drilling method",
        ["percussion", "rotary_open", "rotary_cored"],
        index=2,
        format_func=lambda x: x.replace("_", " ").title(),
        key="drilling_method",
    )

    st.markdown("---")
    if st.button("🔄 Reset all inputs", width="stretch"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

    st.markdown("---")
    st.caption(f"📅 Rates last updated: **{rates['last_updated']}**")
    st.caption(f"💰 Currency: **{currency}**")
    st.caption(f"📚 Sources: {len(rates['source_quotes'])} quotes")


# ─────────────────────────  NATIVE TABS (all render simultaneously)  ─────────────────────────
tab_depth, tab_inst, tab_situ, tab_lab, tab_results = st.tabs(
    ["📏 Depth Profile", "🔧 Instrumentation", "🧪 In-Situ Tests",
     "⚗️ Lab & Chemical", "📊 Results"]
)


# ─────────────────────────  TAB 1 — DEPTH PROFILE  ─────────────────────────
with tab_depth:
    st.subheader("Borehole Depth Profile", divider="blue")
    st.markdown(AUTOSAVE_BADGE, unsafe_allow_html=True)
    st.caption("Enter the average metres drilled per borehole in each depth band")

    cols = st.columns(5)
    band_labels = ["0-10", "10-20", "20-30", "30-40", "40-50"]
    defaults = [10.0, 5.0, 0.0, 0.0, 0.0]

    for col, band, default in zip(cols, band_labels, defaults):
        with col:
            st.number_input(
                f"{band} m", min_value=0.0, max_value=10.0,
                value=default, step=0.5, key=f"band_{band}",
            )

    depth_bands = {b: st.session_state[f"band_{b}"] for b in band_labels}
    avg_total_depth = sum(depth_bands.values())
    total_drilled_m = avg_total_depth * n_bh

    st.write("")
    c1, c2, c3 = st.columns(3)
    with c1:
        ui.metric_card(title="Avg Depth / BH", content=f"{avg_total_depth:.1f} m",
                       description="Across all bands", key="kpi_depth")
    with c2:
        ui.metric_card(title="Total Drilled", content=f"{total_drilled_m:,.0f} m",
                       description=f"For {n_bh} boreholes", key="kpi_total_m")
    with c3:
        ui.metric_card(title="Drilling Method", content=drilling_method.replace("_", " ").title(),
                       description="Affects rate band", key="kpi_method")

    st.markdown("### 💡 Rate Preview for Selected Method")
    band_rates = rates["drilling_per_m"][drilling_method]
    rate_html = "<div class='grid grid-cols-5 gap-3 mt-3'>"
    for band in band_labels:
        rate_html += f"""
        <div class='bg-blue-50 border border-blue-200 rounded-xl p-4 text-center'>
            <div class='text-xs text-blue-700 font-semibold'>{band} m</div>
            <div class='text-2xl font-bold text-blue-900 mt-1'>{band_rates.get(band, '–')}</div>
            <div class='text-xs text-slate-500 mt-1'>{currency}/m</div>
        </div>"""
    rate_html += "</div>"
    st.markdown(rate_html, unsafe_allow_html=True)


# ─────────────────────────  TAB 2 — INSTRUMENTATION  ─────────────────────────
with tab_inst:
    st.subheader("Instrumentation Setup", divider="blue")
    st.markdown(AUTOSAVE_BADGE, unsafe_allow_html=True)
    st.caption("Specify how many boreholes will be instrumented and which extras are needed")

    col1, col2 = st.columns(2)
    with col1:
        pct_instr = st.slider("% of boreholes instrumented", 0, 100, value=10, key="pct_instr")
        n_instr = round(n_bh * pct_instr / 100)
        ui.metric_card(title="Instrumented BHs", content=str(n_instr),
                       description=f"{pct_instr}% of {n_bh}", key="kpi_instr")

    with col2:
        include_logger = st.toggle("Include data loggers?", value=False, key="logger_switch")
        n_loggers = st.number_input("Number of loggers", 0, 100, value=0,
                                    disabled=not include_logger, key="n_loggers")
        if include_logger:
            ui.metric_card(title="Loggers", content=str(n_loggers),
                           description=f"{currency} {rates['instrumentation']['data_logger_per_nr']:,} each",
                           key="kpi_logger")


# ─────────────────────────  TAB 3 — IN-SITU TESTS  ─────────────────────────
with tab_situ:
    st.subheader("In-Situ Testing Quantities", divider="blue")
    st.markdown(AUTOSAVE_BADGE, unsafe_allow_html=True)
    st.caption("Enter the total number of each in-situ test required")

    cols = st.columns(2)
    test_list = list(rates["in_situ_tests"].keys())

    for idx, test in enumerate(test_list):
        with cols[idx % 2]:
            label = test.replace("_", " ").title()
            st.number_input(
                f"{label} ({currency} {rates['in_situ_tests'][test]} each)",
                min_value=0, value=0, step=1, key=f"is_{test}",
            )

    in_situ_inputs = {test: st.session_state[f"is_{test}"] for test in test_list}


# ─────────────────────────  TAB 4 — LAB & CHEMICAL  ─────────────────────────
with tab_lab:
    st.subheader("Laboratory & Chemical Testing", divider="blue")
    st.markdown(AUTOSAVE_BADGE, unsafe_allow_html=True)
    st.caption("Use the sliders to auto-populate quantities, or adjust individually")

    st.markdown("#### 🎚️ Auto-fill helpers (samples per borehole)")
    sl1, sl2, sl3 = st.columns(3)
    with sl1:
        spb_classif = st.slider("Classification samples / BH", 0.0, 5.0, value=2.0, step=0.5, key="spb_classif")
    with sl2:
        spb_chem = st.slider("Chemical samples / BH", 0.0, 3.0, value=1.0, step=0.5, key="spb_chem")
    with sl3:
        spb_rock = st.slider("Rock samples / BH", 0.0, 3.0, value=1.0, step=0.5, key="spb_rock")

    auto_classif = int(round(spb_classif * n_bh))
    auto_chem = int(round(spb_chem * n_bh))
    auto_rock = int(round(spb_rock * n_bh))

    st.write("")

    st.markdown("#### 🧬 Classification tests")
    cols = st.columns(3)
    for i, test in enumerate(rates["classification_tests_per_sample"]):
        with cols[i % 3]:
            st.number_input(test.replace("_", " ").title(), 0, 10000,
                            value=auto_classif, key=f"cls_{test}")

    st.markdown("#### ⚗️ Chemical tests")
    cols = st.columns(3)
    for i, test in enumerate(rates["chemical_tests_per_sample"]):
        with cols[i % 3]:
            st.number_input(test.replace("_", " ").title(), 0, 10000,
                            value=auto_chem, key=f"chm_{test}")

    st.markdown("#### 🪨 Rock tests")
    cols = st.columns(3)
    for i, test in enumerate(rates["rock_tests_per_sample"]):
        with cols[i % 3]:
            st.number_input(test.replace("_", " ").title(), 0, 10000,
                            value=auto_rock, key=f"rk_{test}")

    classif_qty = {t: st.session_state[f"cls_{t}"] for t in rates["classification_tests_per_sample"]}
    chem_qty    = {t: st.session_state[f"chm_{t}"] for t in rates["chemical_tests_per_sample"]}
    rock_qty    = {t: st.session_state[f"rk_{t}"]  for t in rates["rock_tests_per_sample"]}


# ─────────────────────────  TAB 5 — RESULTS  ─────────────────────────
with tab_results:
    # Pull everything from session_state — guaranteed alive because all tabs render
    depth_bands = {b: st.session_state.get(f"band_{b}", 0.0)
                   for b in ["0-10", "10-20", "20-30", "30-40", "40-50"]}
    total_drilled_m = sum(depth_bands.values()) * n_bh

    n_instr = round(n_bh * st.session_state.get("pct_instr", 0) / 100)
    include_logger = st.session_state.get("logger_switch", False)
    n_loggers = st.session_state.get("n_loggers", 0)

    in_situ_inputs = {t: st.session_state.get(f"is_{t}", 0) for t in rates["in_situ_tests"]}
    classif_qty = {t: st.session_state.get(f"cls_{t}", 0) for t in rates["classification_tests_per_sample"]}
    chem_qty    = {t: st.session_state.get(f"chm_{t}", 0) for t in rates["chemical_tests_per_sample"]}
    rock_qty    = {t: st.session_state.get(f"rk_{t}", 0)  for t in rates["rock_tests_per_sample"]}

    # ---- compute ----
    mob   = calc.calc_mobilization(n_bh, drilling_method, rates)
    drill = calc.calc_drilling(depth_bands, n_bh, drilling_method, rates)
    back  = calc.calc_backfill(total_drilled_m, rates)
    inst  = calc.calc_instrumentation(n_instr, include_logger, n_loggers, rates)
    situ  = calc.calc_in_situ(in_situ_inputs, rates)
    lab   = calc.calc_lab_chemical(chem_qty, classif_qty, rock_qty, rates)
    rep   = calc.calc_reporting(rates)

    cat_totals = {
        "Mobilization": mob["TOTAL"], "Drilling": drill["TOTAL"],
        "Backfilling": back["TOTAL"], "Instrumentation": inst["TOTAL"],
        "In-Situ Testing": situ["TOTAL"], "Lab & Chemical": lab["TOTAL"],
        "Reporting": rep["TOTAL"],
    }
    summary = calc.aggregate_costs(cat_totals, n_bh)

    st.subheader("Cost Summary", divider="blue")
    st.caption(f"Estimate for {project_name}")

    c1, c2, c3 = st.columns(3)
    with c1:
        ui.metric_card(title="💰 Total Project Cost",
                       content=f"{currency} {summary['grand_total']:,.0f}",
                       description=f"All {n_bh} boreholes", key="r_total")
    with c2:
        ui.metric_card(title="📍 Per Borehole",
                       content=f"{currency} {summary['per_borehole']:,.0f}",
                       description="Average all-in", key="r_perbh")
    with c3:
        ui.metric_card(title="📏 Total Drilled",
                       content=f"{total_drilled_m:,.0f} m",
                       description=f"{drilling_method.replace('_', ' ').title()}",
                       key="r_drilled")

    st.write("")

    df = pd.DataFrame({"Category": cat_totals.keys(), "Cost": cat_totals.values()})
    df = df[df["Cost"] > 0].sort_values("Cost", ascending=False)

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        fig_pie = px.pie(df, names="Category", values="Cost", hole=0.5,
                         color_discrete_sequence=px.colors.sequential.Blues_r,
                         title="Cost distribution")
        fig_pie.update_layout(margin=dict(t=40, b=10, l=10, r=10),
                              legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig_pie, width="stretch")

    with chart_col2:
        fig_bar = px.bar(df, x="Cost", y="Category", orientation="h",
                         color="Cost", color_continuous_scale="Blues",
                         title="Cost by category")
        fig_bar.update_layout(margin=dict(t=40, b=10, l=10, r=10),
                              yaxis={"categoryorder": "total ascending"},
                              coloraxis_showscale=False)
        st.plotly_chart(fig_bar, width="stretch")

    st.markdown("### 🔍 Detailed Breakdown")
    breakdown_choice = st.selectbox(
        "Select category to view breakdown",
        ["Mobilization", "Drilling", "Backfilling", "Instrumentation",
         "In-Situ", "Lab & Chemical", "Reporting"],
        key="breakdown_choice",
    )
    mapping = {
        "Mobilization": mob, "Drilling": drill, "Backfilling": back,
        "Instrumentation": inst, "In-Situ": situ,
        "Lab & Chemical": lab, "Reporting": rep,
    }
    data = mapping[breakdown_choice]
    df_detail = pd.DataFrame({
        "Item": data.keys(),
        f"Cost ({currency})": [f"{v:,.0f}" for v in data.values()],
    })
    st.dataframe(df_detail, hide_index=True, width="stretch")

    st.write("")

    def to_excel() -> bytes:
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            pd.DataFrame({"Category": cat_totals.keys(),
                          "Cost": cat_totals.values()}).to_excel(
                writer, sheet_name="Summary", index=False)
            for name, d in [("Mobilization", mob), ("Drilling", drill),
                            ("Backfilling", back), ("Instrumentation", inst),
                            ("InSitu", situ), ("Lab", lab), ("Reporting", rep)]:
                pd.DataFrame({"Item": d.keys(), "Cost": d.values()}).to_excel(
                    writer, sheet_name=name[:31], index=False)
        return buf.getvalue()

    st.markdown(
        """
        <div class="bg-gradient-to-r from-emerald-500 to-teal-600 text-white p-5 rounded-xl mt-4">
            <h3 class="text-lg font-bold text-white">✅ Estimate ready</h3>
            <p class="text-emerald-50 text-sm">Download the full breakdown as an Excel workbook below.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.download_button(
        "📥 Download estimate as Excel",
        data=to_excel(),
        file_name=f"{project_name.replace(' ', '_')}_GI_estimate.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
    )


# ─────────────────────────  FOOTER  ─────────────────────────
st.write("")
st.write("")
st.markdown(
    """
    <div class="text-center text-slate-500 text-sm mt-8 pb-4">
        Built with ❤️ using Streamlit + Tailwind CSS
        <br/>GI Cost Calculator v1.4 · © 2026 Rohan Pokale
    </div>
    """,
    unsafe_allow_html=True,
)