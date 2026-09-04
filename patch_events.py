import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_logic = '''        finished_gw_ids = (
            [int(r["id"]) for _, r in events_df[events_df["finished"] == 1].iterrows()]
            if "finished" in events_df.columns
            else []
        )
        next_gw_row = events_df[events_df["is_next"] == 1]
        next_gw_id = int(next_gw_row["id"].values[0]) if not next_gw_row.empty else current_gw

        ongoing_gw_ids = [
            int(r["id"]) for _, r in events_df.iterrows()
            if int(r["id"]) not in finished_gw_ids and int(r["id"]) < next_gw_id
        ]
        ongoing_gw = ongoing_gw_ids[0] if ongoing_gw_ids else None
        last_finished_gw = max(finished_gw_ids) if finished_gw_ids else None'''

new_logic = '''        import time
        now_epoch = int(time.time())

        finished_gw_ids = (
            [int(r["id"]) for _, r in events_df[events_df["finished"] == 1].iterrows()]
            if "finished" in events_df.columns
            else []
        )

        ongoing_gw_ids = []
        for _, r in events_df.iterrows():
            gw_id = int(r["id"])
            if gw_id in finished_gw_ids:
                continue
            if r.get("is_current") == 1 or (not r.get("finished") and r.get("deadline_time_epoch", 2000000000) <= now_epoch):
                ongoing_gw_ids.append(gw_id)

        ongoing_gw = ongoing_gw_ids[0] if ongoing_gw_ids else None
        last_finished_gw = max(finished_gw_ids) if finished_gw_ids else None

        upcoming_gws = [
            int(r["id"]) for _, r in events_df.iterrows()
            if int(r["id"]) not in finished_gw_ids and int(r["id"]) not in ongoing_gw_ids
        ]
        next_gw_id = upcoming_gws[0] if upcoming_gws else current_gw'''

text = text.replace(old_logic, new_logic)

with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Patched event logic")
