import re

with open('tabs/transfer_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

fetch_func = '''@st.cache_data(ttl=60, show_spinner=False)
def fetch_transfer_manager_transfers(manager_id: str):
    try:
        url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/transfers/"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return []

'''

text = text.replace('@st.cache_data(ttl=300, show_spinner=False)\ndef fetch_transfer_manager_picks', fetch_func + '@st.cache_data(ttl=300, show_spinner=False)\ndef fetch_transfer_manager_picks')

old_logic = '''    picks_data = fetch_transfer_manager_picks(mgr_to_use, next_gw)
    entry_hist = picks_data.get("entry_history", {})
    bank_balance = entry_hist.get("bank", mgr_data.get("last_deadline_bank", 0)) / 10.0
    pick_ids = [p["element"] for p in picks_data.get("picks", [])]'''

new_logic = '''    picks_data = fetch_transfer_manager_picks(mgr_to_use, next_gw)
    entry_hist = picks_data.get("entry_history", {})
    
    # Calculate bank before applying transfers. But wait, if they made transfers, the bank balance is updated!
    # Wait, the bank balance returned by /event/{gw}/picks/ is the bank AT THAT GAMEWEEK's DEADLINE.
    # We should get the live bank balance. Where is it?
    # last_deadline_bank is the bank balance right now!
    # But wait, last_deadline_value and last_deadline_bank in entry are from the last deadline.
    # What if they made a transfer? Their bank changes!
    # Let's adjust bank balance using the transfer costs.
    base_bank = entry_hist.get("bank", mgr_data.get("last_deadline_bank", 0))
    
    picks_list = picks_data.get("picks", [])
    pick_ids = [p["element"] for p in picks_list]
    pending_transfers = fetch_transfer_manager_transfers(mgr_to_use)
    if pending_transfers:
        for t in reversed(pending_transfers):
            if t.get("event") == next_gw:
                out_id = t.get("element_out")
                in_id = t.get("element_in")
                out_cost = t.get("element_out_cost")
                in_cost = t.get("element_in_cost")
                if out_id in pick_ids:
                    idx = pick_ids.index(out_id)
                    pick_ids[idx] = in_id
                    # Adjust bank
                    base_bank = base_bank + out_cost - in_cost
                    for p in picks_list:
                        if p["element"] == out_id:
                            p["element"] = in_id
                            break
                            
    bank_balance = base_bank / 10.0'''

text = text.replace(old_logic, new_logic)

with open('tabs/transfer_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Patched transfer analyzer")
