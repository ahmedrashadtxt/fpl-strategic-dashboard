import glob
import re

for filepath in glob.glob('tabs/*.py'):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    orig_content = content
    
    # 1. Fix the trending up/down in the dataframes
    content = content.replace('Market Bullish :material/trending_up: ', 'Market Bullish \u2191')
    content = content.replace('Market Bearish :material/trending_down: ', 'Market Bearish \u2193')
    
    # 2. Fix the comp_badge_icon which is injected into raw HTML
    content = content.replace('comp_badge_icon = ":material/star: "', 'comp_badge_icon = ""')
    content = content.replace('comp_badge_icon = ":material/emoji_events: "', 'comp_badge_icon = ""')
    
    # 3. Clean up the HTML span where comp_badge_icon was injected so it doesn't have an empty leading space
    # Old: {comp_badge_icon} {comp_target_label}
    # We can just leave the space, HTML collapses it anyway. But let's be neat if possible.
    content = content.replace('{comp_badge_icon} {comp_target_label}', '{comp_target_label}')
    
    if content != orig_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Patched {filepath}")

