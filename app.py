import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os
from dotenv import load_dotenv

# -----------------------
# ENV
# -----------------------
load_dotenv()
API_KEY = os.getenv("COMPANIES_HOUSE_API_KEY")

# -----------------------
# CONFIG
# -----------------------
st.set_page_config(
    page_title="Risk Intelligence CRM",
    layout="wide",
    page_icon="📊"
)

st.title("🧠 Risk Intelligence CRM")

# -----------------------
# LOAD DATA
# -----------------------
file = st.file_uploader("Upload CSV", type=["csv"])

if file:
    df = pd.read_csv(file)

    # -----------------------
    # CLEANING (SAFE)
    # -----------------------
    df['company_name'] = df['company_name'].fillna("Unknown")

    df['incorporated'] = pd.to_datetime(df.get('incorporated'), errors='coerce')
    df['company_age_days'] = (pd.Timestamp.now() - df['incorporated']).dt.days

    for col in ['accounts_overdue', 'cs_overdue']:
        if col in df.columns:
            df[col] = df[col].fillna(0)
        else:
            df[col] = 0

    # -----------------------
    # INDUSTRY
    # -----------------------
    sic_map = {
        "62020": "IT Consulting",
        "62012": "Software Development",
        "68100": "Real Estate",
        "82990": "Business Services",
        "99999": "Dormant"
    }

    if "sic_codes" in df.columns:
        df['sic_codes'] = df['sic_codes'].astype(str)
        df['industry'] = df['sic_codes'].map(sic_map).fillna("Other")
    else:
        df['industry'] = "Unknown"

    # -----------------------
    # RISK ENGINE
    # -----------------------
    df['risk_score'] = (
        df['accounts_overdue'].astype(int) * 2 +
        df['cs_overdue'].astype(int) * 2 +
        (df['company_age_days'] < 365).astype(int)
    )

    df['risk_level'] = pd.cut(
        df['risk_score'],
        bins=[-1, 1, 3, 10],
        labels=["Low", "Medium", "High"]
    )

    def risk_reason(row):
        reasons = []
        if row['accounts_overdue']:
            reasons.append("Accounts overdue")
        if row['cs_overdue']:
            reasons.append("CS overdue")
        if row['company_age_days'] < 365:
            reasons.append("New company")
        return ", ".join(reasons)

    df['risk_reason'] = df.apply(risk_reason, axis=1)

    # -----------------------
    # COMPANY HOUSE URL
    # -----------------------
    if "company_number" in df.columns:
        df["companies_house_url"] = (
            "https://find-and-update.company-information.service.gov.uk/company/"
            + df["company_number"].astype(str)
        )
    else:
        df["companies_house_url"] = ""

    # -----------------------
    # SEARCH
    # -----------------------
    search = st.text_input("Search company")

    if search:
        df = df[df["company_name"].str.contains(search, case=False, na=False)]

    # -----------------------
    # FILTERS
    # -----------------------
    st.sidebar.header("Filters")

    risk_filter = st.sidebar.multiselect(
        "Risk Level",
        df['risk_level'].dropna().unique(),
        default=df['risk_level'].dropna().unique()
    )

    df = df[df['risk_level'].isin(risk_filter)]

    # -----------------------
    # API
    # -----------------------
    def get_company_profile(company_number):
        if not API_KEY:
            return None

        url = f"https://api.company-information.service.gov.uk/company/{company_number}"
        r = requests.get(url, auth=(API_KEY, ""))

        if r.status_code == 200:
            return r.json()
        return None

    # -----------------------
    # SESSION STATE
    # -----------------------
    if "selected_company" not in st.session_state:
        st.session_state.selected_company = None

    # -----------------------
    # KPI
    # -----------------------
    st.markdown("## Key Metrics")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Companies", len(df))
    c2.metric("High Risk", (df['risk_level'] == "High").sum())
    c3.metric("Accounts Overdue", int(df['accounts_overdue'].sum()))
    c4.metric("CS Overdue", int(df['cs_overdue'].sum()))

    # -----------------------
    # SECTOR OVERVIEW (FIXED)
    # -----------------------
    st.markdown("## 🧭 Sector Overview")

    sector_df = df.dropna(subset=["industry", "risk_score"]).copy()

    sector_summary = sector_df.groupby("industry", as_index=False).agg(
        companies=("company_name", "count"),
        avg_risk=("risk_score", "mean"),
        high_risk_count=("risk_level", lambda x: (x == "High").sum())
    )

    sector_summary["high_risk_pct"] = (
        sector_summary["high_risk_count"] / sector_summary["companies"] * 100
    )

    sector_summary = sector_summary.sort_values("avg_risk", ascending=False)

    st.dataframe(sector_summary, use_container_width=True)

    fig = px.bar(
        sector_summary,
        x="industry",
        y="avg_risk",
        title="Average Risk by Sector"
    )
    st.plotly_chart(fig, use_container_width=True)

    fig2 = px.bar(
        sector_summary,
        x="industry",
        y="high_risk_pct",
        title="High Risk % by Sector"
    )
    st.plotly_chart(fig2, use_container_width=True)

    # -----------------------
    # LAYOUT
    # -----------------------
    left, right = st.columns([2, 1])

    # -----------------------
    # COMPANY LIST (CLICKABLE)
    # -----------------------
    with left:
        st.markdown("## Companies")

        for _, row in df.sort_values("risk_score", ascending=False).iterrows():

            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                if st.button(row["company_name"], key=str(row["company_number"])):
                    st.session_state.selected_company = row["company_number"]

            with col2:
                st.write(row["risk_level"])

            with col3:
                st.write(row["risk_score"])

            with col4:
                st.markdown(
                    f"[Open]({row['companies_house_url']})",
                    unsafe_allow_html=True
                )

    # -----------------------
    # SIDE PANEL
    # -----------------------
    with right:
        st.markdown("## Company Profile")

        if st.session_state.selected_company:

            company = df[df["company_number"] == st.session_state.selected_company].iloc[0]

            st.subheader(company["company_name"])
            st.write("Risk:", company["risk_level"])
            st.write("Reason:", company["risk_reason"])
            st.write("Score:", company["risk_score"])

            profile = get_company_profile(company["company_number"])

            if profile:
                st.markdown("### Companies House Data")
                st.write("Status:", profile.get("company_status"))
                st.write("Type:", profile.get("type"))
                st.write("Incorporated:", profile.get("date_of_creation"))
                st.write("Jurisdiction:", profile.get("jurisdiction"))
            else:
                st.info("No API data available")

        else:
            st.info("Click a company to view details")

    # -----------------------
    # RISK CHART
    # -----------------------
    st.markdown("## Risk Distribution")

    fig = px.pie(df, names='risk_level')
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Upload a CSV file to get started.")