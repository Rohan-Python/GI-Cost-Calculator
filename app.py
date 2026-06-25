"""
GI Cost Calculator — Streamlit Web App (Path B: shadcn + Tailwind)
Author: Rohan Pokale
Version: 1.2 (deprecation-free)
"""
import streamlit as st
import streamlit_shadcn_ui as ui
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* Tighten layout */
        .block-container {padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1400px;}

        /* Hide Streamlit chrome */
        #MainMenu, footer, header {visibility: hidden;}

        /* Headings */
        h1 {color: #1f4e79; font-weight: 800; letter-spacing: -0.02em;}
        h2, h3 {color: #2c5f8d; font-weight: 700;}

        /* Native metric polish */
        [data-testid="stMetric"] {
            background: linear-gradient(135deg, #f0f4f8 0%, #ffffff 100%);
            padding: 18px;
            border-radius: 12px;
            border-left: 5px solid #1f4e79;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }

        /* Sidebar polish */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
        }

        /* Tabs */
        button[data-baseweb="tab"] {
            font-weight: 600 !important;
            font-size: 0.95rem !important;
        }

        /* Sliders accent */
        [data-baseweb="slider"] > div > div > div {background: #1f4e79 !important;}
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
                <span class="bg-white/20 px-3 py-1 rounded-full text-sm font-medium">v1.2 · Path B</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────  SIDEBAR — PROJECT SETUP  ─────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Project Setup")

    region = st.selectbox("Rate library (region)", list_regions(), index=0)
    rates = load_rates(region)
    currency = rates["currency"]

    project_name = st.text_input("Project name", value="New GI Project")
    n_bh = st.number_input("Number of boreholes", min_value=1, value=30, step=1)
    drilling_method = st.selectbox(
        "Drilling method",
        ["percussion", "rotary_open", "rotary_cored"],
        index=2,
        format_func=lambda x: x.replace("_", " ").title(),
    )

    st.markdown("---")
    st.caption(f"📅 Rates last updated: **{rates['last_updated']}**")
    st.caption(f"💰 Currency: **{currency}**")
    st.caption(f"📚 Sources: {len(rates['source_quotes'])} quotes")


# ─────────────────────────  MAIN TABS (shadcn)  ─────────────────────────
selected_tab = ui.tabs(
    options=["📏 Depth Profile", "🔧 Instrumentation", "🧪 In-Situ Tests",
             "⚗️ Lab & Chemical", "📊 Results"],
    default_value="📏 Depth Profile",
    key="main_tabs",
)


# ─────────────────────────  TAB 1 — DEPTH PROFILE  ─────────────────────────
if selected_tab == "📏 Depth Profile":
    st.subheader("Borehole Depth Profile", divider="blue")
    st.caption("Enter the average metres drilled per borehole in each depth band")

    cols = st.columns(5)
    depth_bands = {}
    band_labels = ["0-10", "10-20", "20-30", "30-40", "40-50"]
    defaults = [10.0, 5.0, 0.0, 0.0, 0.0]

    for col, band, default in zip(cols, band_labels, defaults):
        with col:
            depth_bands[band] = st.number_input(
                f"{band} m",
                min_value=0.0, max_value=10.0,
                value=default, step=0.5, key=f"band_{band}",
            )

    avg_total_depth = sum(depth_bands.values())
    total_drilled_m = avg_total_depth * n_bh

    st.write("")

    # KPI cards via shadcn
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

    # Depth-band rate preview (Tailwind card)
    st.markdown("### 💡 Rate Preview for Selected Method")
    band_rates = rates["drilling_per_m"][drilling_method]
    rate_html = "<div class='grid grid-cols-5 gap-3 mt-3'>"
    for band in band_labels:
        rate_html += f"""
        <div class='bg-blue-50 border border-blue-200 rounded-xl p-4 text-center'>
            <div class='text-xs text-blue-700 font-semibold'>{band} m</div>
            <div class='text-2xl font-bold text-blue-900 mt-1'>{band_rates.get(band, '–')}</div>
            <div class='text-xs text-slate-500 mt-1'>{currency}/m</div>
        </div>
        """
    rate_html += "</div>"
    st.markdown(rate_html, unsafe_allow_html=True)


# ─────────────────────────  TAB 2 — INSTRUMENTATION  ─────────────────────────
elif selected_tab == "🔧 Instrumentation":
    st.subheader("Instrumentation Setup", divider="blue")
    st.caption("Specify how many boreholes will be instrumented and which extras are needed")

    col1, col2 = st.columns(2)
    with col1:
        pct_instr = st.slider("% of boreholes instrumented", 0, 100, 10)
        n_instr = round(n_bh * pct_instr / 100)
        ui.metric_card(title="Instrumented BHs", content=str(n_instr),
                       description=f"{pct_instr}% of {n_bh}", key="kpi_instr")

    with col2:
        include_logger = ui.switch(default_checked=False, label="Include data loggers?",
                                   key="logger_switch")
        n_loggers = st.number_input("Number of loggers", 0, 100, 0,
                                    disabled=not include_logger)
        if include_logger:
            ui.metric_card(title="Loggers", content=str(n_loggers),
                           description=f"{currency} {rates['instrumentation']['data_logger_per_nr']:,} each",
                           key="kpi_logger")

    # Store in session_state so Results tab can read it
    st.session_state["n_instr"] = n_instr
    st.session_state["include_logger"] = include_logger
    st.session_state["n_loggers"] = n_loggers


# ─────────────────────────  TAB 3 — IN-SITU TESTS  ─────────────────────────
elif selected_tab == "🧪 In-Situ Tests":
    st.subheader("In-Situ Testing Quantities", divider="blue")
    st.caption("Enter the total number of each in-situ test required")

    in_situ_inputs = {}
    cols = st.columns(2)
    test_list = list(rates["in_situ_tests"].keys())

    for idx, test in enumerate(test_list):
        with cols[idx % 2]:
            label = test.replace("_", " ").title()
            in_situ_inputs[test] = st.number_input(
                f"{label} ({currency} {rates['in_situ_tests'][test]} each)",
                min_value=0, value=0, step=1, key=f"is_{test}",
            )

    st.session_state["in_situ_inputs"] = in_situ_inputs


# ─────────────────────────  TAB 4 — LAB & CHEMICAL  ─────────────────────────
elif selected_tab == "⚗️ Lab & Chemical":
    st.subheader("Laboratory & Chemical Testing", divider="blue")
    st.caption("Use the sliders to auto-populate quantities, or adjust individually")

    st.markdown("#### 🎚️ Auto-fill helpers (samples per borehole)")
    sl1, sl2, sl3 = st.columns(3)
    with sl1:
        spb_classif = st.slider("Classification samples / BH", 0.0, 5.0, 2.0, 0.5)
    with sl2:
        spb_chem = st.slider("Chemical samples / BH", 0.0, 3.0, 1.0, 0.5)
    with sl3:
        spb_rock = st.slider("Rock samples / BH", 0.0, 3.0, 1.0, 0.5)

    auto_classif = int(round(spb_classif * n_bh))
    auto_chem = int(round(spb_chem * n_bh))
    auto_rock = int(round(spb_rock * n_bh))

    st.write("")

    # Classification
    st.markdown("#### 🧬 Classification tests")
    classif_qty = {}
    cols = st.columns(3)
    for i, test in enumerate(rates["classification_tests_per_sample"]):
        with cols[i % 3]:
            classif_qty[test] = st.number_input(
                test.replace("_", " ").title(),
                0, 10000, auto_classif, key=f"cls_{test}",
            )

    # Chemical
    st.markdown("#### ⚗️ Chemical tests")
    chem_qty = {}
    cols = st.columns(3)
    for i, test in enumerate(rates["chemical_tests_per_sample"]):
        with cols[i % 3]:
            chem_qty[test] = st.number_input(
                test.replace("_", " ").title(),
                0, 10000, auto_chem, key=f"chm_{test}",
            )

    # Rock
    st.markdown("#### 🪨 Rock tests")
    rock_qty = {}
    cols = st.columns(3)
    for i, test in enumerate(rates["rock_tests_per_sample"]):
        with cols[i % 3]:
            rock_qty[test] = st.number_input(
                test.replace("_", " ").title(),
                0, 10000, auto_rock, key=f"rk_{test}",
            )

    st.session_state["classif_qty"] = classif_qty
    st.session_state["chem_qty"] = chem_qty
    st.session_state["rock_qty"] = rock_qty


# ─────────────────────────  TAB 5 — RESULTS  ─────────────────────────
elif selected_tab == "📊 Results":
    # Pull stored state with safe defaults
    depth_bands = {b: st.session_state.get(f"band_{b}", 0.0)
                   for b in ["0-10", "10-20", "20-30", "30-40", "40-50"]}
    total_drilled_m = sum(depth_bands.values()) * n_bh

    n_instr = st.session_state.get("n_instr", 0)
    include_logger = st.session_state.get("include_logger", False)
    n_loggers = st.session_state.get("n_loggers", 0)
    in_situ_inputs = st.session_state.get("in_situ_inputs", {})
    classif_qty = st.session_state.get("classif_qty", {})
    chem_qty = st.session_state.get("chem_qty", {})
    rock_qty = st.session_state.get("rock_qty", {})

    # ---- compute ----
    mob = calc.calc_mobilization(n_bh, drilling_method, rates)
    drill = calc.calc_drilling(depth_bands, n_bh, drilling_method, rates)
    back = calc.calc_backfill(total_drilled_m, rates)
    inst = calc.calc_instrumentation(n_instr, include_logger, n_loggers, rates)
    situ = calc.calc_in_situ(in_situ_inputs, rates)
    lab = calc.calc_lab_chemical(chem_qty, classif_qty, rock_qty, rates)
    rep = calc.calc_reporting(rates)

    cat_totals = {
        "Mobilization": mob["TOTAL"],
        "Drilling": drill["TOTAL"],
        "Backfilling": back["TOTAL"],
        "Instrumentation": inst["TOTAL"],
        "In-Situ Testing": situ["TOTAL"],
        "Lab & Chemical": lab["TOTAL"],
        "Reporting": rep["TOTAL"],
    }
    summary = calc.aggregate_costs(cat_totals, n_bh)

    # ---- HERO METRICS ----
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

    # ---- DUAL CHARTS ----
    df = pd.DataFrame({"Category": cat_totals.keys(),
                       "Cost": cat_totals.values()})
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

    # ---- DETAILED BREAKDOWN ----
    st.markdown("### 🔍 Detailed Breakdown")
    breakdown_tab = ui.tabs(
        options=["Mobilization", "Drilling", "Backfilling", "Instrumentation",
                 "In-Situ", "Lab & Chemical", "Reporting"],
        default_value="Mobilization",
        key="breakdown_tabs",
    )
    mapping = {
        "Mobilization": mob, "Drilling": drill, "Backfilling": back,
        "Instrumentation": inst, "In-Situ": situ,
        "Lab & Chemical": lab, "Reporting": rep,
    }
    data = mapping[breakdown_tab]
    df_detail = pd.DataFrame({
        "Item": data.keys(),
        f"Cost ({currency})": [f"{v:,.0f}" for v in data.values()],
    })
    ui.table(data=df_detail, key=f"tbl_{breakdown_tab}")

    st.write("")

    # ---- EXPORT ----
    def to_excel() -> bytes:
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            pd.DataFrame({"Category": cat_totals.keys(),
                          "Cost": cat_totals.values()}).to_excel(
                writer, sheet_name="Summary", index=False)
            for name, d in [("Mobilization", mob), ("Drilling", drill),
                            ("Backfilling", back), ("Instrumentation", inst),
                            ("InSitu", situ), ("Lab", lab),
                            ("Reporting", rep)]:
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
        Built with ❤️ using Streamlit + shadcn/ui + Tailwind CSS
        <br/>GI Cost Calculator v1.2 · © 2026 Rohan Pokale
    </div>
    """,
    unsafe_allow_html=True,
)