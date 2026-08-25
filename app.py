from pathlib import Path
import os

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_folium import st_folium

from src.ingestion import load_tabular, normalize_column_names
from src.schema import suggest_mapping, apply_mapping
from src.quality import quality_audit, completeness_table
from src.transform import build_analysis_dataset
from src.analytics import (
    rapid_indicators,
    categorical_profile,
    completeness_summary,
)
from src.reporting import build_brief
from src.charts import (
    epidemic_curve_figure,
    weekly_curve_figure,
    place_figure,
    age_figure,
    sex_figure,
    outcome_figure,
)
from src.constants import CANONICAL_FIELDS
from src.maps import internal_case_map, briefing_aggregate_map
from src.ai_interpretation import interpret_surveillance_results
from src.auth import (
    init_db,
    authenticate,
    can,
    log_event,
    list_users,
    list_audit,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="EpiFlow v2 | Surveillance Intelligence",
    page_icon="🧬",
    layout="wide",
)

init_db()


# ============================================================
# AUTHENTICATION
# ============================================================

if "user" not in st.session_state:
    st.session_state.user = None


if not st.session_state.user:

    st.title("🧬 EpiFlow v2")

    st.caption(
        "Governed surveillance intelligence workspace"
    )

    with st.form("login"):

        username = st.text_input(
            "Username"
        )

        password = st.text_input(
            "Password",
            type="password",
        )

        submitted = st.form_submit_button(
            "Sign in",
            use_container_width=True,
        )

    if submitted:

        user = authenticate(
            username,
            password,
        )

        if user:

            st.session_state.user = user

            log_event(
                user,
                "LOGIN",
            )

            st.rerun()

        else:

            st.error(
                "Invalid username or password."
            )

    st.stop()


user = st.session_state.user


# ============================================================
# HEADER
# ============================================================

h1, h2 = st.columns(
    [8, 2]
)

with h1:

    st.title(
        "🧬 EpiFlow v2 — Surveillance Intelligence"
    )

    st.caption(
        "Validated epidemiology → "
        "Person · Place · Time → "
        "Maps → Dashboard → "
        "AI-assisted interpretation"
    )


with h2:

    st.write(
        f"**{user['username']}**"
    )

    st.caption(
        user["role"].title()
    )

    if st.button(
        "Sign out",
        use_container_width=True,
    ):

        log_event(
            user,
            "LOGOUT",
        )

        st.session_state.clear()

        st.rerun()


# ============================================================
# SESSION STATE
# ============================================================

if "source_df" not in st.session_state:
    st.session_state.source_df = None

if "source_name" not in st.session_state:
    st.session_state.source_name = None


# ============================================================
# SIDEBAR — DATA INGESTION
# ============================================================

with st.sidebar:

    st.header(
        "Workspace"
    )

    st.caption(
        f"Role: **{user['role']}**"
    )

    if can(
        user,
        "upload",
    ):

        uploaded = st.file_uploader(
            "Upload surveillance data",
            type=[
                "csv",
                "xlsx",
                "xls",
                "parquet",
            ],
        )

        if uploaded is not None:

            loaded = normalize_column_names(
                load_tabular(
                    uploaded
                )
            )

            st.session_state.source_df = loaded

            st.session_state.source_name = (
                uploaded.name
            )

            log_event(
                user,
                "UPLOAD_DATASET",
                uploaded.name,
                (
                    f"{len(loaded)} rows x "
                    f"{loaded.shape[1]} columns"
                ),
            )


        demo = Path(
            "data/"
            "mpox_case_study_"
            "messy_spatial_dashboard.csv"
        )

        if (
            demo.exists()
            and st.button(
                "Load bundled demo",
                use_container_width=True,
            )
        ):

            st.session_state.source_df = (
                normalize_column_names(
                    load_tabular(
                        demo
                    )
                )
            )

            st.session_state.source_name = (
                demo.name
            )

            log_event(
                user,
                "LOAD_DEMO",
                demo.name,
            )


    st.divider()

    st.markdown(
        "**Pipeline**"
    )

    st.caption(
        "Ingest → Schema → Quality → Clean → "
        "Person → Place → Time → Maps → "
        "Dashboard → AI → Export"
    )


