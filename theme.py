import html
import streamlit as st


def get_theme_css(is_dark: bool = True) -> str:
    if is_dark:
        bg_app = "#0a0a0a"
        bg_card = "#141414"
        bg_list_card = "#111111"
        border_color = "#222222"
        input_border = "#2e2e2e"
        input_bg = "#141414"
        text_main = "#ffffff"
        text_sub = "#94a3b8"
        text_meta = "#64748b"
        placeholder_color = "#64748b"
        tab_bar_bg = "#141414"
        tab_active_bg = "#1e293b"
        tab_inactive_txt = "#94a3b8"
        tab_active_txt = "#9BBEED"
        tag_gray_bg = "rgba(255, 255, 255, 0.06)"
        tag_gray_txt = "#94a3b8"
        tag_gray_border = "#2a2a2a"
        header_border = "#1a1a1a"
        df_filter = "none"
        toggle_track_off = "#334155"
        toggle_border_off = "#475569"
        
        # High contrast pastel tag text for Dark Mode
        tag_blue_txt = "#9BBEED"
        tag_green_txt = "#4ade80" 
        tag_red_txt = "#f87171" 
        tag_yellow_txt = "#facc15" 
    else:
        bg_app = "#f8fafc"
        bg_card = "#ffffff"
        bg_list_card = "#ffffff"
        border_color = "#e2e8f0"
        input_border = "#cbd5e1"
        input_bg = "#ffffff"
        text_main = "#0f172a"
        text_sub = "#334155"
        text_meta = "#64748b"
        placeholder_color = "#64748b"
        tab_bar_bg = "#e2e8f0"
        tab_active_bg = "#ffffff"
        tab_inactive_txt = "#334155"
        tab_active_txt = "#1d4ed8"
        tag_gray_bg = "#f1f5f9"
        tag_gray_txt = "#334155"
        tag_gray_border = "#cbd5e1"
        header_border = "#e2e8f0"
        df_filter = "invert(0.92) hue-rotate(180deg) brightness(1.02)"
        toggle_track_off = "#cbd5e1"
        toggle_border_off = "#94a3b8"
        
        # Deep contrast tag text for Light Mode
        tag_blue_txt = "#1e40af"
        tag_green_txt = "#15803d"
        tag_red_txt = "#b91c1c"
        tag_yellow_txt = "#a16207"

    return f"""
<style>
/* Modern Font Upgrades (Outfit for headings, Inter for FPL-style data tables) */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@500;600;700;800;900&family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}

h1, h2, h3, h4, h5, h6, .stSubheader {{
    font-family: 'Outfit', sans-serif !important;
    color: {text_main} !important;
}}

.stApp {{
    background: {bg_app} !important;
}}

#MainMenu, footer {{
    visibility: hidden;
    height: 0;
}}

header[data-testid="stHeader"] {{
    background: transparent !important;
    z-index: 100 !important;
}}

/* Sidebar Base Styling */
.stApp [data-testid="stSidebarCollapsedControl"] {{
    display: flex !important;
    visibility: visible !important;
    z-index: 999999 !important;
    color: {text_main} !important;
    background-color: {bg_card} !important;
    border: 1px solid {input_border} !important;
    border-radius: 8px !important;
    margin-left: 0.5rem !important;
    margin-top: 0.5rem !important;
}}

.block-container {{
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}}

.stApp [data-testid="stSidebar"] {{
    background: {bg_app} !important;
    border-right: 1px solid {border_color} !important;
}}

.stApp [data-testid="stSidebar"] > div:first-child {{
    background: {bg_app} !important;
}}

.sidebar-card {{
    background: {bg_card};
    border: 1px solid {border_color};
    border-radius: 12px;
    padding: 1rem 1.1rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}}

.sidebar-card h4 {{
    margin: 0 0 0.75rem 0;
    font-size: 1rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    color: {text_meta};
}}

.sidebar-stat {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.45rem 0;
    border-bottom: 1px solid {border_color};
    font-size: 0.875rem;
}}

.sidebar-stat:last-child {{ border-bottom: none; }}
.sidebar-stat .label {{ color: {text_sub}; font-weight: 500; }}
.sidebar-stat .value {{ color: {text_main}; font-weight: 700; }}

/* ── OVERHAULED TOP BAR ── */
.top-bar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.5rem 0 1.5rem 0;
    border-bottom: 1px solid {header_border};
    margin-bottom: 1.5rem;
}}

.top-bar-brand {{
    display: flex;
    align-items: center;
}}

.top-bar-title {{
    font-family: 'Outfit', sans-serif;
    font-size: 3.2rem; 
    font-weight: 600; 
    letter-spacing: -0.03em;
    color: {text_main};
    line-height: 1.1;
}}

.top-bar-sub {{
    font-family: 'Inter', sans-serif;
    font-size: 0.95rem;
    color: {text_sub};
    font-weight: 500;
    margin-top: 6px;
}}

/* ── COMPACT & MODERN SECTION HEADER ── */
.section-card {{
    background: transparent !important;
    border: none !important;
    border-left: 4px solid #2563eb !important;
    border-radius: 0 !important;
    padding: 0.25rem 0 0.25rem 1rem !important;
    margin-top: 0.5rem !important;
    margin-bottom: 1.5rem !important;
}}

.section-card h3 {{
    margin: 0 0 0.35rem 0 !important;
    font-size: 1.45rem !important;
    font-weight: 700 !important;
    color: {text_main} !important;
    letter-spacing: -0.01em !important;
}}

.section-card .section-desc {{
    color: {text_sub} !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    margin: 0 !important;
}}

.list-card {{
    background: {bg_list_card};
    border: 1px solid {border_color};
    border-radius: 10px;
    padding: 1rem 1.15rem;
    margin-bottom: 0.5rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}}

.list-card-title {{
    font-family: 'Outfit', sans-serif;
    font-size: 1.05rem;
    font-weight: 600;
    color: {text_main};
    margin-bottom: 0.5rem;
}}

.list-card-tags {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin-bottom: 0.5rem;
}}

.tag {{
    display: inline-block;
    padding: 0.15rem 0.55rem;
    border-radius: 999px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.02em;
}}

/* Dynamic High-Contrast Tag Colors */
.tag-green {{ background: rgba(34, 197, 94, 0.15); color: {tag_green_txt}; border: 1px solid rgba(34, 197, 94, 0.3); }}
.tag-red {{ background: rgba(239, 68, 68, 0.15); color: {tag_red_txt}; border: 1px solid rgba(239, 68, 68, 0.3); }}
.tag-blue {{ background: rgba(155, 190, 237, 0.25); color: {tag_blue_txt}; border: 1px solid #9BBEED; }}
.tag-yellow {{ background: rgba(234, 179, 8, 0.18); color: {tag_yellow_txt}; border: 1px solid rgba(234, 179, 8, 0.35); }}
.tag-gray {{ background: {tag_gray_bg}; color: {tag_gray_txt}; border: 1px solid {tag_gray_border}; }}

.list-card-meta {{
    font-size: 0.78rem;
    color: {text_sub};
    line-height: 1.5;
}}

.list-card-meta span {{ color: {text_meta}; font-weight: 600; }}

/* ── DISTINCT, SEPARATED TABS OVERHAUL ── */
.stApp div[data-testid="stTabs"] {{
    background-color: transparent !important;
}}

/* Container has no background, just spacing */
.stApp div[data-testid="stTabs"] [role="tablist"] {{
    gap: 12px !important;
    background-color: transparent !important;
    border: none !important;
    padding: 0.25rem 0 0.75rem 0 !important;
}}

/* Each tab is a distinct button */
.stApp div[data-testid="stTabs"] button[role="tab"] {{
    background-color: {tab_bar_bg} !important;
    border: 1px solid {border_color} !important;
    border-radius: 8px !important;
    padding: 0.6rem 1.4rem !important;
    transition: all 0.2s ease-in-out !important;
}}

.stApp div[data-testid="stTabs"] button[role="tab"][aria-selected="false"] p,
.stApp div[data-testid="stTabs"] button[role="tab"][aria-selected="false"] span,
.stApp div[data-testid="stTabs"] button[role="tab"][aria-selected="false"] div,
.stApp div[data-testid="stTabs"] button[role="tab"][aria-selected="false"] * {{
    color: {tab_inactive_txt} !important;
    -webkit-text-fill-color: {tab_inactive_txt} !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    opacity: 0.85 !important;
    visibility: visible !important;
}}

.stApp div[data-testid="stTabs"] button[role="tab"][aria-selected="false"]:hover {{
    background-color: {bg_card} !important;
    border-color: {text_sub} !important;
    opacity: 1 !important;
}}

/* Active Tab elevates and gets a distinct blue border */
.stApp div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
    background-color: {tab_active_bg} !important;
    border: 1px solid #2563eb !important;
    box-shadow: 0 4px 8px rgba(0,0,0,0.06) !important;
    transform: translateY(-1px);
}}

.stApp div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] p,
.stApp div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] span,
.stApp div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] div,
.stApp div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] * {{
    color: {tab_active_txt} !important;
    -webkit-text-fill-color: {tab_active_txt} !important;
    font-weight: 800 !important;
    font-size: 0.9rem !important;
    opacity: 1 !important;
}}

/* Removes default Streamlit blue underline */
.stApp div[data-testid="stTabs"] [data-baseweb="tab-highlight"],
.stApp div[data-testid="stTabs"] [data-baseweb="tab-border"] {{
    display: none !important;
}}

/* ── BULLETPROOF SELECTBOX & DROPDOWNS ── */
.stApp div[data-testid="stSelectbox"] > div > div,
.stApp div[data-testid="stSelectbox"] [data-baseweb="select"] > div,
.stApp div[data-testid="stMultiSelect"] > div > div,
.stApp div[data-testid="stMultiSelect"] [data-baseweb="select"] > div,
.stApp div[data-baseweb="select"] > div {{
    background-color: {input_bg} !important;
    background: {input_bg} !important;
    border: 1px solid {input_border} !important;
    border-radius: 8px !important;
}}

.stApp div[data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within,
.stApp div[data-testid="stMultiSelect"] [data-baseweb="select"] > div:focus-within,
.stApp div[data-baseweb="select"] > div:focus-within {{
    border-color: #2563eb !important;
    box-shadow: 0 0 0 1px #2563eb !important;
}}

.stApp div[data-testid="stSelectbox"] *,
.stApp div[data-testid="stMultiSelect"] *,
.stApp div[data-baseweb="select"] * {{
    color: {text_main} !important;
    -webkit-text-fill-color: {text_main} !important;
}}

.stApp div[data-testid="stSelectbox"] svg,
.stApp div[data-testid="stMultiSelect"] svg,
.stApp div[data-baseweb="select"] svg {{
    fill: {text_main} !important;
    color: {text_main} !important;
}}

/* Dropdown Menu Overlay */
.stApp div[data-baseweb="popover"],
.stApp div[data-baseweb="popover"] > div,
.stApp ul[data-baseweb="menu"],
.stApp ul[role="listbox"],
.stApp li[role="option"] {{
    background-color: {bg_card} !important;
    background: {bg_card} !important;
    color: {text_main} !important;
    border-color: {border_color} !important;
}}

.stApp div[data-baseweb="popover"] *,
.stApp ul[role="listbox"] *,
.stApp li[role="option"] * {{
    color: {text_main} !important;
    -webkit-text-fill-color: {text_main} !important;
}}

.stApp li[role="option"]:hover,
.stApp li[role="option"][aria-selected="true"] {{
    background-color: {tab_bar_bg} !important;
    background: {tab_bar_bg} !important;
}}

/* ── BULLETPROOF TOGGLE SWITCH ── */
.stApp div[data-testid="stToggle"] label {{
    cursor: pointer !important;
}}

.stApp div[data-testid="stToggle"] label p,
.stApp div[data-testid="stToggle"] label span {{
    color: {text_main} !important;
    -webkit-text-fill-color: {text_main} !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
}}

/* Toggle Track (Off State) */
.stApp div[data-testid="stToggle"] label > div:first-of-type {{
    background-color: {toggle_track_off} !important;
    background: {toggle_track_off} !important;
    border: 1px solid {toggle_border_off} !important;
    opacity: 1 !important;
}}

/* Toggle Track (On State) */
.stApp div[data-testid="stToggle"] input:checked + div {{
    background-color: #2563eb !important;
    background: #2563eb !important;
    border-color: #2563eb !important;
}}

/* Toggle Thumb Handle */
.stApp div[data-testid="stToggle"] label > div:first-of-type > div {{
    background-color: #ffffff !important;
    background: #ffffff !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
    border: none !important;
}}

/* ── STRICT CHECKBOX FIX ── */
.stApp div[data-testid="stCheckbox"] label > span:first-of-type,
.stApp div[data-testid="stCheckbox"] [data-baseweb="checkbox"] > span:first-of-type {{
    background-color: {input_bg} !important;
    background: {input_bg} !important;
    border: 1px solid {input_border} !important;
    border-radius: 4px !important;
}}

.stApp div[data-testid="stCheckbox"] input:checked + span,
.stApp div[data-testid="stCheckbox"] [data-baseweb="checkbox"] input:checked + span {{
    background-color: #2563eb !important;
    background: #2563eb !important;
    border-color: #2563eb !important;
}}

.stApp div[data-testid="stCheckbox"] svg {{
    stroke: #ffffff !important;
    fill: #ffffff !important;
}}

.stApp div[data-testid="stCheckbox"] label p {{
    color: {text_main} !important;
    font-weight: 500 !important;
}}

/* ── SLIDERS ── */
.stApp div[data-baseweb="slider"] div[role="slider"] {{
    background-color: #2563eb !important;
    border: 2px solid #ffffff !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2) !important;
}}

.stApp div[data-baseweb="slider"] > div > div > div {{
    background-color: #2563eb !important;
}}

.stApp div[data-baseweb="slider"] p {{
    color: {text_sub} !important;
    font-weight: 600 !important;
}}

/* ── BUTTONS ── */
.stApp .stButton > button,
.stApp .stButton > button[kind="primary"],
.stApp .stButton > button[kind="secondary"] {{
    background-color: #2563eb !important;
    color: #ffffff !important;
    border: 1px solid #1d4ed8 !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    padding: 0.55rem 1.25rem !important;
    box-shadow: 0 2px 4px rgba(37, 99, 235, 0.15) !important;
}}

.stApp .stButton > button:hover {{
    background-color: #1d4ed8 !important;
    border-color: #1e40af !important;
    color: #ffffff !important;
}}

/* ── GUIDE POPOVER BUTTON ── */
.stApp div[data-testid="stPopover"] > button,
.stApp div[data-testid="stPopover"] button {{
    background-color: {bg_card} !important;
    color: {text_main} !important;
    border: 1px solid {input_border} !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
}}

.stApp div[data-testid="stPopover"] > button *,
.stApp div[data-testid="stPopover"] button * {{
    color: {text_main} !important;
    -webkit-text-fill-color: {text_main} !important;
    font-weight: 600 !important;
}}

/* ── METRICS (Fixes Text / Number Truncation) ── */
.stApp [data-testid="stMetric"] {{
    background: {bg_card} !important;
    border: 1px solid {border_color} !important;
    border-radius: 10px !important;
    padding: 0.75rem 0.85rem !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    overflow: visible !important;
}}

.stApp [data-testid="stMetricLabel"] {{
    font-family: 'Outfit', sans-serif !important;
    color: {text_sub} !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em;
    overflow: visible !important;
    white-space: normal !important; 
}}

.stApp [data-testid="stMetricValue"], 
.stApp [data-testid="stMetricValue"] > div {{
    color: {text_main} !important;
    font-weight: 800 !important;
    font-size: 1.25rem !important; 
    overflow: visible !important;
    white-space: normal !important;
    word-break: break-word !important;
}}

/* ── TABLES & DATAFRAMES ── */
.stApp div[data-testid="stDataFrame"] {{
    border: 1px solid {border_color} !important;
    border-radius: 10px !important;
    overflow: hidden !important;
    background: {bg_card} !important;
    filter: {df_filter} !important;
}}

.stApp div[data-testid="stAlert"] {{
    border-radius: 10px;
    border: 1px solid {border_color};
}}

/* ── INPUT FIELDS ── */
.stApp div[data-baseweb="input"],
.stApp div[data-baseweb="base-input"],
.stApp .stTextInput > div > div {{
    background-color: {input_bg} !important;
    border: 1px solid {input_border} !important;
    border-radius: 8px !important;
}}

.stApp div[data-baseweb="input"]:focus-within,
.stApp .stTextInput > div > div:focus-within {{
    border-color: #2563eb !important;
    box-shadow: 0 0 0 1px #2563eb !important;
}}

.stApp .stTextInput input, 
.stApp .stNumberInput input {{
    background-color: transparent !important;
    color: {text_main} !important;
    border: none !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
}}

.stApp ::placeholder,
.stApp input::placeholder,
.stApp textarea::placeholder,
.stApp .stTextInput input::placeholder {{
    color: {placeholder_color} !important;
    opacity: 0.85 !important;
}}

.stApp label, .stApp .stMarkdown p, .stApp .stCaption {{
    color: {text_sub} !important;
}}

.gw-badge {{
    display: inline-block;
    background: rgba(37, 99, 235, 0.1);
    color: #2563eb;
    border: 1px solid rgba(37, 99, 235, 0.3);
    border-radius: 999px;
    padding: 0.25rem 0.75rem;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.02em;
}}
</style>
"""


