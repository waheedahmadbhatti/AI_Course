import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import altair as alt

st.set_page_config(page_title="Streamlit Power Demo", page_icon="📊", layout="wide")

st.title("📊 Streamlit Power Demo")
st.markdown(
    """
    This single-file app demonstrates the breadth of what **Streamlit** can do:
    widgets, metrics, tables, built-in charts, Matplotlib, Plotly, and Altair.
    """
)

# ------------------------------------------------------------------
# Sidebar controls
# ------------------------------------------------------------------
st.sidebar.header("Controls")
n_points = st.sidebar.slider("Number of data points", 50, 1000, 200, step=50)
noise_level = st.sidebar.slider("Noise level", 0.0, 1.0, 0.2, step=0.05)
chart_type = st.sidebar.selectbox(
    "Highlight chart", ["Line", "Bar", "Area", "Scatter"], index=0
)
show_raw = st.sidebar.checkbox("Show raw data table", value=True)

# ------------------------------------------------------------------
# Build a synthetic dataset
# ------------------------------------------------------------------
rng = np.random.default_rng(seed=42)
x = np.linspace(0, 10, n_points)
trend = np.sin(x) + 0.3 * x
noise = rng.normal(0, noise_level, size=n_points)
y = trend + noise

df = pd.DataFrame({"x": x, "y": y, "trend": trend})
df["category"] = pd.cut(
    df["x"], bins=4, labels=["Q1", "Q2", "Q3", "Q4"]
)

# ------------------------------------------------------------------
# Metrics row
# ------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Data points", n_points)
col2.metric("Mean y", f"{df['y'].mean():.3f}")
col3.metric("Std y", f"{df['y'].std():.3f}")
col4.metric("Max y", f"{df['y'].max():.3f}")

st.divider()

# ------------------------------------------------------------------
# Built-in Streamlit charts
# ------------------------------------------------------------------
st.header("1. Built-in Streamlit Charts")

st.subheader(f"Highlighted: {chart_type} chart")
if chart_type == "Line":
    st.line_chart(df, x="x", y="y", color="#ff4b4b")
elif chart_type == "Bar":
    st.bar_chart(df.groupby("category", observed=True)["y"].mean())
elif chart_type == "Area":
    st.area_chart(df, x="x", y="y")
else:
    st.scatter_chart(df, x="x", y="y")

st.subheader("All three side-by-side")
c1, c2, c3 = st.columns(3)
with c1:
    st.caption("Line chart")
    st.line_chart(df, x="x", y="y")
with c2:
    st.caption("Area chart")
    st.area_chart(df, x="x", y="y")
with c3:
    st.caption("Bar chart (avg y per category)")
    st.bar_chart(df.groupby("category", observed=True)["y"].mean())

# ------------------------------------------------------------------
# Matplotlib
# ------------------------------------------------------------------
st.header("2. Matplotlib Figure")
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(df["x"], df["y"], label="noisy signal", alpha=0.7)
ax.plot(df["x"], df["trend"], label="trend", linewidth=2, color="red")
ax.set_xlabel("x")
ax.set_ylabel("y")
ax.set_title("Signal vs. Trend (Matplotlib)")
ax.legend()
ax.grid(True, alpha=0.3)
st.pyplot(fig)

# ------------------------------------------------------------------
# Plotly
# ------------------------------------------------------------------
st.header("3. Plotly Interactive Charts")

pc1, pc2 = st.columns(2)
with pc1:
    st.subheader("Plotly Express line")
    fig_px = px.line(df, x="x", y="y", color_discrete_sequence=["#0068c9"])
    st.plotly_chart(fig_px, use_container_width=True)

with pc2:
    st.subheader("Plotly scatter + trend")
    fig_go = go.Figure()
    fig_go.add_trace(go.Scatter(x=df["x"], y=df["y"], mode="markers", name="data"))
    fig_go.add_trace(go.Scatter(x=df["x"], y=df["trend"], mode="lines", name="trend"))
    fig_go.update_layout(xaxis_title="x", yaxis_title="y")
    st.plotly_chart(fig_go, use_container_width=True)

st.subheader("Plotly histogram of y")
fig_hist = px.histogram(df, x="y", nbins=40, title="Distribution of y")
st.plotly_chart(fig_hist, use_container_width=True)

# ------------------------------------------------------------------
# Altair
# ------------------------------------------------------------------
st.header("4. Altair Charts")

ac1, ac2 = st.columns(2)
with ac1:
    st.subheader("Altair line")
    line = (
        alt.Chart(df)
        .mark_line()
        .encode(x="x:Q", y="y:Q")
        .properties(height=300)
    )
    st.altair_chart(line, use_container_width=True)

with ac2:
    st.subheader("Altair scatter colored by category")
    scatter = (
        alt.Chart(df)
        .mark_circle(opacity=0.6)
        .encode(x="x:Q", y="y:Q", color="category:N")
        .properties(height=300)
    )
    st.altair_chart(scatter, use_container_width=True)

# ------------------------------------------------------------------
# Map (requires lat/lon columns)
# ------------------------------------------------------------------
st.header("5. Built-in st.map")
map_df = pd.DataFrame(
    {
        "lat": rng.uniform(37.70, 37.82, size=200),
        "lon": rng.uniform(-122.52, -122.35, size=200),
    }
)
st.map(map_df)

# ------------------------------------------------------------------
# Raw data table
# ------------------------------------------------------------------
if show_raw:
    st.header("6. Raw Data")
    st.dataframe(df.head(50), use_container_width=True)
    st.caption(f"Showing first 50 of {len(df)} rows.")

st.divider()
st.success("Done! Tweak the sidebar controls to see the charts update live.")