import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import nh3

st.set_page_config(page_title="IGS Dashboard", layout="wide")

st.title("IGS Dashboard: California Census Tracts")
st.markdown(
    "Visualize social and economic indicators for low- and high-income neighborhoods."
)

st.info(
    "Ethics notice: Data is aggregated and anonymized. "
    "Avoid using these scores to stigmatize communities. "
    "Always consider context, limitations, and potential bias."
)


@st.cache_data
def login_to_api(username, password, api_url="http://localhost:8000/token"):
    """
    Obtain JWT token from FastAPI backend.
    """
    try:
        response = requests.post(api_url, data={"username": username, "password": password})
        response.raise_for_status()
        return response.json()["access_token"]
    except requests.RequestException as e:
        st.error(f"Login failed: {str(e)}")
        return None


@st.cache_data
def fetch_api_data(token, api_url="http://localhost:8000/tracts/"):
    """
    Fetch census tract data from FastAPI backend.
    """
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Sanitize census_tract strings
        for item in data:
            item["census_tract"] = nh3.clean(item["census_tract"])

        return pd.DataFrame(data)
    except requests.RequestException as e:
        st.error(f"API error: {str(e)}")
        return None


# --- Sidebar: Login ---
st.sidebar.header("Login")
username = st.sidebar.text_input("Username", value="admin")
password = st.sidebar.text_input("Password", type="password")

if st.sidebar.button("Login"):
    token = login_to_api(username, password)
    if token:
        st.session_state.token = token
        st.success("Login successful!")
    else:
        st.stop()

if "token" not in st.session_state:
    st.warning("Please log in to access data.")
    st.stop()

df = fetch_api_data(st.session_state.token)
if df is None or df.empty:
    st.warning("No data available.")
    st.stop()

# Data structure: list of unique census tracts
tract_list = sorted(list(df["census_tract"].unique()))
st.write(f"Available Census Tracts: {tract_list}")

# --- Sidebar Filters ---
st.sidebar.header("Filters")
selected_tract = st.sidebar.selectbox("Select Census Tract", ["All"] + tract_list)
min_inclusion = st.sidebar.slider("Minimum Inclusion Score", 0, 100, 0)

filtered_df = df[df["inclusion_score"] >= min_inclusion]

if selected_tract != "All":
    filtered_df = filtered_df[filtered_df["census_tract"] == selected_tract]

# --- Layout ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Census Tract Data")
    st.dataframe(filtered_df, use_container_width=True)

with col2:
    st.subheader("Inclusion vs. Growth")
    if not filtered_df.empty:
        fig = px.scatter(
            filtered_df,
            x="inclusion_score",
            y="growth_score",
            color="census_tract",
            title="Inclusion vs. Growth Score",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No data to display for current filters.")

# --- Challenge: List Comprehension (Low vs High Income Averages) ---

st.markdown("---")
st.subheader("Average Scores: Low-Income vs High-Income Tracts")

low_income_tracts = {
    "06037102107",  # Los Angeles, Skid Row
    "06065045117",  # Riverside, low-income urban
    "06059099251",  # Orange County, Santa Ana
    "06001400300",  # Alameda, Oakland inner city
    "06073008339",  # San Diego, City Heights
}

high_income_tracts = {
    "06085511712",  # Santa Clara, Palo Alto
    "06075010200",  # San Francisco, Pacific Heights
    "06041110100",  # Marin, Mill Valley
    "06013355102",  # Contra Costa, Danville
    "06059062610",  # Orange County, Newport Beach
}

# Use list comprehensions to get inclusion scores by group
low_inclusion_scores = [
    row.inclusion_score
    for _, row in df.iterrows()
    if row.census_tract in low_income_tracts
]

high_inclusion_scores = [
    row.inclusion_score
    for _, row in df.iterrows()
    if row.census_tract in high_income_tracts
]

def safe_avg(values):
    return sum(values) / len(values) if values else 0

avg_df = pd.DataFrame(
    {
        "group": ["Low Income", "High Income"],
        "avg_inclusion_score": [
            safe_avg(low_inclusion_scores),
            safe_avg(high_inclusion_scores),
        ],
    }
)

fig_bar = px.bar(
    avg_df,
    x="group",
    y="avg_inclusion_score",
    title="Average Inclusion Score: Low vs High Income Tracts",
)
st.plotly_chart(fig_bar, use_container_width=True)

st.caption(
    "This comparison highlights potential socioeconomic bias: "
    "if high-income tracts consistently have higher inclusion scores, "
    "decisions based solely on these scores may reinforce existing inequalities."
)
