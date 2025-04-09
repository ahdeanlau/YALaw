import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# ---------- Setup ----------
st.set_page_config(page_title="Website Traffic Dashboard", layout="wide")

# ---------- Sidebar ----------
st.sidebar.title("📊 Navigation")
page = st.sidebar.radio("Go to", ["Overview", "Trends", "Settings"])

# ---------- Fake data ----------
dates = pd.date_range(datetime.today() - timedelta(days=30), periods=30)
data = {
    "date": dates,
    "visitors": (1000 + 300 * np.sin(np.linspace(0, 3.14 * 2, 30))).astype(int),
    "bounce_rate": (50 + 10 * np.random.rand(30)).round(2),
}
df = pd.DataFrame(data)

# ---------- Header ----------
st.title("🌐 Website Traffic Dashboard")
st.markdown("Welcome to your dashboard. Here's how your site is performing lately.")

# ---------- Overview Page ----------
if page == "Overview":
    col1, col2, col3 = st.columns(3)

    col1.metric("👥 Visitors Today", df["visitors"].iloc[-1], f"{df['visitors'].iloc[-1] - df['visitors'].iloc[-2]}")
    col2.metric("📉 Bounce Rate", f"{df['bounce_rate'].iloc[-1]}%", f"{df['bounce_rate'].iloc[-1] - df['bounce_rate'].iloc[-2]:.2f}%")
    col3.metric("📆 Date", df["date"].iloc[-1].strftime("%Y-%m-%d"))

    st.markdown("### 📈 Traffic Over Time")
    fig = px.line(df, x="date", y="visitors", title="Visitor Trends (Last 30 Days)")
    st.plotly_chart(fig, use_container_width=True)

# ---------- Trends Page ----------
elif page == "Trends":
    st.markdown("### 🔍 Deep Dive into Metrics")
    selected_metric = st.selectbox("Select a metric to view", ["visitors", "bounce_rate"])

    fig = px.area(df, x="date", y=selected_metric, title=f"{selected_metric.capitalize()} Over Time")
    st.plotly_chart(fig, use_container_width=True)

# ---------- Settings Page ----------
elif page == "Settings":
    st.markdown("### ⚙️ Customize Your Dashboard")
    st.text_input("Website Name", "example.com")
    st.selectbox("Time zone", ["UTC", "EST", "PST", "CST"])
    st.color_picker("Primary Theme Color", "#4CAF50")
    st.button("💾 Save Settings")