# ============================================================
# NO DATA YET
# ============================================================

if st.session_state.source_df is None:

    if user["role"] == "viewer":

        st.info(
            "A viewer account can access approved "
            "dashboard outputs once an analyst has "
            "loaded data in this app session."
        )

    else:

        st.info(
            "Upload a CSV, Excel or Parquet "
            "surveillance line list to begin."
        )

    st.stop()


# ============================================================
# SOURCE DATA
# ============================================================

raw = (
    st.session_state
    .source_df
    .copy()
)

source_name = (
    st.session_state.source_name
    or "dataset"
)

suggested = suggest_mapping(
    raw.columns
)


# ============================================================
# ROLE-AWARE TAB CONSTRUCTION
# ============================================================

tab_names = []


if can(
    user,
    "view_raw",
):
    tab_names.append(
        "① Data"
    )


if can(
    user,
    "schema",
):
    tab_names.append(
        "② Schema"
    )


if can(
    user,
    "clean",
):
    tab_names.append(
        "③ Quality & Cleaning"
    )


if can(
    user,
    "analyse",
):
    tab_names += [
        "④ Person",
        "⑤ Place",
        "⑥ Time",
    ]


if (
    can(
        user,
        "internal_map",
    )
    or can(
        user,
        "briefing_map",
    )
):

    tab_names.append(
        "⑦ Maps"
    )


if can(
    user,
    "dashboard",
):
    tab_names.append(
        "⑧ Dashboard"
    )


if can(
    user,
    "ai",
):
    tab_names.append(
        "⑨ AI Interpretation"
    )


if (
    can(
        user,
        "export_data",
    )
    or can(
        user,
        "export_brief",
    )
):

    tab_names.append(
        "⑩ Export"
    )


if (
    can(
        user,
        "manage_users",
    )
    or can(
        user,
        "audit",
    )
):

    tab_names.append(
        "⚙️ Admin"
    )


tabs = dict(
    zip(
        tab_names,
        st.tabs(
            tab_names
        ),
    )
)


# ============================================================
# TAB 1 — DATA
# ============================================================

if "① Data" in tabs:

    with tabs["① Data"]:

        st.success(
            f"Loaded **{source_name}** — "
            f"{len(raw):,} rows × "
            f"{raw.shape[1]} columns"
        )

        a, b, c = st.columns(
            3
        )

        a.metric(
            "Rows",
            f"{len(raw):,}",
        )

        b.metric(
            "Columns",
            raw.shape[1],
        )

        c.metric(
            "Missing cells",
            (
                f"{int(raw.isna().sum().sum()):,}"
            ),
        )

        st.dataframe(
            raw.head(
                150
            ),
            use_container_width=True,
            height=480,
        )


# ============================================================
# TAB 2 — SCHEMA MAPPING
# ============================================================

if "② Schema" in tabs:

    with tabs["② Schema"]:

        st.subheader(
            "Map this dataset into a common "
            "epidemiology schema"
        )

        st.write(
            "Different systems use different column "
            "names. EpiFlow suggests mappings; "
            "the analyst approves meaning."
        )

        opts = [
            "— not available —"
        ] + list(
            raw.columns
        )

        mapping = {}

        cols = st.columns(
            3
        )

        for i, canon in enumerate(
            CANONICAL_FIELDS
        ):

            d = suggested.get(
                canon
            )

            idx = (
                opts.index(
                    d
                )
                if d in opts
                else 0
            )

            choice = cols[
                i % 3
            ].selectbox(
                canon,
                opts,
                index=idx,
                key=f"map_{canon}",
            )

            mapping[
                canon
            ] = (
                None
                if choice == opts[0]
                else choice
            )


        if st.button(
            "Approve schema mapping",
            type="primary",
            key="approve_schema_mapping",
        ):

            st.session_state.approved_mapping = (
                mapping.copy()
            )

            log_event(
                user,
                "APPROVE_SCHEMA",
                source_name,
                str(
                    mapping
                ),
            )

            st.success(
                "Schema mapping approved."
            )