def apply_theme(is_dark: bool = True, *args, **kwargs):
    st.markdown(get_theme_css(is_dark), unsafe_allow_html=True)


def esc(text) -> str:
    return html.escape(str(text))


def fmt_num(value, spec: str = ".2f") -> str:
    try:
        return format(float(value), spec)
    except (ValueError, TypeError):
        return str(value)


def render_top_bar(subtitle: str = ""):
    sub_html = f'<div class="top-bar-sub">{esc(subtitle)}</div>' if subtitle else ""
    st.markdown(
        f"""
        <div class="top-bar">
            <div class="top-bar-brand">
                <div>
                    <div class="top-bar-title">FPL Optimizer</div>
                    {sub_html}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_card(title: str, rows: list[tuple[str, str]]):
    rows_html = "".join(
        f'<div class="sidebar-stat"><span class="label">{esc(k)}</span><span class="value">{esc(v)}</span></div>'
        for k, v in rows
    )
    st.sidebar.markdown(
        f'<div class="sidebar-card"><h4>{esc(title)}</h4>{rows_html}</div>',
        unsafe_allow_html=True,
    )


def render_tag(label: str, tag_type: str = "gray") -> str:
    return f'<span class="tag tag-{tag_type}">{esc(label)}</span>'


def render_list_card(title: str, tags: list[tuple[str, str]], meta: str, progress: float | None = None, progress_red: bool = False):
    tags_html = "".join(render_tag(label, t) for label, t in tags)
    progress_html = ""
    if progress is not None:
        fill_class = " red" if progress_red else ""
        progress_html = f"""
        <div class="progress-bar-wrap">
            <div class="progress-bar-fill{fill_class}" style="width: {min(progress, 100):.0f}%"></div>
        </div>
        """
    st.markdown(
        f"""
        <div class="list-card">
            <div class="list-card-title">{esc(title)}</div>
            <div class="list-card-tags">{tags_html}</div>
            <div class="list-card-meta">{meta}</div>
            {progress_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, description: str = ""):
    desc = f'<div class="section-desc">{esc(description)}</div>' if description else ""
    st.markdown(
        f'<div class="section-card"><h3>{esc(title)}</h3>{desc}</div>',
        unsafe_allow_html=True,
    )