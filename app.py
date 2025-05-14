import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Prévision 2026 - Multi Marchés", layout="wide")
st.title("📊 Prévision 2026 - Dashboard Multi Marchés")

st.markdown("""
Cet outil vous permet de :
- Visualiser les prévisions par marché
- Ajuster le taux de croissance annuel
- Modifier la saisonnalité mensuelle
- Télécharger les résultats
- Comparer les KPIs entre 2025 et 2026
""")

# === Chargement du fichier fusionné
df = pd.read_excel("forecast_2026_fusion.xlsx")

# === Barre latérale : configuration
markets = df["Market"].unique().tolist()
selected_market = st.sidebar.selectbox("🌍 Choisir un marché", markets)
df_filtered = df[df["Market"] == selected_market]

growth_rate = st.sidebar.slider("📈 Évolution annuelle (%)", -10.0, 20.0, 2.0, step=0.5)
months = ['01','02','03','04','05','06','07','08','09','10','11','12']
seasonality = [st.sidebar.slider(f"Mois {m}", 0.0, 0.2, round(1/12, 3), 0.01) for m in months]

# === Calculs avec ajustements
adjusted_rows = []
for _, row in df_filtered.iterrows():
    base = row['Total_2025'] * (1 + growth_rate / 100)
    monthly_vals = [round(max(0, base * s), 2) for s in seasonality]
    adjusted_rows.append({
        "Product": row["Product"],
        "Product Line": row["Product Line"],
        **{f"2026-{m}": monthly_vals[i] for i, m in enumerate(months)},
        "Total_2026": round(sum(monthly_vals), 2),
        "Total_2025": row["Total_2025"],
        "Delta_%": round(((sum(monthly_vals) - row["Total_2025"]) / row["Total_2025"]) * 100, 2) if row["Total_2025"] > 0 else 0
    })

df_result = pd.DataFrame(adjusted_rows)

# === KPIs globaux
total_2025 = df_result["Total_2025"].sum()
total_2026 = df_result["Total_2026"].sum()
delta_global = ((total_2026 - total_2025) / total_2025) * 100 if total_2025 > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("📦 Total 2025", f"{total_2025:,.0f}")
col2.metric("🚀 Total 2026", f"{total_2026:,.0f}")
col3.metric("📊 Variation %", f"{delta_global:.2f}%", delta_color="inverse" if delta_global < 0 else "normal")

# === Tableau interactif
st.subheader(f"📋 Détails par SKU - {selected_market}")
st.dataframe(df_result, use_container_width=True)

# === Sélecteur pour Product Line individuelle
product_lines = df_result["Product Line"].unique().tolist()
selected_line = st.selectbox("📂 Choisir une ligne de produit à visualiser", ["Toutes"] + product_lines)

if selected_line != "Toutes":
    df_line_filtered = df_result[df_result["Product Line"] == selected_line]
    df_compare = df_line_filtered.groupby("Product Line")[["Total_2025", "Total_2026"]].sum().reset_index()
else:
    df_compare = df_result.groupby("Product Line")[["Total_2025", "Total_2026"]].sum().reset_index()

# === Graphique dynamique par Product Line : comparaison 2025 vs 2026
fig_compare = go.Figure()
fig_compare.add_trace(go.Bar(x=df_compare["Product Line"], y=df_compare["Total_2025"], name="2025"))
fig_compare.add_trace(go.Bar(x=df_compare["Product Line"], y=df_compare["Total_2026"], name="2026"))
fig_compare.update_layout(barmode='group', title="Comparaison des prévisions par ligne de produit")
st.plotly_chart(fig_compare, use_container_width=True)

# === Téléchargement
st.download_button(
    label="📥 Télécharger les prévisions ajustées",
    data=df_result.to_csv(index=False).encode('utf-8'),
    file_name=f"forecast_2026_{selected_market.lower()}.csv",
    mime='text/csv'
)