# ============================================================
# APPLY APPROVED / SUGGESTED SCHEMA
# ============================================================

approved = st.session_state.get(
    "approved_mapping"
)

if approved is None:

    approved = {
        canon: suggested.get(
            canon
        )
        for canon
        in CANONICAL_FIELDS
    }


canonical = apply_mapping(
    raw,
    approved,
)


# ============================================================
# CLEANING POLICY
# ============================================================

with st.sidebar:

    if can(
        user,
        "clean",
    ):

        st.header(
            "Cleaning policy"
        )

        drop_exact = st.checkbox(
            "Drop exact duplicate rows",
            True,
            key="clean_drop_exact",
        )

        dedupe = st.checkbox(
            "Keep first repeated case_id",
            False,
            help=(
                "Off by default because repeated IDs "
                "require domain verification."
            ),
            key="clean_dedupe_case_id",
        )

    else:

        drop_exact = True

        dedupe = False


# ============================================================
# BUILD ANALYSIS DATASET
# ============================================================

analysis = build_analysis_dataset(
    canonical,
    drop_exact,
    dedupe,
)

audit = quality_audit(
    canonical
)

ind = rapid_indicators(
    analysis
)


# ============================================================
# TAB 3 — QUALITY & CLEANING
# ============================================================

if "③ Quality & Cleaning" in tabs:

    with tabs[
        "③ Quality & Cleaning"
    ]:

        st.subheader(
            "Automated data-quality gates"
        )

        vc = (
            audit[
                "status"
            ]
            .value_counts()
        )

        a, b, c = st.columns(
            3
        )

        a.metric(
            "PASS",
            int(
                vc.get(
                    "PASS",
                    0,
                )
            ),
        )

        b.metric(
            "WARN",
            int(
                vc.get(
                    "WARN",
                    0,
                )
            ),
        )

        c.metric(
            "FAIL",
            int(
                vc.get(
                    "FAIL",
                    0,
                )
            ),
        )

        st.dataframe(
            audit,
            use_container_width=True,
            hide_index=True,
        )

        with st.expander(
            "Completeness profile"
        ):

            st.dataframe(
                completeness_table(
                    canonical
                ),
                use_container_width=True,
                hide_index=True,
            )


        st.warning(
            "A quality flag is not automatic truth. "
            "Repeated IDs and temporal conflicts "
            "can require source verification."
        )


        if st.button(
            "Record cleaning policy",
            type="primary",
            key="record_cleaning_policy",
        ):

            log_event(
                user,
                "APPLY_CLEANING_POLICY",
                source_name,
                (
                    f"drop_exact={drop_exact}; "
                    f"dedupe={dedupe}"
                ),
            )

            st.success(
                "Analysis copy prepared: "
                f"{len(analysis):,} records."
            )


# ============================================================
# TAB 4 — PERSON
# ============================================================

if "④ Person" in tabs:

    with tabs["④ Person"]:

        st.subheader(
            "👥 PERSON — Who is represented "
            "in the reported data?"
        )

        a, b, c, d = st.columns(
            4
        )

        a.metric(
            "Analysis records",
            ind.get(
                "records",
                "—",
            ),
        )

        b.metric(
            "Confirmed",
            ind.get(
                "confirmed",
                "—",
            ),
        )

        c.metric(
            "Deaths recorded",
            ind.get(
                "deaths_recorded",
                "—",
            ),
        )

        d.metric(
            "Median age",
            ind.get(
                "median_age",
                "—",
            ),
        )


        l, r = st.columns(
            2
        )


        # UNIQUE KEY 1
        f = age_figure(
            analysis
        )

        if f is not None:

            l.plotly_chart(
                f,
                use_container_width=True,
                key="person_age_distribution_chart",
            )


        # UNIQUE KEY 2
        f = sex_figure(
            analysis
        )

        if f is not None:

            r.plotly_chart(
                f,
                use_container_width=True,
                key="person_sex_distribution_chart",
            )


        # UNIQUE KEY 3
        f = outcome_figure(
            analysis
        )

        if f is not None:

            st.plotly_chart(
                f,
                use_container_width=True,
                key="person_outcome_distribution_chart",
            )


        candidates = [
            x
            for x in [
                "sex",
                "classification",
                "outcome",
                "hospitalized",
            ]
            if x in analysis
        ]


        if candidates:

            v = st.selectbox(
                "Profile a person-related variable",
                candidates,
                key="person_profile_variable",
            )

            st.dataframe(
                categorical_profile(
                    analysis,
                    v,
                ),
                use_container_width=True,
                hide_index=True,
            )


        st.caption(
            "These describe reported records. "
            "Population risk requires "
            "appropriate denominators."
        )


