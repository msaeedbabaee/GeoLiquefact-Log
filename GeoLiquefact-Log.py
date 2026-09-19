بر اساس راهنمای مهندسی پی کانادا (Canadian Foundation Engineering Manual - فصل ۴)، معیارهای طبقه‌بندی استواری خاک‌های چسبنده بر اساس مقاومت برشی زهکشی‌نشده ($c_u$) و تعداد ضربات تست نفوذ استاندارد (SPT-N) به جدول زیر مستند شده است:

* **بسیار نرم (Very soft):** $c_u < 12$ کیلوپاسکال


* **نرم (Soft):** $12 \le c_u < 25$ کیلوپاسکال


* **سفت نسبی (Firm):** $25 \le c_u < 50$ کیلوپاسکال


* **سفت (Stiff):** $50 \le c_u < 100$ کیلوپاسکال


* **بسیار سفت (Very stiff):** $100 \le c_u \le 200$ کیلوپاسکال


* **سخت (Hard):** $c_u > 200$ کیلوپاسکال



کد کامل و به‌روزرسانی‌شده‌ی استریم‌لیت که ویژگی **تعیین استواری خاک (Consistency)** بر اساس جدول ۴.۱ مرجع مذکور را به تحلیل‌گر اضافه می‌کند، به شرح زیر است:

```python
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

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
        """American / Skempton & Mitchell Sensitivity Classification"""
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
        """Swedish Standard Sensitivity Classification"""
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

        # Liquefaction / Quick Behavior Warnings
        warnings = []
        is_critical = False

        if wn > LL:
            warnings.append("⚠️ HIGH RISK: Natural water content exceeds Liquid Limit (wn > LL, LI > 1.0). High propensity for liquid flow upon disturbance.")
            is_critical = True

        if cu_remolded < 0.5:
            warnings.append("🚨 CRITICAL WARNING: Remolded shear strength is less than 0.5 kPa. Soil behaves as a liquid when remolded!")
            is_critical = True

        if St >= 50 or swedish_class == "Quick Clay (Kvicklera)":
            warnings.append("⚡ QUICK CLAY HAZARD: High Sensitivity (St ≥ 50). Risk of sudden retrogressive landslides.")
            is_critical = True

        if not warnings:
            warnings.append("✅ STABLE: Soil exhibits normal cohesive behavior under remolding.")

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
            "Sensitivity (St)": St,
            "US Classification": us_class,
            "Swedish Classification": swedish_class,
            "Critical Status": "DANGER" if is_critical else "SAFE",
            "Warning Details": " | ".join(warnings)
        }

    def plot_casagrande_chart(self, results):
        fig, ax = plt.subplots(figsize=(8, 5))
        
        # Plot A-Line: PI = 0.73 * (LL - 20)
        ll_vals = list(range(10, 100))
        a_line_pi = [0.73 * (ll - 20) for ll in ll_vals]
        
        ax.plot(ll_vals, a_line_pi, 'k--', label='A-Line (PI = 0.73*(LL-20))')
        ax.axvline(x=50, color='gray', linestyle=':', label='High Plasticity Limit (LL=50)')

        for res in results:
            marker_color = 'red' if res['Critical Status'] == 'DANGER' else 'green'
            ax.plot(res['LL (%)'], res['PI (%)'], 'o', color=marker_color, markersize=8)
            ax.annotate(res['Sample ID'], (res['LL (%)'] + 0.8, res['PI (%)'] + 0.8))

        ax.set_xlim(10, 100)
        ax.set_ylim(0, 60)
        ax.set_xlabel('Liquid Limit (LL %)', fontweight='bold')
        ax.set_ylabel('Plasticity Index (PI %)', fontweight='bold')
        ax.set_title('Atterberg Limits Plasticity Chart & Hazard Flags', fontweight='bold')
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.legend()
        
        return fig


# ==========================================
# Streamlit Web User Interface
# ==========================================

st.title("💧 Cohesive Soil Sensitivity & Liquefaction Matrix")
st.markdown("Automated evaluation of soil sensitivity ($S_t$), quick clay hazards, soil consistency (CFEM Table 4.1), and liquid-like behavior[cite: 1].")

st.sidebar.header("Add Laboratory Sample")
sample_id = st.sidebar.text_input("Sample ID", "BH-01 (Depth 4m)")
ll_input = st.sidebar.number_input("Liquid Limit - LL (%)", value=45.0, step=1.0)
pl_input = st.sidebar.number_input("Plastic Limit - PL (%)", value=20.0, step=1.0)
wn_input = st.sidebar.number_input("Natural Water Content - wn (%)", value=48.0, step=1.0)
cu_input = st.sidebar.number_input("Undisturbed Shear Strength - cu (kPa)", value=25.0, step=1.0)
cur_input = st.sidebar.number_input("Remolded Shear Strength - cur (kPa)", value=0.4, step=0.1)
spt_input = st.sidebar.number_input("SPT-N Blow Count (Optional)", value=6, step=1)

analyzer = CohesiveSensitivityAnalyzer()

# Pre-loaded Benchmark Test Dataset
if "sample_list" not in st.session_state:
    st.session_state.sample_list = [
        analyzer.evaluate_sample("BH-01 (Stiff Clay)", LL=40, PL=18, wn=22, cu_undisturbed=60, cu_remolded=15, spt_n=10),
        analyzer.evaluate_sample("BH-02 (Sensitive Clay)", LL=52, PL=22, wn=55, cu_undisturbed=30, cu_remolded=1.2, spt_n=5),
        analyzer.evaluate_sample("BH-03 (Quick Clay Hazard)", LL=35, PL=15, wn=42, cu_undisturbed=20, cu_remolded=0.3, spt_n=3),
    ]

if st.sidebar.button("Add Sample to Matrix"):
    try:
        new_sample = analyzer.evaluate_sample(sample_id, ll_input, pl_input, wn_input, cu_input, cur_input, spt_input)
        st.session_state.sample_list.append(new_sample)
        st.sidebar.success(f"Sample {sample_id} added successfully!")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

# Display Results
df_results = pd.DataFrame(st.session_state.sample_list)

st.write("### 📊 Soil Sensitivity & Consistency Evaluation Matrix")
st.dataframe(df_results[["Sample ID", "LL (%)", "PL (%)", "wn (%)", "PI (%)", "LI", "cu (kPa)", "Consistency", "Sensitivity (St)", "US Classification", "Swedish Classification", "Critical Status"]], use_container_state=False)

st.write("### 🚨 Automated Safety Alerts & Hazard Logs")
for idx, row in df_results.iterrows():
    if row["Critical Status"] == "DANGER":
        st.error(f"**{row['Sample ID']}**: {row['Warning Details']}")
    else:
        st.success(f"**{row['Sample ID']}**: {row['Warning Details']}")

# Render Visual Plasticity Chart
st.write("### 📈 Plasticity Chart (Atterberg Limits) & Critical Samples")
fig = analyzer.plot_casagrande_chart(st.session_state.sample_list)
st.pyplot(fig)

```
