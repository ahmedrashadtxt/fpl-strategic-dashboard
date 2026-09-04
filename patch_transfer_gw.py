import re

with open('tabs/transfer_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

pattern = re.compile(r"    next_gw_row = events_df\[events_df\[\"is_next\"\] == 1\]\n    next_gw = int\(next_gw_row\[\"id\"\].values\[0\]\) if not next_gw_row\.empty else current_gw")

new_logic = '''    import time
    now_epoch = int(time.time())
    upcoming_gws = []
    for _, r in events_df.iterrows():
        is_fin = str(r.get("finished", "")).strip().lower() in ["1", "true", "yes"]
        is_cur = str(r.get("is_current", "")).strip().lower() in ["1", "true", "yes"]
        try:
            dl_epoch = int(r.get("deadline_time_epoch", 2000000000))
        except (ValueError, TypeError):
            dl_epoch = 2000000000
        if not is_fin and not (is_cur or dl_epoch <= now_epoch):
            upcoming_gws.append(int(r["id"]))
            
    next_gw = upcoming_gws[0] if upcoming_gws else current_gw'''

new_text = pattern.sub(new_logic, text)

if new_text != text:
    with open('tabs/transfer_analyzer.py', 'w', encoding='utf-8') as f:
        f.write(new_text)
    print("Patched transfer_analyzer.py")
else:
    print("Regex failed to match in transfer_analyzer.py")
