import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_logic = '''            if super_team_mode:
                comp_data = dream_team_data or motw_manager_data
                comp_title = "Super Team"
            else:
                comp_data = motw_manager_data or dream_team_data
                raw_title = comp_data.get("manager_name", "Manager of the Week") if comp_data else "Top Performer"
                comp_title = (raw_title[:20] + "..") if len(raw_title) > 22 else raw_title'''

new_logic = '''            if super_team_mode:
                comp_data = dream_team_data or motw_manager_data
                raw_title = comp_data.get("manager_name", "Team of the Week") if comp_data else "Super Team"
                comp_title = (raw_title[:20] + "..") if len(raw_title) > 22 else raw_title
            else:
                comp_data = motw_manager_data or dream_team_data
                raw_title = comp_data.get("manager_name", "Manager of the Week") if comp_data else "Top Performer"
                comp_title = (raw_title[:20] + "..") if len(raw_title) > 22 else raw_title'''

text = text.replace(old_logic, new_logic)

with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Patched comp_title logic")
