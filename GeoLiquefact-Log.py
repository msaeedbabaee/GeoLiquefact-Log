import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Streamlit Page Config
st.set_page_config(page_title="GeoLiquefact & Sensitivity Analyzer", layout="wide")

class CohesiveSensitivityAnalyzer:
    """
    Evaluates Sensitivity (St), Liquefaction Potential, Quick Clay behavior, 
    and Soil Consistency based on Atterberg Limits, Water Content, and Shear Strength.
    Reference: Canadian Foundation Engineering Manual, Chapter 4[cite: 1].
    """

    def calculate_indices(self, LL, PL, wn):
        PI = LL - PL
        if PI <= 0:
            raise ValueError("LL must be strictly greater than PL.")
        LI = (wn - PL) / PI
        return round(PI, 2), round(LI, 2)

    def classify_consistency(self, cu):
        """Classifies soil consistency based on Undrained Shear Strength (Table 4.1)[cite: 1]"""
        if cu < 12:
            return "Very Soft"
        elif 12 <= cu < 25:
            return "Soft"
        elif 25 <= cu < 50:
            return "Firm"
        elif 50 <= cu < 100:
            return "Stiff"
        elif 100 <= cu <= 200:
            return "Very Stiff"
        else:
            return "Hard"

    def classify_sensitivity_us(self, St):
        if St < 1.0:
            return "Insensitive"
        elif 1.0 <= St < 2.0:
            return "Low Sensitivity"
        elif 2.0 <= St < 4.0:
            return "Medium Sensitivity"
        elif 4.0 <= St < 8.0:
            return "Sensitive"
        elif 8.0 <= St < 16.0:
            return "Extra Sensitive"
        elif 16.0 <= St <= 32.0:
            return "Slightly Quick"
        elif 32.0 < St <= 64.0:
            return "Medium Quick"
        else:
            return "Very Quick"

    def classify_sensitivity_swedish(self, St):
        if St < 8.0:
            return "Normal / Low Sensitivity"
        elif 8.0 <= St < 30.0:
            return "Medium Sensitivity"
        elif 30.0 <= St < 50.0:
            return "High Sensitivity"
        else:
            return "Quick Clay (Kvicklera)"

    def evaluate_sample(self, sample_name, LL, PL, wn, cu_undisturbed, cu_remolded, spt_n):
        PI, LI = self.calculate_indices(LL, PL, wn)
        St = round(cu_undisturbed / cu_remolded, 2) if cu_remolded > 0 else 999.0

        us_class = self.classify_sensitivity_us(St)
        swedish_class = self.classify_sensitivity_swedish(St)
        consistency_class = self.classify_consistency(cu_undisturbed)
        
        wc_ll_ratio = round(wn / LL, 2)

        # Liquefaction & Quick Behavior Warnings
        warnings = []
        is_critical = False

        if wn > LL:
            warnings.append("⚠️ HIGH RISK: Natural water content exceeds Liquid Limit (wn > LL, LI > 1.0).")
            is_critical = True

        if cu_remolded < 0.5:
            warnings.append("🚨 CRITICAL WARNING: Remolded shear strength < 0.5 kPa. Behaves as liquid!")
            is_critical = True

        if St >= 30 or swedish_class == "Quick Clay (Kvicklera)":
            warnings.append("⚡ QUICK CLAY HAZARD: High Sensitivity.")
            is_critical = True

        if not warnings:
            warnings.append("✅ STABLE: Normal cohesive behavior.")

        # Liquefaction risk categorization for the image-style dashboard
        if wc_ll_ratio > 1.5:
            liq_risk = "HIGH"
        elif wc_ll_ratio > 1.0:
            liq_risk = "Moderate"
        else:
            liq_risk = "Low"

        is_quick = "Yes" if St >= 30 or wn > LL else "No"
        behavior = "Quick Clay" if is_quick == "Yes" else "Stiff/Stable"

        return {
            "Sample ID": sample_name,
            "LL (%)": LL,
            "PL (%)": PL,
            "wn (%)": wn,
            "PI (%)": PI,
            "LI": LI,
            "cu (kPa)": cu_undisturbed,
            "cu_remolded (kPa)": cu_remolded,
            "SPT-N": spt_n,
            "Consistency": consistency_class,
            "St": St,
            "wc/LL": wc_ll_ratio,
            "Quick Clay?": is_quick,
            "Liquefaction Risk": liq_risk,
            "Behavior": behavior,
            "US Classification": us_class,
            "Swedish Classification": swedish_class,
            "Critical Status": "DANGER" if is_critical else "SAFE",
            "Warning Details": " | ".join(warnings)
        }

    def plot_liquefaction_potential(self, results):
        fig, ax = plt.subplots(figsize=(10, 4))
        
        # Color-coded threshold regions matching user reference image
        ax.axhspan(0, 0.8, color='#28a745', alpha=0.6)
        ax.axhspan(0.8, 1.3, color='#ffc107', alpha=0.6)
        ax.axhspan(1.3, 2.0, color='#dc3545', alpha=0.6)
        
        ratios = [res['wc/LL'] for res in results]
        y_dummy = [np.random.uniform(0.5, 1.5) for _ in results]
        
        ax.scatter(ratios, y_dummy, color='black', s=80, zorder=5)
        for i, res in enumerate(results):
            ax.annotate(res['Sample ID'], (ratios[i] + 0.03, y_dummy[i]), fontweight='bold', color='white')

        ax.set_xlim(0, 3.0)
        ax.set_ylim(0, 2.0)
        ax.set_xlabel('Liquefaction Potential (wc/LL ratio)', fontweight='bold', color='white')
        ax.set_ylabel('Threshold', fontweight='bold', color='white')
        ax.set_title('Liquefaction Potential (wc/LL ratio)', fontweight='bold', color='white')
        ax.grid(True, linestyle='--', alpha=0.3)
        
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#0e1117')
        ax.tick_params(colors='white')
        return fig

    def plot_casagrande_chart(self, results):
        fig, ax = plt.subplots(figsize=(10, 5))
        
        ll_vals = list(range(10, 60))
        a_line_pi = [0.73 * (ll - 20) for ll in ll_vals]
        
        ax.plot(ll_vals, a_line_pi, color='cyan', linewidth=2, label='A-Line')
        
        ax.fill_between(ll_vals, a_line_pi, [val + 40 for val in a_line_pi], color='orange', alpha=0.3)
        ax.fill_between(ll_vals, [0]*len(ll_vals), a_line_pi, color='green', alpha=0.3)

        for res in results:
            ax.plot(res['LL (%)'], res['PI (%)'], 'o', color='yellow', markersize=8, zorder=5)
            ax.annotate(res['Sample ID'], (res['LL (%)'] + 0.5, res['PI (%)'] + 0.5), color='white', fontweight='bold')

        ax.set_xlim(0, 60)
        ax.set_ylim(0, 100)
        ax.set_xlabel('Plasticity (LL/PI)', fontweight='bold', color='white')
        ax.set_ylabel('Plasticity (PI %)', fontweight='bold', color='white')
        ax.set_title('Plasticity Chart (Atterberg Limits) & Critical Samples', fontweight='bold', color='white')
        ax.grid(True, linestyle='--', alpha=0.3)
        
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#0e1117')
        ax.tick_params(colors='white')
        return fig


