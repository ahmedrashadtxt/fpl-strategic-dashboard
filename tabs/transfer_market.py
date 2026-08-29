from data import get_manager_squad_ids
import pandas as pd
import streamlit as st
from theme import fmt_num, render_list_card, section_header


def render_transfer_market_tab(conn, current_gw):
    col_t5_hdr, col_t5_pop = st.columns([6, 1])
    with col_t5_hdr:
        section_header(
            "Transfer Market Watch",
            "Track net transfers to anticipate price changes",
        )
    with col_t5_pop:
        st.markdown("<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True)
        with st.popover("📖 Guide"):
            st.markdown(
                """
                **Transfer Velocity & Price Change Guide**
                
                * **Net Transfers:** Transfers in minus transfers out for the active gameweek.
                * 📈 **Heating Up (Green):** Crossing threshold triggers a **+£0.1m price rise**.
                * 📉 **Cooling Down (Red):** Heavy selling momentum indicates an impending **-£0.1m price drop**.
                """
            )

    col_search5, col_sq5, col_ref5 = st.columns([2.2, 1.3, 1.0])
    with col_search5:
        search_query5 = st.text_input(
            "🔍 Search Player / Club",
            placeholder="e.g. Palmer, Chelsea, Haaland, MCI...",
            key="tab5_search",
        )

    with col_sq5:
        st.markdown("<div style='margin-top: 1.8rem;'></div>", unsafe_allow_html=True)
        only_my_squad_tab5 = st.toggle(
            "🎯 Only My Squad Players", key="tab5_only_squad"
        )
    with col_ref5:
        st.markdown("<div style='margin-top: 1.8rem;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Update Market", width="stretch"):
            with st.spinner("Fetching latest transfers & prices..."):
                import fetch_data
                fetch_data.fetch_transfer_market_data()
            st.cache_data.clear()
            st.rerun()

    market_query = """
    SELECT
        p.id AS element_id,
        p.code,
        p.web_name AS Player,
        p.first_name || ' ' || p.second_name AS Full_Name,
        t.short_name AS Team,
        t.name AS Club_Name,
        (p.now_cost - p.cost_change_start) / 10.0 AS Start_Price,
        p.now_cost / 10.0 AS Current_Price,
        p.cost_change_start / 10.0 AS Total_Change,
        (p.transfers_in_event - p.transfers_out_event) AS Net_Transfers
    FROM players p
    INNER JOIN teams t ON p.team = t.id
    ORDER BY Net_Transfers DESC
    """
    market_df = pd.read_sql(market_query, conn)
    for col_name in (
        "Start_Price",
        "Current_Price",
        "Total_Change",
        "Net_Transfers",
    ):
        market_df[col_name] = pd.to_numeric(market_df[col_name], errors="coerce")
    THRESHOLD = 60000

    if only_my_squad_tab5:
        active_manager_id_tab5 = st.session_state.get("manager_id", "").strip()
        if not active_manager_id_tab5:
            st.info("💡 Enter your FPL Team ID in the top bar to filter by your squad.")
            market_df = market_df.iloc[0:0]
        else:
            squad_ids_tab5 = get_manager_squad_ids(active_manager_id_tab5, current_gw)
            market_df = market_df[market_df["element_id"].isin(squad_ids_tab5)]

    if search_query5.strip():
        q5 = search_query5.strip()
        market_df = market_df[
            market_df["Player"].str.contains(q5, case=False, na=False)
            | market_df["Full_Name"].str.contains(q5, case=False, na=False)
            | market_df["Team"].str.contains(q5, case=False, na=False)
            | market_df["Club_Name"].str.contains(q5, case=False, na=False)
        ]

    if market_df.empty:
        st.info("No players found matching your transfer search or squad filter criteria.")
    else:
        col_in, col_out = st.columns(2)

        with col_in:
            st.markdown("#### 📈 Heating Up")
            heating_df = market_df[market_df["Net_Transfers"] > 0].head(10)
            if heating_df.empty:
                st.info("No matching players heating up.")
            else:
                for _, row in heating_df.iterrows():
                    progress = min((max(0, row["Net_Transfers"]) / THRESHOLD) * 100, 100)
                    change_tag = ("Rising", "green") if row["Total_Change"] > 0 else ("Flat", "gray")
                    card_img = f"https://resources.premierleague.com/premierleague/photos/players/110x140/p{row['code']}.png" if pd.notna(row.get("code")) else None
                    render_list_card(
                        f"{row['Player']} · {row['Team']}",
                        [("Transfer In", "green"), change_tag],
                        f'<span>Price</span> £{fmt_num(row["Current_Price"], ".1f")} ·'
                        f' <span>Change</span> {fmt_num(row["Total_Change"], "+.1f")}m ·'
                        f' <span>Net</span> {int(float(row["Net_Transfers"])):,}',
                        progress=progress,
                        img_url=card_img,
                    )

        with col_out:
            st.markdown("#### 📉 Cooling Down")
            cooling_df = market_df[market_df["Net_Transfers"] < 0].tail(10).sort_values(
                by="Net_Transfers", ascending=True
            )
            if cooling_df.empty:
                st.info("No matching players cooling down.")
            else:
                for _, row in cooling_df.iterrows():
                    progress = min((abs(min(0, row["Net_Transfers"])) / THRESHOLD) * 100, 100)
                    change_tag = ("Falling", "red") if row["Total_Change"] < 0 else ("Flat", "gray")
                    card_img = f"https://resources.premierleague.com/premierleague/photos/players/110x140/p{row['code']}.png" if pd.notna(row.get("code")) else None
                    render_list_card(
                        f"{row['Player']} · {row['Team']}",
                        [("Transfer Out", "red"), change_tag],
                        f'<span>Price</span> £{fmt_num(row["Current_Price"], ".1f")} ·'
                        f' <span>Change</span> {fmt_num(row["Total_Change"], "+.1f")}m ·'
                        f' <span>Net</span> {int(float(row["Net_Transfers"])):,}',
                        progress=progress,
                        progress_red=True,
                        img_url=card_img,
                    )