# ============================================================
# TAB 5 — PLACE
# ============================================================

if "⑤ Place" in tabs:

    with tabs["⑤ Place"]:

        st.subheader(
            "📍 PLACE — Where are cases "
            "being reported?"
        )


        l, r = st.columns(
            2
        )


        # UNIQUE KEY 4
        f = place_figure(
            analysis,
            "region",
        )

        if f is not None:

            l.plotly_chart(
                f,
                use_container_width=True,
                key="place_region_burden_chart",
            )


        # UNIQUE KEY 5
        f = place_figure(
            analysis,
            "district",
        )

        if f is not None:

            r.plotly_chart(
                f,
                use_container_width=True,
                key="place_district_burden_chart",
            )


        st.caption(
            "Reported case burden is not "
            "the same as population risk."
        )


# ============================================================
# TAB 6 — TIME
# ============================================================

if "⑥ Time" in tabs:

    with tabs["⑥ Time"]:

        st.subheader(
            "📈 TIME — When are cases occurring?"
        )


        a, b, c = st.columns(
            3
        )


        a.metric(
            "Median reporting delay",
            ind.get(
                "median_reporting_delay_days",
                "—",
            ),
        )


        b.metric(
            "90th percentile delay",
            ind.get(
                "p90_reporting_delay_days",
                "—",
            ),
        )


        latest = (
            analysis[
                "date_onset"
            ].max()
            if (
                "date_onset"
                in analysis
                and analysis[
                    "date_onset"
                ]
                .notna()
                .any()
            )
            else None
        )


        c.metric(
            "Latest onset",
            (
                latest.strftime(
                    "%Y-%m-%d"
                )
                if latest is not None
                else "—"
            ),
        )


        l, r = st.columns(
            2
        )


        # UNIQUE KEY 6
        f = epidemic_curve_figure(
            analysis
        )

        if f is not None:

            l.plotly_chart(
                f,
                use_container_width=True,
                key="time_epidemic_curve_chart",
            )


        # UNIQUE KEY 7
        f = weekly_curve_figure(
            analysis
        )

        if f is not None:

            r.plotly_chart(
                f,
                use_container_width=True,
                key="time_weekly_onset_chart",
            )


        st.caption(
            "A lower recent bar does not prove "
            "lower transmission. Consider reporting "
            "delay, extraction date and completeness."
        )


# ============================================================
# TAB 7 — MAPS
# ============================================================

if "⑦ Maps" in tabs:

    with tabs["⑦ Maps"]:

        st.subheader(
            "🗺️ Geographic intelligence"
        )


        # ----------------------------------------------------
        # INTERNAL ANALYST MAP
        # ----------------------------------------------------

        if can(
            user,
            "internal_map",
        ):

            st.markdown(
                "### Internal case-location exploration"
            )


            if {
                "latitude",
                "longitude",
            }.issubset(
                analysis.columns
            ):

                m = internal_case_map(
                    analysis
                )

                if m:

                    st_folium(
                        m,
                        width=None,
                        height=520,
                        key="internal_case_location_map",
                    )

                    st.caption(
                        "Analyst-only view. "
                        "Record-level coordinates "
                        "may be sensitive."
                    )

                    log_event(
                        user,
                        "VIEW_INTERNAL_MAP",
                        source_name,
                    )

                else:

                    st.info(
                        "No usable record-level "
                        "coordinates."
                    )

            else:

                st.info(
                    "Latitude and longitude "
                    "are not mapped."
                )


        # ----------------------------------------------------
        # AGGREGATED BRIEFING MAP
        # ----------------------------------------------------

        if can(
            user,
            "briefing_map",
        ):

            st.markdown(
                "### Briefing map — "
                "aggregated reported burden"
            )


            bm, summary = (
                briefing_aggregate_map(
                    analysis,
                    "district",
                )
            )


            if bm:

                st_folium(
                    bm,
                    width=None,
                    height=500,
                    key="aggregated_district_briefing_map",
                )


                st.dataframe(
                    summary.sort_values(
                        "reported_cases",
                        ascending=False,
                    ),
                    use_container_width=True,
                    hide_index=True,
                )


                st.caption(
                    "This v2 prototype aggregates "
                    "available case coordinates to "
                    "district mean locations. "
                    "It is not an official "
                    "administrative-boundary choropleth."
                )

            else:

                st.info(
                    "District plus usable coordinates "
                    "are required for this briefing view."
                )


