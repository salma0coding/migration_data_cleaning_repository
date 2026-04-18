
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Africa Migration Dashboard",
    page_icon="📊",
    layout="wide"
)

DATA_PATH = "cleaned_africa_data_updated.xlsx"

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)

    # Clean column names
    df.columns = [str(c).strip() for c in df.columns]

    # Dates / numerics
    if "Incident Date" in df.columns:
        df["Incident Date"] = pd.to_datetime(df["Incident Date"], errors="coerce")

    numeric_cols = [
        "Incident Year",
        "Number of Dead",
        "Minimum Estimated Number of Missing",
        "Total Number of Dead and Missing",
        "Number of Survivors",
        "Number of Females",
        "Number of Males",
        "Number of Children",
        "Africa_Region_Code",
        "Check_Total",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Friendly text fill
    text_cols = df.select_dtypes(include="object").columns
    for col in text_cols:
        df[col] = df[col].fillna("Unknown").astype(str).str.strip()

    return df


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filters")

    years = sorted(df["Incident Year"].dropna().astype(int).unique().tolist()) if "Incident Year" in df.columns else []
    year_range = st.sidebar.slider(
        "Incident Year",
        min_value=min(years) if years else 2017,
        max_value=max(years) if years else 2025,
        value=(min(years) if years else 2017, max(years) if years else 2025),
    )

    region_options = sorted(df["Africa_Region_Name"].dropna().unique().tolist()) if "Africa_Region_Name" in df.columns else []
    selected_regions = st.sidebar.multiselect(
        "Africa Region",
        region_options,
        default=region_options
    )

    route_options = sorted(df["Migration Route"].dropna().unique().tolist()) if "Migration Route" in df.columns else []
    selected_routes = st.sidebar.multiselect(
        "Migration Route",
        route_options,
        default=route_options[:8] if len(route_options) > 8 else route_options
    )

    country_options = sorted(df["Country of Incident"].dropna().unique().tolist()) if "Country of Incident" in df.columns else []
    selected_countries = st.sidebar.multiselect(
        "Country of Incident",
        country_options,
        default=country_options
    )

    filtered = df.copy()

    if "Incident Year" in filtered.columns:
        filtered = filtered[
            filtered["Incident Year"].between(year_range[0], year_range[1])
        ]
    if selected_regions and "Africa_Region_Name" in filtered.columns:
        filtered = filtered[filtered["Africa_Region_Name"].isin(selected_regions)]
    if selected_routes and "Migration Route" in filtered.columns:
        filtered = filtered[filtered["Migration Route"].isin(selected_routes)]
    if selected_countries and "Country of Incident" in filtered.columns:
        filtered = filtered[filtered["Country of Incident"].isin(selected_countries)]

    return filtered


def metric_card(label: str, value):
    st.metric(label, f"{value:,}" if isinstance(value, (int, float)) else value)


def main():
    st.title("Africa Migration Incident Dashboard")
    st.caption("Interactive dashboard built from your cleaned dataset using Streamlit + Plotly.")

    try:
        df = load_data(DATA_PATH)
    except FileNotFoundError:
        st.error(f"Could not find `{DATA_PATH}` in the same folder as this app.")
        st.stop()

    filtered = apply_filters(df)

    # KPIs
    total_incidents = int(filtered["Incident ID"].nunique()) if "Incident ID" in filtered.columns else len(filtered)
    total_dead_missing = int(filtered["Total Number of Dead and Missing"].sum()) if "Total Number of Dead and Missing" in filtered.columns else 0
    total_survivors = int(filtered["Number of Survivors"].sum()) if "Number of Survivors" in filtered.columns else 0
    avg_per_incident = round(total_dead_missing / total_incidents, 2) if total_incidents else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Total Incidents", total_incidents)
    with c2:
        metric_card("Dead & Missing", total_dead_missing)
    with c3:
        metric_card("Survivors", total_survivors)
    with c4:
        metric_card("Avg Dead/Missing per Incident", avg_per_incident)

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Routes & Regions", "Demographics", "Data Table"])

    with tab1:
        left, right = st.columns((1.2, 1))
        with left:
            if "Incident Year" in filtered.columns and "Total Number of Dead and Missing" in filtered.columns:
                yearly = (
                    filtered.groupby("Incident Year", as_index=False)["Total Number of Dead and Missing"]
                    .sum()
                    .sort_values("Incident Year")
                )
                fig = px.line(
                    yearly,
                    x="Incident Year",
                    y="Total Number of Dead and Missing",
                    markers=True,
                    title="Dead & Missing by Year"
                )
                fig.update_layout(height=420)
                st.plotly_chart(fig, use_container_width=True)

        with right:
            if "Africa_Region_Name" in filtered.columns and "Incident ID" in filtered.columns:
                by_region = (
                    filtered.groupby("Africa_Region_Name", as_index=False)["Incident ID"]
                    .nunique()
                    .rename(columns={"Incident ID": "Incidents"})
                    .sort_values("Incidents", ascending=False)
                )
                fig = px.bar(
                    by_region,
                    x="Africa_Region_Name",
                    y="Incidents",
                    color="Africa_Region_Name",
                    title="Incidents by Africa Region"
                )
                fig.update_layout(showlegend=False, height=420, xaxis_title="")
                st.plotly_chart(fig, use_container_width=True)

        bottom_left, bottom_right = st.columns(2)
        with bottom_left:
            if "Cause of Death" in filtered.columns:
                top_causes = (
                    filtered.groupby("Cause of Death", as_index=False)["Incident ID"]
                    .nunique()
                    .rename(columns={"Incident ID": "Incidents"})
                    .sort_values("Incidents", ascending=False)
                    .head(10)
                )
                fig = px.bar(
                    top_causes,
                    x="Incidents",
                    y="Cause of Death",
                    orientation="h",
                    title="Top 10 Causes of Death"
                )
                fig.update_layout(height=420, yaxis={"categoryorder": "total ascending"})
                st.plotly_chart(fig, use_container_width=True)

        with bottom_right:
            if "Country of Incident" in filtered.columns and "Incident ID" in filtered.columns:
                top_countries = (
                    filtered.groupby("Country of Incident", as_index=False)["Incident ID"]
                    .nunique()
                    .rename(columns={"Incident ID": "Incidents"})
                    .sort_values("Incidents", ascending=False)
                    .head(10)
                )
                fig = px.bar(
                    top_countries,
                    x="Incidents",
                    y="Country of Incident",
                    orientation="h",
                    title="Top 10 Incident Countries"
                )
                fig.update_layout(height=420, yaxis={"categoryorder": "total ascending"})
                st.plotly_chart(fig, use_container_width=True)

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            if "Migration Route" in filtered.columns and "Total Number of Dead and Missing" in filtered.columns:
                route_summary = (
                    filtered.groupby("Migration Route", as_index=False)["Total Number of Dead and Missing"]
                    .sum()
                    .sort_values("Total Number of Dead and Missing", ascending=False)
                    .head(12)
                )
                fig = px.bar(
                    route_summary,
                    x="Migration Route",
                    y="Total Number of Dead and Missing",
                    color="Total Number of Dead and Missing",
                    title="Dead & Missing by Migration Route"
                )
                fig.update_layout(height=430, xaxis_title="", xaxis_tickangle=-30, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            if {"Africa_Region_Name", "Total Number of Dead and Missing"}.issubset(filtered.columns):
                region_fatal = (
                    filtered.groupby("Africa_Region_Name", as_index=False)["Total Number of Dead and Missing"]
                    .sum()
                    .sort_values("Total Number of Dead and Missing", ascending=False)
                )
                fig = px.pie(
                    region_fatal,
                    names="Africa_Region_Name",
                    values="Total Number of Dead and Missing",
                    title="Share of Dead & Missing by Africa Region",
                    hole=0.45
                )
                fig.update_layout(height=430)
                st.plotly_chart(fig, use_container_width=True)

    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            demo = pd.DataFrame({
                "Group": ["Females", "Males", "Children", "Survivors"],
                "Count": [
                    int(filtered["Number of Females"].sum()) if "Number of Females" in filtered.columns else 0,
                    int(filtered["Number of Males"].sum()) if "Number of Males" in filtered.columns else 0,
                    int(filtered["Number of Children"].sum()) if "Number of Children" in filtered.columns else 0,
                    int(filtered["Number of Survivors"].sum()) if "Number of Survivors" in filtered.columns else 0,
                ]
            })
            fig = px.bar(
                demo,
                x="Group",
                y="Count",
                color="Group",
                title="Demographic Totals"
            )
            fig.update_layout(showlegend=False, height=420)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            if "Incident Year" in filtered.columns:
                yearly_demo = (
                    filtered.groupby("Incident Year", as_index=False)[["Number of Females", "Number of Males", "Number of Children"]]
                    .sum()
                    .sort_values("Incident Year")
                )
                fig = go.Figure()
                for col in ["Number of Females", "Number of Males", "Number of Children"]:
                    fig.add_trace(go.Scatter(
                        x=yearly_demo["Incident Year"],
                        y=yearly_demo[col],
                        mode="lines+markers",
                        name=col.replace("Number of ", "")
                    ))
                fig.update_layout(
                    title="Demographics Over Time",
                    height=420,
                    xaxis_title="Incident Year",
                    yaxis_title="Count"
                )
                st.plotly_chart(fig, use_container_width=True)

    with tab4:
        keep_cols = [
            "Incident ID",
            "Incident Date",
            "Incident Year",
            "Africa_Region_Name",
            "Country of Incident",
            "Migration Route",
            "Cause of Death",
            "Total Number of Dead and Missing",
            "Number of Survivors",
        ]
        available = [c for c in keep_cols if c in filtered.columns]
        st.dataframe(filtered[available], use_container_width=True, height=500)

        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download filtered data as CSV",
            data=csv,
            file_name="filtered_africa_dashboard_data.csv",
            mime="text/csv"
        )

    st.markdown("---")
    st.markdown("**Suggested title for Mostaql portfolio:** Interactive Africa Migration Dashboard | Streamlit, Python, Plotly")


if __name__ == "__main__":
    main()
