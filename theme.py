import html
import streamlit as st


THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #0a0a0a;
}

#MainMenu, footer, header[data-testid="stHeader"] {
    visibility: hidden;
    height: 0;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

[data-testid="stSidebar"] {
    background: #0a0a0a;
    border-right: 1px solid #1f1f1f;
}

[data-testid="stSidebar"] > div:first-child {
    background: #0a0a0a;
}

.sidebar-card {
    background: #141414;
    border: 1px solid #222;
    border-radius: 12px;
    padding: 1rem 1.1rem;
    margin-bottom: 1rem;
}

.sidebar-card h4 {
    margin: 0 0 0.75rem 0;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #666;
}

.sidebar-stat {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.45rem 0;
    border-bottom: 1px solid #1a1a1a;
    font-size: 0.875rem;
}

.sidebar-stat:last-child { border-bottom: none; }
.sidebar-stat .label { color: #888; }
.sidebar-stat .value { color: #fff; font-weight: 600; }

.top-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.25rem 0 1.25rem 0;
    border-bottom: 1px solid #1a1a1a;
    margin-bottom: 1.5rem;
}

.top-bar-brand {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.top-bar-logo {
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, #22c55e, #16a34a);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
}

.top-bar-title {
    font-size: 1.35rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    color: #fff;
    text-transform: uppercase;
}

.top-bar-sub {
    font-size: 0.75rem;
    color: #555;
    letter-spacing: 0.04em;
}

.stats-banner {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    margin-bottom: 1.25rem;
    flex-wrap: wrap;
    gap: 1rem;
}

.stats-banner-left h1 {
    font-size: 2.5rem;
    font-weight: 800;
    color: #fff;
    margin: 0;
    line-height: 1;
    letter-spacing: -0.02em;
}

.stats-banner-left .sub-stats {
    margin-top: 0.5rem;
    font-size: 0.875rem;
    color: #666;
}

.stats-banner-left .sub-stats .green { color: #22c55e; font-weight: 600; }
.stats-banner-left .sub-stats .red { color: #ef4444; font-weight: 600; }

.section-card {
    background: #141414;
    border: 1px solid #222;
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1rem;
}

.section-card h3 {
    margin: 0 0 0.25rem 0;
    font-size: 1rem;
    font-weight: 700;
    color: #fff;
}

.section-card .section-desc {
    color: #666;
    font-size: 0.8rem;
    margin-bottom: 1rem;
}

.list-card {
    background: #111;
    border: 1px solid #1e1e1e;
    border-radius: 10px;
    padding: 1rem 1.15rem;
    margin-bottom: 0.5rem;
    transition: border-color 0.15s;
}

.list-card:hover {
    border-color: #333;
}

.list-card-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: #fff;
    margin-bottom: 0.5rem;
}

.list-card-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin-bottom: 0.5rem;
}

.tag {
    display: inline-block;
    padding: 0.15rem 0.55rem;
    border-radius: 999px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}

.tag-green { background: rgba(34, 197, 94, 0.15); color: #22c55e; border: 1px solid rgba(34, 197, 94, 0.3); }
.tag-red { background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); }
.tag-blue { background: rgba(59, 130, 246, 0.15); color: #3b82f6; border: 1px solid rgba(59, 130, 246, 0.3); }
.tag-gray { background: rgba(255, 255, 255, 0.06); color: #888; border: 1px solid #2a2a2a; }
.tag-yellow { background: rgba(234, 179, 8, 0.15); color: #eab308; border: 1px solid rgba(234, 179, 8, 0.3); }

.list-card-meta {
    font-size: 0.78rem;
    color: #555;
    line-height: 1.5;
}

.list-card-meta span { color: #777; }

.progress-bar-wrap {
    margin-top: 0.5rem;
    background: #1a1a1a;
    border-radius: 999px;
    height: 4px;
    overflow: hidden;
}

.progress-bar-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, #22c55e, #16a34a);
}

.progress-bar-fill.red {
    background: linear-gradient(90deg, #ef4444, #dc2626);
}

[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 0;
    background: #111;
    border: 1px solid #222;
    border-radius: 10px;
    padding: 4px;
}

[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent;
    border-radius: 8px;
    color: #666;
    font-weight: 600;
    font-size: 0.8rem;
    padding: 0.5rem 1rem;
    border: none;
}

[data-testid="stTabs"] [aria-selected="true"] {
    background: #1a1a1a !important;
    color: #22c55e !important;
}

[data-testid="stTabs"] [data-baseweb="tab-highlight"],
[data-testid="stTabs"] [data-baseweb="tab-border"] {
    display: none;
}

.stButton > button[kind="primary"],
.stButton > button {
    background: #22c55e;
    color: #000;
    border: none;
    border-radius: 8px;
    font-weight: 700;
    font-size: 0.85rem;
    padding: 0.55rem 1.25rem;
    transition: background 0.15s;
}

.stButton > button:hover {
    background: #16a34a;
    color: #000;
    border: none;
}

[data-testid="stMetric"] {
    background: #141414;
    border: 1px solid #222;
    border-radius: 10px;
    padding: 0.85rem 1rem;
}

[data-testid="stMetricLabel"] {
    color: #666 !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

[data-testid="stMetricValue"] {
    color: #fff !important;
    font-weight: 700 !important;
}

[data-testid="stDataFrame"] {
    border: 1px solid #222;
    border-radius: 10px;
    overflow: hidden;
}

div[data-testid="stAlert"] {
    border-radius: 10px;
    border: 1px solid #222;
}

.stTextInput input, .stSelectbox div[data-baseweb="select"],
.stSlider, .stNumberInput input {
    background: #141414 !important;
    border-color: #222 !important;
    border-radius: 8px !important;
    color: #fff !important;
}

label, .stMarkdown p, .stCaption {
    color: #888 !important;
}

h1, h2, h3, .stSubheader {
    color: #fff !important;
}

.gw-badge {
    display: inline-block;
    background: rgba(34, 197, 94, 0.12);
    color: #22c55e;
    border: 1px solid rgba(34, 197, 94, 0.25);
    border-radius: 999px;
    padding: 0.25rem 0.75rem;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.04em;
}
</style>
"""


def apply_theme():
    st.markdown(THEME_CSS, unsafe_allow_html=True)


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
                <div class="top-bar-logo">⚽</div>
                <div>
                    <div class="top-bar-title">FPL Dashboard</div>
                    {sub_html}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stats_banner(total: int, green_count: int, red_count: int, label: str = "PLAYERS"):
    st.markdown(
        f"""
        <div class="stats-banner">
            <div class="stats-banner-left">
                <h1>{total:,} {label}</h1>
                <div class="sub-stats">
                    <span class="green">{green_count:,} buy signals</span>
                    &nbsp;·&nbsp;
                    <span class="red">{red_count:,} sell signals</span>
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