# ============================================================
# TAB 8 — DASHBOARD
# ============================================================

if "⑧ Dashboard" in tabs:

    with tabs["⑧ Dashboard"]:

        st.subheader(
            "📊 Surveillance Situation Dashboard"
        )

        st.caption(
            f"Source: {source_name}"
        )


        k1, k2, k3, k4 = st.columns(
            4
        )


        k1.metric(
            "Confirmed",
            ind.get(
                "confirmed",
                "—",
            ),
        )


        k2.metric(
            "Deaths recorded",
            ind.get(
                "deaths_recorded",
                "—",
            ),
        )


        delay = ind.get(
            "median_reporting_delay_days"
        )


        k3.metric(
            "Median reporting delay",
            (
                f"{delay} days"
                if delay is not None
                else "—"
            ),
        )


        comp = completeness_summary(
            analysis
        )


        comp_value = (
            round(
                float(
                    comp[
                        "percent"
                    ].mean()
                ),
                1,
            )
            if not comp.empty
            else None
        )


        k4.metric(
            "Mean selected completeness",
            (
                f"{comp_value}%"
                if comp_value is not None
                else "—"
            ),
        )


        left, right = st.columns(
            [2, 1]
        )


        # UNIQUE KEY 8
        # Same weekly figure as Time tab,
        # therefore MUST have a different key.
        f = weekly_curve_figure(
            analysis
        )

        if f is not None:

            left.plotly_chart(
                f,
                use_container_width=True,
                key="dashboard_weekly_onset_chart",
            )


        with right:

            st.markdown(
                "#### Priority signals"
            )


            if (
                "district"
                in analysis
                and analysis[
                    "district"
                ]
                .notna()
                .any()
            ):

                for (
                    name,
                    count,
                ) in (
                    analysis[
                        "district"
                    ]
                    .value_counts()
                    .head(
                        3
                    )
                    .items()
                ):

                    st.write(
                        f"• **{name}** — "
                        f"{count} reported records"
                    )


            if not comp.empty:

                worst = comp.iloc[
                    0
                ]

                st.write(
                    "• Lowest selected completeness: "
                    f"**{worst['metric']} "
                    f"({worst['percent']}%)**"
                )


            if (
                ind.get(
                    "p90_reporting_delay_days"
                )
                is not None
            ):

                st.write(
                    "• 90th percentile reporting delay: "
                    f"**{ind['p90_reporting_delay_days']} days**"
                )


        l, r = st.columns(
            2
        )


        # UNIQUE KEY 9
        # Same district chart as Place tab,
        # so use a separate dashboard-specific key.
        f = place_figure(
            analysis,
            "district",
        )

        if f is not None:

            l.plotly_chart(
                f,
                use_container_width=True,
                key="dashboard_district_burden_chart",
            )


        # UNIQUE KEY 10
        if not comp.empty:

            qf = px.bar(
                comp.sort_values(
                    "percent"
                ),
                x="percent",
                y="metric",
                orientation="h",
                range_x=[
                    0,
                    100,
                ],
                title=(
                    "Selected data completeness"
                ),
            )

            r.plotly_chart(
                qf,
                use_container_width=True,
                key="dashboard_data_completeness_chart",
            )


        st.markdown(
            "#### Rapid epidemiological brief"
        )


        st.info(
            build_brief(
                analysis,
                ind,
            )
        )


        st.caption(
            "Dashboard values come from the "
            "same validated analysis dataset "
            "used by Person, Place and Time."
        )


        log_event(
            user,
            "VIEW_DASHBOARD",
            source_name,
        )


