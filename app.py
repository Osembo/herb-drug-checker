import streamlit as st
import json
import pandas as pd
import datetime
import os

# Page config
st.set_page_config(
    page_title="Herb-Drug Checker Kenya",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'search_performed' not in st.session_state:
    st.session_state.search_performed = False
if 'last_drug' not in st.session_state:
    st.session_state.last_drug = ""
if 'last_herb' not in st.session_state:
    st.session_state.last_herb = ""
if 'last_result' not in st.session_state:
    st.session_state.last_result = None
if 'report_submitted' not in st.session_state:
    st.session_state.report_submitted = False
# My Meds list
if 'my_meds' not in st.session_state:
    st.session_state.my_meds = []

# ------------------------------------------------------------
# Load data
@st.cache_data
def load_data():
    try:
        with open('interactions.json', 'r', encoding='utf-8') as f:
            return json.load(f)['interactions']
    except:
        return []

# Normalize data to handle both formats (drug vs Drug Name, etc.)
def normalize_data(data):
    normalized = []
    for item in data:
        if 'drug' in item:
            normalized.append(item)
            continue
        if 'Drug Name' in item:
            try:
                new_item = {
                    'drug': item['Drug Name'].lower().strip(),
                    'herb': item['Herb Name'].lower().strip(),
                    'risk': item['Risk Level'],
                    'explanation': f"{item.get('Explanation (English)', '')} {item.get('Explanation (Swahili)', '')}".strip(),
                    'recommendation': f"{item.get('Recommendation (English)', '')} {item.get('Recommendation (Swahili)', '')}".strip()
                }
                # Optional fields
                if item.get('Scientific Name'):
                    new_item['scientific_name'] = item['Scientific Name']
                if item.get('Mechanism'):
                    new_item['mechanism'] = item['Mechanism']
                if item.get('Source'):
                    new_item['source'] = item['Source']
                if item.get('CYP450 Effect'):
                    new_item['cyp_effect'] = item['CYP450 Effect']
                if item.get('Notes'):
                    new_item['notes'] = item['Notes']
                normalized.append(new_item)
            except:
                continue
        else:
            continue
    return normalized

raw_data = load_data()
data = normalize_data(raw_data)

# Load aliases
@st.cache_data
def load_aliases():
    try:
        with open('aliases.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

aliases = load_aliases()

# Load conditions
@st.cache_data
def load_conditions():
    try:
        with open('conditions.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"✅ Loaded {len(data)} conditions")  # appears in Streamlit Cloud logs
            return data
    except FileNotFoundError:
        print("❌ conditions.json not found in the repository root!")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ JSON error in conditions.json: {e}")
        return {}

conditions_data = load_conditions()

# Function to find canonical herb name
def get_canonical_name(search_term):
    if not search_term:
        return search_term
    search_lower = search_term.lower().strip()
    if search_lower in aliases:
        return search_lower
    for canonical, alias_list in aliases.items():
        if search_lower in [a.lower() for a in alias_list]:
            return canonical
    return search_lower

# Function to save reports
def save_report(drug, herb, current_risk, reason, details):
    report = {
        "timestamp": str(datetime.datetime.now()),
        "drug": drug,
        "herb": herb,
        "current_risk": current_risk,
        "reason": reason,
        "details": details
    }
    reports = []
    if os.path.exists("reports.json"):
        with open("reports.json", "r") as f:
            try:
                reports = json.load(f)
            except:
                reports = []
    reports.append(report)
    with open("reports.json", "w") as f:
        json.dump(reports, f, indent=2)
    st.session_state.report_submitted = True

# ------------------------------------------------------------
# UI CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
.stApp {
    font-family: 'Inter', sans-serif;
    background: linear-gradient(135deg, #f5f7fa 0%, #e9ecef 100%);
}
.kenya-bar {
    height: 5px;
    background: linear-gradient(90deg, #000000 0%, #000000 33.33%, 
                #c8102e 33.33%, #c8102e 66.66%, 
                #00923f 66.66%, #00923f 100%);
    margin-bottom: 1rem;
}
.main-header {
    background: linear-gradient(135deg, #1a5f2a 0%, #2e7d32 100%);
    padding: 2rem 1rem;
    border-radius: 0 0 20px 20px;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    margin-bottom: 2rem;
}
.main-header h1 {
    color: white;
    font-size: 2.2rem;
    font-weight: 700;
    margin: 0;
}
.main-header p {
    color: rgba(255,255,255,0.9);
    font-size: 1.1rem;
    margin: 0.5rem 0 0 0;
}
.glass-card {
    background: white;
    padding: 1.5rem;
    border-radius: 15px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    margin: 1rem 0;
    border: 1px solid rgba(0,0,0,0.05);
}
.risk-card {
    border-radius: 15px;
    padding: 1.5rem;
    margin: 1.5rem 0;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    border-left: 8px solid;
}
.risk-high {
    background: #ffebee;
    border-left-color: #c62828;
}
.risk-moderate {
    background: #fff8e1;
    border-left-color: #ff8f00;
}
.risk-low {
    background: #e8f5e9;
    border-left-color: #2e7d32;
}
.risk-unknown {
    background: #f5f5f5;
    border-left-color: #757575;
}
.risk-card h3 {
    margin: 0 0 0.5rem 0;
    font-size: 1.5rem;
    font-weight: 700;
}
.scientific-name {
    font-style: italic;
    color: #2e7d32;
    font-size: 0.9rem;
    margin-top: -0.5rem;
    margin-bottom: 1rem;
}
.stButton button {
    background: linear-gradient(135deg, #1a5f2a 0%, #2e7d32 100%) !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 0.6rem 2rem !important;
    border-radius: 50px !important;
    border: none !important;
    box-shadow: 0 4px 12px rgba(46, 125, 50, 0.3) !important;
    width: 100%;
}
.stButton button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(46, 125, 50, 0.4) !important;
}
.chip-container {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin: 1rem 0;
}
.emergency-button {
    background: linear-gradient(135deg, #c62828 0%, #b71c1c 100%);
    padding: 1rem;
    border-radius: 12px;
    text-align: center;
    margin: 1rem 0;
}
.emergency-button a {
    display: inline-block;
    background: white;
    color: #c62828;
    padding: 0.6rem 1.5rem;
    border-radius: 50px;
    text-decoration: none;
    font-weight: bold;
    font-size: 1.3rem;
    margin: 0.5rem 0;
}
@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(198, 40, 40, 0.4); }
    70% { box-shadow: 0 0 0 10px rgba(198, 40, 40, 0); }
    100% { box-shadow: 0 0 0 0 rgba(198, 40, 40, 0); }
}
.pulse {
    animation: pulse 2s infinite;
}
.footer {
    text-align: center;
    padding: 1.5rem;
    background: linear-gradient(135deg, #2c3e50 0%, #1a1f2c 100%);
    color: white;
    border-radius: 20px 20px 0 0;
    margin-top: 2rem;
}
@media (max-width: 768px) {
    .main-header h1 {
        font-size: 1.8rem;
    }
}
/* Make select boxes clearly visible */
div[data-testid="stSelectbox"] > div {
    background-color: white !important;
    border: 2px solid #2e7d32 !important;
    border-radius: 10px !important;
    padding: 0.2rem !important;
}
div[data-testid="stSelectbox"] input {
    color: #1a5f2a !important;
    font-weight: 500 !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    background-color: white !important;
}
div[data-testid="stSelectbox"] input::placeholder {
    color: #6c757d !important;
    opacity: 1;
}
div[data-testid="stSelectbox"] svg {
    fill: #2e7d32 !important;
}
div[data-testid="stSelectbox"] span {
    color: #1a5f2a !important;
}
div[role="listbox"] ul {
    background-color: white !important;
    border: 1px solid #2e7d32 !important;
}
div[role="listbox"] li {
    color: #1a5f2a !important;
}
div[role="listbox"] li:hover {
    background-color: #e8f5e9 !important;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# Language selection
col1, col2 = st.columns([3, 1])
with col2:
    language = st.selectbox("🌐", ["English", "Kiswahili"])

# English texts
if language == "English":
    texts = {
        "title": "🌿 Herb-Drug Interaction Checker",
        "subtitle": "Know before you combine | Created in Kenya 🇰🇪",
        "drug_label": "💊 Medication",
        "drug_placeholder": "e.g., warfarin, metformin, tenofovir",
        "herb_label": "🌿 Herb",
        "herb_placeholder": "e.g., moringa, mwarobaini, neem",
        "check_button": "🔍 Check Interaction",
        "result_title": "📋 Interaction Result",
        "high_risk": "🚨🚨 HIGH RISK 🚨🚨",
        "moderate_risk": "⚠️⚠️ MODERATE RISK ⚠️⚠️",
        "low_risk": "✅ LOW RISK ✅",
        "unknown_risk": "❓ UNKNOWN ❓",
        "explanation": "Explanation",
        "recommendation": "Recommendation",
        "mechanism": "🔬 Mechanism of Action",
        "no_data_message": "No specific data for",
        "no_data_note": "This does NOT mean the combination is safe.",
        "advice_1": "• Consult a pharmacist or doctor",
        "advice_2": "• Keep a list of all herbs and medications",
        "advice_3": "• Start with small amounts",
        "advice_4": "• Call 719 in emergency",
        "view_common": "📚 View Common Interactions",
        "quick_search": "🔍 Quick Search",
        "search_all": "🔎 Search All",
        "search_placeholder": "Search by drug or herb...",
        "found": "Found {} interactions",
        "no_matches": "No matches found",
        "report_title": "📢 Report a Problem",
        "report_question": "What's wrong?",
        "report_button": "📤 Submit Report",
        "report_thanks": "✅ Thank you! Our team will review.",
        "request_button": "📢 Request this combination",
        "disclaimer": "⚠️ For informational purposes only. Not medical advice.",
        "emergency": "🚨 EMERGENCY: 719 (Kenya Poison Control)",
        "stats": "📊 Database Stats",
        "about": "### About This Tool",
        "last_updated": "Last Updated: March 2026",
        "footer": "Made with ❤️ for Kenya",
        # My Meds
        "my_meds_title": "💊 My Medications",
        "my_meds_add_label": "Add a drug to your list",
        "my_meds_add_placeholder": "Select a drug...",
        "my_meds_current": "Your current medications:",
        "my_meds_remove": "Remove",
        "my_meds_empty": "No medications saved yet. Add some above.",
        "my_meds_check_header": "🔍 Checking against your medications:",
        # Condition search
        "condition_title": "🔍 Search by Condition",
        "condition_placeholder": "Select a condition...",
        "condition_drugs_header": "Common medications for this condition:",
        "condition_herbs_header": "Herbs to be cautious with:",
        "condition_check_button": "Check interactions with my medications",
        "condition_no_drugs": "No specific drug list for this condition.",
        "condition_no_herbs": "No specific herb warnings for this condition.",
    }
else:
    texts = {
        "title": "🌿 Angalia Mwingiliano wa Dawa na Mitishamba",
        "subtitle": "Jua kabla ya kuchanganya | Imeundwa Kenya 🇰🇪",
        "drug_label": "💊 Dawa",
        "drug_placeholder": "mfano: warfarin, metformin",
        "herb_label": "🌿 Mmea",
        "herb_placeholder": "mfano: moringa, mwarobaini, neem",
        "check_button": "🔍 Angalia",
        "result_title": "📋 Matokeo",
        "high_risk": "🚨🚨 HATARI KUBWA 🚨🚨",
        "moderate_risk": "⚠️⚠️ HATARI YA KATI ⚠️⚠️",
        "low_risk": "✅ HATARI NDOGO ✅",
        "unknown_risk": "❓ HAIJULIKANI ❓",
        "explanation": "Maelezo",
        "recommendation": "Ushauri",
        "mechanism": "🔬 Jinsi Inavyofanya Kazi",
        "no_data_message": "Hatuna taarifa za",
        "no_data_note": "Hii haimaanishi kuwa ni salama.",
        "advice_1": "• Wasiliana na mfamasia au daktari",
        "advice_2": "• Orodhesha dawa na mitishamba yote",
        "advice_3": "• Anza kwa kiasi kidogo",
        "advice_4": "• Piga 719 kwa dharura",
        "view_common": "📚 Tazama Mwingiliano wa Kawaida",
        "quick_search": "🔍 Tafuta Haraka",
        "search_all": "🔎 Tafuta Zote",
        "search_placeholder": "Tafuta kwa dawa au mmea...",
        "found": "Yamepatikana {} mwingiliano",
        "no_matches": "Hakuna matokeo",
        "report_title": "📢 Ripoti Tatizo",
        "report_question": "Kipi hakiko sawa?",
        "report_button": "📤 Tuma Ripoti",
        "report_thanks": "✅ Asante! Timu yetu itaangalia.",
        "request_button": "📢 Omba mchanganyiko huu",
        "disclaimer": "⚠️ Kwa taarifa tu. Sio ushauri wa kitabibu.",
        "emergency": "🚨 DHARURA: 719 (Kenya Poison Control)",
        "stats": "📊 Takwimu",
        "about": "### Kuhusu Zana Hii",
        "last_updated": "Ilisasishwa: Machi 2026",
        "footer": "Imetengenezwa kwa ❤️ kwa Kenya",
        # My Meds
        "my_meds_title": "💊 Dawa Zangu",
        "my_meds_add_label": "Ongeza dawa kwenye orodha yako",
        "my_meds_add_placeholder": "Chagua dawa...",
        "my_meds_current": "Dawa zako za sasa:",
        "my_meds_remove": "Ondoa",
        "my_meds_empty": "Hakuna dawa zilizohifadhiwa bado. Ongeza hapo juu.",
        "my_meds_check_header": "🔍 Kuangalia dhidi ya dawa zako:",
        # Condition search
        "condition_title": "🔍 Tafuta kwa Hali ya Afya",
        "condition_placeholder": "Chagua hali...",
        "condition_drugs_header": "Dawa za kawaida kwa hali hii:",
        "condition_herbs_header": "Mimea ya kuwa mwangalifu nayo:",
        "condition_check_button": "Angalia mwingiliano na dawa zangu",
        "condition_no_drugs": "Hakuna orodha maalum ya dawa kwa hali hii.",
        "condition_no_herbs": "Hakuna tahadhari maalum za mimea kwa hali hii.",
    }

# Kenyan Flag Bar
st.markdown('<div class="kenya-bar"></div>', unsafe_allow_html=True)

# Header
st.markdown(f"""
    <div class="main-header">
        <h1>{texts['title']}</h1>
        <p>{texts['subtitle']}</p>
    </div>
""", unsafe_allow_html=True)

if data:
    # Get all unique drugs
    all_drugs = sorted(list(set([item['drug'].title() for item in data if item['drug'] != "any"])))
    all_herbs = sorted(list(set(aliases.keys()))) if aliases else []

    # --------------------------------------------------------
    # 1. My Meds Section
    with st.expander(texts['my_meds_title']):
        col1, col2 = st.columns([3, 1])
        with col1:
            new_med = st.selectbox(
                texts['my_meds_add_label'],
                options=[""] + all_drugs,
                format_func=lambda x: x if x else texts['my_meds_add_placeholder'],
                key="new_med_select"
            )
        with col2:
            if st.button("➕ Add", use_container_width=True):
                if new_med and new_med not in st.session_state.my_meds:
                    st.session_state.my_meds.append(new_med)
                    st.rerun()
        if st.session_state.my_meds:
            st.markdown(f"**{texts['my_meds_current']}**")
            for med in st.session_state.my_meds:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"• {med}")
                with col2:
                    if st.button(f"{texts['my_meds_remove']}", key=f"remove_{med}"):
                        st.session_state.my_meds.remove(med)
                        st.rerun()
        else:
            st.info(texts['my_meds_empty'])

    # --------------------------------------------------------
    # 2. Search by Condition Section
    with st.expander(texts['condition_title']):
        condition_options = [""] + sorted(conditions_data.keys())
        selected_condition_key = st.selectbox(
            "",
            options=condition_options,
            format_func=lambda x: conditions_data[x]['display_name'] if x else texts['condition_placeholder'],
            key="condition_select"
        )
        if selected_condition_key:
            condition = conditions_data[selected_condition_key]
            st.markdown(f"**{texts['condition_drugs_header']}**")
            if condition.get('drugs'):
                for drug in condition['drugs']:
                    if st.button(f"💊 {drug.title()}", key=f"cond_drug_{drug}"):
                        st.session_state.drug_select = drug.title()
                        st.rerun()
            else:
                st.info(texts['condition_no_drugs'])
            st.markdown(f"**{texts['condition_herbs_header']}**")
            if condition.get('herb_warnings'):
                for hw in condition['herb_warnings']:
                    risk_color = "🔴" if hw['risk'] == "High" else "🟡" if hw['risk'] == "Moderate" else "🟢"
                    st.markdown(f"""
                    <div style="background: #f8f9fa; padding: 0.8rem; border-radius: 8px; margin: 0.5rem 0; border-left: 5px solid {'#c62828' if hw['risk']=='High' else '#ff8f00' if hw['risk']=='Moderate' else '#2e7d32'};">
                        <b>{risk_color} {hw['herb'].title()}</b> – {hw['explanation']}<br>
                        <small><i>Recommendation:</i> {hw['recommendation']}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info(texts['condition_no_herbs'])

    # --------------------------------------------------------
    # 3. Quick Search Chips
    st.markdown(f"### {texts['quick_search']}")
    quick_searches = [
        {"drug": "Warfarin", "herb": "mwarobaini", "risk": "High"},
        {"drug": "Tenofovir", "herb": "muguka", "risk": "High"},
        {"drug": "Metformin", "herb": "moringa", "risk": "Moderate"},
        {"drug": "Lisinopril", "herb": "garlic", "risk": "Moderate"},
    ]
    cols = st.columns(len(quick_searches))
    for i, search in enumerate(quick_searches):
        with cols[i]:
            risk_color = "🔴" if search['risk'] == "High" else "🟡"
            button_key = f"chip_{i}_{search['drug']}_{search['herb']}"
            if st.button(f"{risk_color} {search['drug']} + {search['herb']}", key=button_key):
                if st.session_state.get('_last_chip') != button_key:
                    st.session_state['_last_chip'] = button_key
                    drug_lower = search['drug'].lower().strip()
                    herb_canonical = get_canonical_name(search['herb'])
                    result = None
                    for item in data:
                        if item['drug'] == drug_lower and item['herb'] == herb_canonical:
                            result = item
                            break
                    if not result:
                        for item in data:
                            if item['drug'] == "any" and item['herb'] == herb_canonical:
                                result = item
                                break
                    st.session_state.last_drug = search['drug']
                    st.session_state.last_herb = search['herb']
                    st.session_state.last_result = result
                    st.session_state.search_performed = True
                    st.rerun()

    # --------------------------------------------------------
    # 4. Input Section
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"##### {texts['drug_label']}")
        drug_input = st.selectbox("", options=all_drugs, index=None,
                                  placeholder=texts['drug_placeholder'],
                                  label_visibility="collapsed", key="drug_select")
    with col2:
        st.markdown(f"##### {texts['herb_label']}")
        herb_input = st.selectbox("", options=all_herbs, index=None,
                                  placeholder=texts['herb_placeholder'],
                                  label_visibility="collapsed", key="herb_select")
    st.markdown('</div>', unsafe_allow_html=True)

    # --------------------------------------------------------
    # 5. Check Button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        check_button = st.button(texts['check_button'], type="primary", use_container_width=True)

    # Handle search
    if check_button:
        if not drug_input or not herb_input:
            st.warning("⚠️ Please select both a drug and herb")
            st.session_state.search_performed = False
        else:
            st.session_state.search_performed = True
            st.session_state.last_drug = drug_input
            st.session_state.last_herb = herb_input
            herb_canonical = get_canonical_name(herb_input)
            drug_lower = drug_input.lower().strip()
            result = None
            for item in data:
                if item['drug'] == drug_lower and item['herb'] == herb_canonical:
                    result = item
                    break
            if not result:
                for item in data:
                    if item['drug'] == "any" and item['herb'] == herb_canonical:
                        result = item
                        break
            st.session_state.last_result = result

    # Display results
    if st.session_state.search_performed and st.session_state.last_drug:
        result = st.session_state.last_result
        drug_display = st.session_state.last_drug
        herb_display = st.session_state.last_herb
        herb_canonical = get_canonical_name(herb_display)

        if result:
            risk = result['risk']
            if risk == "High":
                card_class = "risk-card risk-high pulse"
                title = texts['high_risk']
            elif risk == "Moderate":
                card_class = "risk-card risk-moderate"
                title = texts['moderate_risk']
            else:
                card_class = "risk-card risk-low"
                title = texts['low_risk']
            if result.get('scientific_name'):
                st.markdown(f'<p class="scientific-name">{result["scientific_name"]}</p>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="{card_class}">
                <h3>{title}</h3>
                <div style="background: rgba(0,0,0,0.1); height: 2px; margin: 1rem 0;"></div>
                <p><strong>{texts['explanation']}:</strong> {result['explanation']}</p>
                <p><strong>{texts['recommendation']}:</strong> {result['recommendation']}</p>
            </div>
            """, unsafe_allow_html=True)
            if result.get('mechanism'):
                with st.expander(texts['mechanism']):
                    st.markdown(result['mechanism'])
                    if result.get('source'):
                        st.markdown(f"📚 **Source:** {result['source']}")
            with st.expander(texts['report_title']):
                report_reason = st.radio(
                    texts['report_question'],
                    ["Risk level seems wrong", "Explanation is unclear",
                     "Information is outdated", "Other"],
                    label_visibility="collapsed",
                    key="report_reason"
                )
                report_details = st.text_area("Details:", height=80, key="report_details")
                if st.button(texts['report_button'], key="submit_report"):
                    save_report(drug_display, herb_display, result['risk'], report_reason, report_details)
                if st.session_state.report_submitted:
                    st.success(texts['report_thanks'])
                    st.session_state.report_submitted = False
        else:
            st.markdown(f"""
            <div class="risk-card risk-unknown">
                <h3>{texts['unknown_risk']}</h3>
                <div style="background: rgba(0,0,0,0.1); height: 2px; margin: 1rem 0;"></div>
                <p><strong>{texts['no_data_message']} {drug_display} + {herb_display}</strong></p>
                <p>{texts['no_data_note']}</p>
                <p>{texts['advice_1']}<br>{texts['advice_2']}<br>{texts['advice_3']}<br>{texts['advice_4']}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(texts['request_button']):
                st.success(f"✅ Thank you! We'll research {drug_display} + {herb_display}")

        # Check against My Meds list
        if st.session_state.my_meds:
            st.markdown(f"### {texts['my_meds_check_header']}")
            found_any = False
            for med in st.session_state.my_meds:
                med_lower = med.lower().strip()
                if med_lower == drug_display.lower().strip():
                    continue
                interaction = None
                for item in data:
                    if item['drug'] == med_lower and item['herb'] == herb_canonical:
                        interaction = item
                        break
                if not interaction:
                    for item in data:
                        if item['drug'] == "any" and item['herb'] == herb_canonical:
                            interaction = item
                            break
                if interaction:
                    found_any = True
                    risk = interaction['risk']
                    if risk == "High":
                        card_class = "risk-card risk-high"
                        title = texts['high_risk']
                    elif risk == "Moderate":
                        card_class = "risk-card risk-moderate"
                        title = texts['moderate_risk']
                    else:
                        card_class = "risk-card risk-low"
                        title = texts['low_risk']
                    st.markdown(f"""
                    <div class="{card_class}">
                        <h4 style="margin-top:0;">{med} + {herb_display}</h4>
                        <div style="background: rgba(0,0,0,0.1); height: 2px; margin: 0.5rem 0;"></div>
                        <p><strong>{texts['explanation']}:</strong> {interaction['explanation']}</p>
                        <p><strong>{texts['recommendation']}:</strong> {interaction['recommendation']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            if not found_any:
                st.info(f"No known interactions found between {herb_display} and your other medications.")

    # --------------------------------------------------------
    # 6. Quick Reference & Search
    with st.expander(texts['view_common']):
        df_data = []
        for item in data[:10]:
            if item['drug'] != "any" and item['herb'] != "any":
                df_data.append({
                    texts['drug_label']: item['drug'].title(),
                    texts['herb_label']: item['herb'].title(),
                    "Risk": item['risk'],
                    texts['recommendation']: item['recommendation'][:50] + "..."
                })
        if df_data:
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)

    st.markdown(f"### {texts['search_all']}")
    search = st.text_input("", placeholder=texts['search_placeholder'], label_visibility="collapsed")
    if search:
        search_lower = search.lower()
        results = []
        for item in data:
            if item['drug'] != "any" and (search_lower in item['drug'] or search_lower in item['herb']):
                results.append(item)
        if results:
            st.success(texts['found'].format(len(results)))
            for r in results[:5]:
                risk_color = "🔴" if r['risk'] == "High" else "🟡" if r['risk'] == "Moderate" else "🟢"
                st.markdown(f"{risk_color} **{r['drug'].title()}** + **{r['herb'].title()}**")
        else:
            st.info(texts['no_matches'])

# ------------------------------------------------------------
# Sidebar (unchanged)
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/kenya.png", width=60)
    st.markdown(texts['about'])
    st.markdown("• PubMed • Natural Medicines DB • Kenyan guides")
    st.markdown("""
    <div class="emergency-button">
        <p style="color: white; margin: 0; font-size: 1.2rem; font-weight: bold;">🚨 EMERGENCY</p>
        <p style="color: white; margin: 0.5rem 0;">Kenya Poison Control</p>
        <a href="tel:719">📞 719</a>
        <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0; font-size: 0.9rem;">Free • 24/7</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(f"**{texts['stats']}**")
    if data:
        valid_interactions = [x for x in data if x['drug'] != "any" and x.get('risk')]
        if valid_interactions:
            high_count = sum(1 for x in valid_interactions if x['risk'] == 'High')
            moderate_count = sum(1 for x in valid_interactions if x['risk'] == 'Moderate')
            low_count = sum(1 for x in valid_interactions if x['risk'] == 'Low')
            total = len(valid_interactions)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🔴 High", high_count)
            with col2:
                st.metric("🟡 Moderate", moderate_count)
            with col3:
                st.metric("🟢 Low", low_count)
            st.markdown(f"**Total:** {total} interactions")
            st.markdown("**Risk Distribution:**")
            if high_count > 0:
                st.markdown(f"🔴 High: {'█' * high_count} ({high_count})")
            if moderate_count > 0:
                st.markdown(f"🟡 Moderate: {'█' * moderate_count} ({moderate_count})")
            if low_count > 0:
                st.markdown(f"🟢 Low: {'█' * low_count} ({low_count})")
        else:
            st.info("No interaction data")
    else:
        st.info("No data loaded")
    st.markdown("---")
    st.markdown(f"*{texts['last_updated']}*")

# Footer
st.markdown(f"""
    <div class="footer">
        <p>⚠️ {texts['disclaimer']}</p>
        <p>{texts['emergency']}</p>
        <p style="margin-top: 1rem;">❤️ {texts['footer']}</p>
    </div>
""", unsafe_allow_html=True)
