import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta

st.set_page_config(page_title="MedGuard AI", page_icon="💊", layout="wide")

DEFAULT_DATA = pd.DataFrame([
    ["Amoxicillin",420,55,5,120],["Paracetamol",680,82,7,180],
    ["Insulin",210,18,10,90],["Azithromycin",360,34,6,80],
    ["ORS",900,95,4,250],["Metformin",520,42,8,130],
    ["Cefixime",240,30,6,75],["Ibuprofen",460,48,5,100],
    ["Doxycycline",310,38,7,90],["Salbutamol",190,24,9,70]
], columns=["Medicine","Stock","Daily_Usage","Lead_Time_Days","Safety_Stock"])

def calculate(df):
    out=df.copy()
    out["Days_of_Cover"]=(out["Stock"]/out["Daily_Usage"].replace(0,np.nan)).round(1)
    out["Lead_Time_Demand"]=out["Daily_Usage"]*out["Lead_Time_Days"]
    out["30_Day_Demand"]=out["Daily_Usage"]*30
    out["Stockout_Date"]=[
        (date.today()+timedelta(days=max(0,int(np.floor(x))))).isoformat()
        if np.isfinite(x) else "N/A" for x in out["Days_of_Cover"]
    ]
    out["Risk_Score"]=np.clip(
        (out["Lead_Time_Demand"]+out["Safety_Stock"]-out["Stock"])/
        (out["Lead_Time_Demand"]+out["Safety_Stock"]+1)*100,0,100
    ).round().astype(int)
    out["Risk"]=pd.cut(out["Risk_Score"],[-1,24,59,79,101],
                       labels=["Low","Medium","High","Critical"])
    out["Reorder_Qty"]=np.maximum(
        0,out["30_Day_Demand"]+out["Safety_Stock"]-out["Stock"]
    ).round().astype(int)
    out["Priority"]=pd.cut(out["Risk_Score"],[-1,39,69,84,101],
                           labels=["Monitor","Normal","Urgent","Immediate"])
    return out

df=calculate(DEFAULT_DATA)

st.markdown("""
<style>
.title{font-size:2.4rem;font-weight:800;margin-bottom:0}
.sub{color:#6b7280;font-size:1.05rem;margin-bottom:1rem}
</style>
""",unsafe_allow_html=True)

st.markdown('<div class="title">💊 MedGuard AI</div>',unsafe_allow_html=True)
st.markdown('<div class="sub">Smart Medicine Inventory & Demand Forecasting • Hackathon MVP</div>',unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Controls")
    uploaded=st.file_uploader("Upload inventory CSV",type=["csv"])
    if uploaded:
        try:
            incoming=pd.read_csv(uploaded)
            required={"Medicine","Stock","Daily_Usage","Lead_Time_Days","Safety_Stock"}
            if required.issubset(incoming.columns):
                df=calculate(incoming); st.success("Inventory loaded.")
            else:
                st.error("Required: Medicine, Stock, Daily_Usage, Lead_Time_Days, Safety_Stock")
        except Exception as e: st.error(str(e))
    horizon=st.selectbox("Forecast horizon",[7,30,90],index=1)
    st.caption("Explainable MVP baseline using current consumption rate.")

a,b,c,d=st.columns(4)
a.metric("💊 Medicines",len(df))
b.metric("📦 Low Stock",int((df["Days_of_Cover"]<df["Lead_Time_Days"]).sum()))
c.metric("🚨 High/Critical",int(df["Risk"].isin(["High","Critical"]).sum()))
d.metric("📅 Avg. Cover",f"{df['Days_of_Cover'].mean():.1f} d")

tab1,tab2,tab3,tab4=st.tabs(["📊 Dashboard","🔮 Forecast","🚨 Alerts","🛒 Procurement"])

with tab1:
    st.subheader("Inventory Overview")
    st.dataframe(df[["Medicine","Stock","Daily_Usage","Days_of_Cover","Risk","Risk_Score"]],
                 use_container_width=True,hide_index=True)
    selected=st.selectbox("Medicine",df["Medicine"].tolist())
    r=df[df["Medicine"]==selected].iloc[0]
    days=np.arange(1,horizon+1)
    forecast=r["Daily_Usage"]*(1+0.08*np.sin(days/3))
    st.line_chart(pd.DataFrame({"Forecasted Demand":forecast},index=days))

with tab2:
    st.subheader("🔮 Demand Forecast")
    selected=st.selectbox("Select medicine",df["Medicine"].tolist(),key="f")
    r=df[df["Medicine"]==selected].iloc[0]
    days=np.arange(1,horizon+1)
    forecast=r["Daily_Usage"]*(1+0.08*np.sin(days/3))
    st.metric(f"{horizon}-day expected demand",f"{forecast.sum():.0f} units")
    st.dataframe(pd.DataFrame({"Day":days,"Expected Demand":forecast.round(1)}),
                 use_container_width=True,hide_index=True)

with tab3:
    st.subheader("🚨 Priority Alerts")
    for _,r in df.sort_values("Risk_Score",ascending=False).head(6).iterrows():
        st.warning(f"**{r['Medicine']}** — {r['Risk']} risk • stockout in ~{r['Days_of_Cover']:.1f} days • {r['Priority']} priority")

with tab4:
    st.subheader("🛒 Reorder Recommendations")
    st.dataframe(df.sort_values("Risk_Score",ascending=False)[
        ["Medicine","Stock","Days_of_Cover","Lead_Time_Days","Risk","Risk_Score","Reorder_Qty","Priority"]],
        use_container_width=True,hide_index=True)
    st.info("Decision-support prototype using forecast demand, supplier lead time and safety stock. Synthetic/demo data only.")

st.divider()
st.caption("MedGuard AI • Student innovation project • Synthetic/demo inventory data")