# ============================================================
# TAB 9 — AI INTERPRETATION
# ============================================================

if "⑨ AI Interpretation" in tabs:

    with tabs[
        "⑨ AI Interpretation"
    ]:

        st.subheader(
            "🧠 AI-assisted epidemiological "
            "interpretation"
        )


        st.write(
            "Python performs deterministic "
            "calculations first. Claude receives "
            "aggregated analytical and quality "
            "evidence—not an intentional "
            "patient-level line list."
        )


        st.warning(
            "AI assists interpretation. "
            "It does not replace "
            "the epidemiologist."
        )


        if os.getenv(
            "ANTHROPIC_API_KEY"
        ):

            st.success(
                "Anthropic API is configured."
            )

        else:

            st.info(
                "Set ANTHROPIC_API_KEY on "
                "the server to enable this feature."
            )


        if st.button(
            "Generate AI interpretation",
            type="primary",
            key="generate_ai_interpretation",
        ):

            with st.spinner(
                "Interpreting validated "
                "aggregate evidence..."
            ):

                text, err = (
                    interpret_surveillance_results(
                        analysis,
                        ind,
                        audit,
                    )
                )


            if err:

                st.error(
                    err
                )

            else:

                st.session_state[
                    "ai_interpretation"
                ] = text


                log_event(
                    user,
                    "RUN_AI_INTERPRETATION",
                    source_name,
                )


        if st.session_state.get(
            "ai_interpretation"
        ):

            st.markdown(
                st.session_state[
                    "ai_interpretation"
                ]
            )


            st.caption(
                "AI-generated interpretation "
                "must be reviewed before "
                "operational use."
            )


# ============================================================
# TAB 10 — EXPORT
# ============================================================

if "⑩ Export" in tabs:

    with tabs["⑩ Export"]:

        st.subheader(
            "📦 Controlled exports"
        )


        brief = build_brief(
            analysis,
            ind,
        )


        if can(
            user,
            "export_data",
        ):

            st.download_button(
                "Download analysis-ready CSV",
                analysis.to_csv(
                    index=False
                ).encode(),
                "analysis_ready.csv",
                "text/csv",
                key="download_analysis_ready_csv",
            )


            st.download_button(
                "Download QA report",
                audit.to_csv(
                    index=False
                ).encode(),
                "quality_audit.csv",
                "text/csv",
                key="download_quality_audit_csv",
            )


        if can(
            user,
            "export_brief",
        ):

            st.download_button(
                "Download epidemiological brief",
                brief.encode(),
                "epidemiological_brief.txt",
                "text/plain",
                key="download_epidemiological_brief",
            )


        st.caption(
            "Viewer accounts cannot export "
            "the analysis-ready line list."
        )


# ============================================================
# ADMIN
# ============================================================

if "⚙️ Admin" in tabs:

    with tabs["⚙️ Admin"]:

        if can(
            user,
            "manage_users",
        ):

            st.subheader(
                "Users"
            )


            users_df = pd.DataFrame(
                list_users()
            )


            if not users_df.empty:

                st.dataframe(
                    users_df,
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "No users found."
                )


            st.info(
                "Create users from the server "
                "with setup_users.py. "
                "Passwords are bcrypt-hashed."
            )


        if can(
            user,
            "audit",
        ):

            st.subheader(
                "Audit log"
            )


            audit_df = pd.DataFrame(
                list_audit()
            )


            if not audit_df.empty:

                st.dataframe(
                    audit_df,
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "No audit events recorded yet."
                )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "EpiFlow v2 prototype. Before identifiable "
    "production health data: add HTTPS, private "
    "persistent storage, least-privilege IAM, "
    "approved retention, backups, monitoring "
    "and organizational identity."
)