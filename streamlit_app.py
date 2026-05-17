import streamlit as st
from country_state_city import Country, State, City
import time
from app import app_graph

st.set_page_config(page_title="DriveLegal AI", page_icon="⚖️", layout="wide")

@st.cache_data(show_spinner=False)
def search_drivelegal(location, query):
    initial_state = {"location": location, "query": query}
    result = app_graph.invoke(initial_state)
    response = result.get('final_answer', "No response received.")
    
    if isinstance(response, list):
        text_blocks = [block.get('text', '') for block in response if isinstance(block, dict) and block.get('type') == 'text']
        if text_blocks:
            response = "\n".join(text_blocks)
        else:
            response = str(response)
    elif not isinstance(response, str):
        response = str(response)
        
    return response

# Futuristic CSS injection
st.markdown("""
<style>
    .stApp {
        background-color: #0f172a;
        background-image: 
            radial-gradient(circle at 15% 50%, rgba(59, 130, 246, 0.15), transparent 25%),
            radial-gradient(circle at 85% 30%, rgba(139, 92, 246, 0.15), transparent 25%);
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    h1 {
        font-size: 3.5rem !important;
        background: linear-gradient(to right, #60a5fa, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding-bottom: 0px;
        margin-bottom: 0px;
    }
    .subtitle {
        text-align: center;
        color: #94a3b8;
        font-size: 1.1rem;
        font-weight: 300;
        margin-bottom: 3rem;
    }
    .stSelectbox > div > div {
        background-color: rgba(30, 41, 59, 0.7);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
    }
    .results-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 2.5rem;
        margin-top: 2rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        color: #cbd5e1;
        line-height: 1.6;
    }
    .results-card h3 { color: #f8fafc; font-weight: 600; margin-top: 1rem; }
    .results-card strong { color: #93c5fd; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>DriveLegal</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Location-Aware Traffic Law & Fine Intelligence</div>", unsafe_allow_html=True)

# UI Layout
main_col, _ = st.columns([1, 0.01]) # Just to keep things centered if needed, using wide layout

with main_col:
    loc_cols = st.columns(3)
    
    with loc_cols[0]:
        countries = Country.get_countries()
        country_names = [c.name for c in countries]
        default_idx = country_names.index("United States") if "United States" in country_names else 0
        selected_country_name = st.selectbox("🌍 Country", options=country_names, index=default_idx)
        selected_country = next((c for c in countries if c.name == selected_country_name), None)
        
    with loc_cols[1]:
        states = State.get_states_of_country(selected_country.iso2) if selected_country else []
        if states:
            state_names = [s.name for s in states]
            selected_state_name = st.selectbox("🗺️ State / Province", options=state_names)
            selected_state = next((s for s in states if s.name == selected_state_name), None)
        else:
            selected_state_name = st.selectbox("🗺️ State / Province", options=["N/A"], disabled=True)
            selected_state = None
            
    with loc_cols[2]:
        if selected_country and selected_state:
            cities = City.get_cities_of_state(selected_country.iso2, selected_state.iso_code)
            if cities:
                city_names = [c.name for c in cities]
                selected_city_name = st.selectbox("📍 City", options=city_names)
            else:
                selected_city_name = st.selectbox("📍 City", options=["N/A"], disabled=True)
        else:
            selected_city_name = st.selectbox("📍 City", options=["N/A"], disabled=True)

    loc_parts = []
    if selected_city_name and selected_city_name != "N/A":
        loc_parts.append(selected_city_name)
    if selected_state_name and selected_state_name != "N/A":
        loc_parts.append(selected_state_name)
    if selected_country_name:
        loc_parts.append(selected_country_name)
        
    location_str = ", ".join(loc_parts)
    
    COMMON_QUERIES = [
        "What are the speeding fines and limits?",
        "Are U-turns legal at intersections?",
        "What are the street parking rules?",
        "Is it legal to turn right on red?",
        "What are the window tinting laws?",
        "What are the distracted driving or cell phone laws?",
        "What are the child car seat requirements?",
        "What are the DUI/DWI limits and penalties?",
        "Do I need to carry physical car insurance documents?",
        "What are the rules for yielding to pedestrians?",
        "Are there HOV (High Occupancy Vehicle) lane restrictions?",
        "What are the laws regarding motorcycle lane splitting?",
        "Is it required to wear a helmet on a motorcycle or bicycle?",
        "What are the restrictions for teenage or learner drivers?",
        "Are radar detectors legal to use?",
        "What are the penalties for running a stop sign or red light?",
        "What are the laws on using hazard lights while driving?",
        "Is it legal to drive barefoot?",
        "What are the rules for driving with a cracked windshield?",
        "Are dashcams legal to use and mount on the windshield?"
    ]
    
    selected_query = st.selectbox("⚖️ Legal Query", options=COMMON_QUERIES)
    
    st.write("") # Spacer
    if st.button("Search Traffic Laws", type="primary", use_container_width=True):
        with st.spinner("Searching Database & Web..."):
            try:
                response = search_drivelegal(location_str, selected_query)
                safe_response = response.replace('$', '\\$')
                full_html = f"<div class='results-card'>\n\n{safe_response}\n\n</div>"
                st.markdown(full_html, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
