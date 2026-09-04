import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_logic = '''        bank_balance = entry_history.get("bank", mgr_data.get("last_deadline_bank", 0)) / 10.0

        picks_list = picks_data.get("picks", [])
        pick_ids = [p["element"] for p in picks_list]
        
        # Apply any pending transfers for the upcoming gameweek
        pending_transfers = fetch_manager_transfers(mgr_to_use)
        if pending_transfers:
            for t in reversed(pending_transfers):
                if t.get("event") == next_gw_id:
                    out_id = t.get("element_out")
                    in_id = t.get("element_in")
                    if out_id in pick_ids:
                        idx = pick_ids.index(out_id)
                        pick_ids[idx] = in_id
                        # Also update picks_list so order is maintained
                        for p in picks_list:
                            if p["element"] == out_id:
                                p["element"] = in_id
                                break'''

new_logic = '''        base_bank = entry_history.get("bank", mgr_data.get("last_deadline_bank", 0))

        picks_list = picks_data.get("picks", [])
        pick_ids = [p["element"] for p in picks_list]
        
        # Apply any pending transfers for the upcoming gameweek
        pending_transfers = fetch_manager_transfers(mgr_to_use)
        if pending_transfers:
            for t in reversed(pending_transfers):
                if t.get("event") == next_gw_id:
                    out_id = t.get("element_out")
                    in_id = t.get("element_in")
                    out_cost = t.get("element_out_cost")
                    in_cost = t.get("element_in_cost")
                    if out_id in pick_ids:
                        idx = pick_ids.index(out_id)
                        pick_ids[idx] = in_id
                        base_bank = base_bank + out_cost - in_cost
                        # Also update picks_list so order is maintained
                        for p in picks_list:
                            if p["element"] == out_id:
                                p["element"] = in_id
                                break
                                
        bank_balance = base_bank / 10.0'''

text = text.replace(old_logic, new_logic)

with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Patched squad analyzer bank")