# ==========================================
# Streamlit Web User Interface
# ==========================================

st.title("💧 Cohesive Soil Sensitivity & Liquefaction Comprehensive Dashboard")
st.markdown("Automated evaluation of soil sensitivity ($S_t$), CFEM Table 4.1 consistency, and hazard analytics[cite: 1].")

st.sidebar.header("Add Laboratory Sample")
sample_id = st.sidebar.text_input("Sample ID", "BH-01 (Depth 4m)")
ll_input = st.sidebar.number_input("Liquid Limit - LL (%)", value=45.0, step=1.0)
pl_input = st.sidebar.number_input("Plastic Limit - PL (%)", value=20.0, step=1.0)
wn_input = st.sidebar.number_input("Natural Water Content - wn (%)", value=48.0, step=1.0)
cu_input = st.sidebar.number_input("Undisturbed Shear Strength - cu (kPa)", value=25.0, step=1.0)
cur_input = st.sidebar.number_input("Remolded Shear Strength - cur (kPa)", value=0.4, step=0.1)
spt_input = st.sidebar.number_input("SPT-N Blow Count", value=6, step=1)

analyzer = CohesiveSensitivityAnalyzer()

if "sample_list" not in st.session_state:
    st.session_state.sample_list = [
        analyzer.evaluate_sample("BH-01", LL=40, PL=18, wn=22, cu_undisturbed=60, cu_remolded=15, spt_n=10),
        analyzer.evaluate_sample("BH-02", LL=52, PL=22, wn=55, cu_undisturbed=30, cu_remolded=1.2, spt_n=5),
        analyzer.evaluate_sample("BH-05", LL=35, PL=15, wn=42, cu_undisturbed=20, cu_remolded=0.3, spt_n=3),
    ]

if st.sidebar.button("Add Sample to Matrix"):
    try:
        new_sample = analyzer.evaluate_sample(sample_id, ll_input, pl_input, wn_input, cu_input, cur_input, spt_input)
        st.session_state.sample_list.append(new_sample)
        st.sidebar.success(f"Sample {sample_id} added successfully!")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

df_results = pd.DataFrame(st.session_state.sample_list)

# Section 1: Soil Sensitivity Evaluation Matrix
st.write("### 📊 Soil Sensitivity Evaluation Matrix")
st.dataframe(df_results[["Sample ID", "LL (%)", "St", "Quick Clay?", "Liquefaction Risk", "Behavior", "Consistency", "US Classification"]])

# Section 2: Liquefaction Potential Chart
st.write("### 🌈 Liquefaction Potential (wc/LL ratio)")
fig_liq = analyzer.plot_liquefaction_potential(st.session_state.sample_list)
st.pyplot(fig_liq)

# Section 3: Plasticity Chart & A-Line
st.write("### 📈 Plasticity Chart (Atterberg Limits) & Critical Samples")
fig_casa = analyzer.plot_casagrande_chart(st.session_state.sample_list)
st.pyplot(fig_casa)

# Section 4: Safety Alerts
st.write("### 🚨 Automated Safety Alerts & Hazard Logs")
for idx, row in df_results.iterrows():
    if row["Critical Status"] == "DANGER":
        st.error(f"**{row['Sample ID']}**: {row['Warning Details']}")
    else:
        st.success(f"**{row['Sample ID']}**: {row['Warning Details']}")
