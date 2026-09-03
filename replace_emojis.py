import os
import re

replacements = {
    '???': ':material/stadium:',
    '??': ':material/balance:',
    '??': ':material/star:',
    '??': ':material/bar_chart:',
    '?': ':material/bolt:',
    '??': ':material/lock:',
    '??': ':material/sync:',
    '??': ':material/style:',
    '??': ':material/target:',
    '?': ':material/check_circle:',
    '??': ':material/content_paste:',
    '??': ':material/chair:',
    '??': ':material/group:',
    '??': ':material/settings:',
    '??': ':material/trending_down:',
    '??': ':material/calendar_month:',
    '??': ':material/casino:',
    '??': ':material/trending_up:',
    '??': ':material/search:',
    '??': ':material/lightbulb:',
    '???': ':material/shield:',
    '??': ':material/swords:',
    '??': ':material/warning:',
    '??': ':material/local_fire_department:',
    '??': ':material/ac_unit:',
    '??': ':material/timer:',
    '?': ':material/sports_soccer:',
    '??': ':material/rocket:',
    '??': ':material/payments:',
    '??': ':material/edit:',
    '??': ':material/trending_down:',
    '??': ':material/trending_up:',
    '??': ':material/menu_book:',
    '??': ':material/emoji_events:',
    '??': ':material/trending_down:',
    '??': ':material/money_off:',
    '??': ':material/work:',
    '??': ':material/autorenew:',
    '?': ':material/check:',
    '?': ':material/close:',
    '??': ':material/warning_amber:',
    '??': ':material/medical_services:',
    '??': ':material/info:',
    '??': ':material/sync:',
    '??': ':material/local_fire_department:',
    '??': ':material/psychology:',
    '??': ':material/ads_click:',
    '?': ':material/star:',
    '??': ':material/timer:',
    '???': ':material/stadium:',
    '??': ':material/balance:',
    '??': ':material/trending_down:',
    '??': ':material/bar_chart:',
    '??': ':material/trending_up:',
    '?': ':material/sports_soccer:',
    '???': ':material/shield:',
    '??': ':material/local_fire_department:',
    '??': ':material/ac_unit:',
    '??': ':material/edit:',
    '?': ':material/check:',
    '??': ':material/autorenew:',
    '??': ':material/work:',
    '??': ':material/money_off:',
    '??': ':material/emoji_events:',
    '??': ':material/calendar_month:',
    '??': ':material/menu_book:',
    '??': ':material/payments:',
    '??': ':material/rocket:',
    '??': ':material/lightbulb:',
    '??': ':material/search:',
    '??': ':material/warning:',
    '??': ':material/star:',
    '??': ':material/chair:',
    '??': ':material/settings:',
    '??': ':material/group:',
    '??': ':material/style:',
    '?': ':material/bolt:',
    '??': ':material/lock:',
    '??': ':material/content_paste:',
    '??': ':material/casino:',
    '??': ':material/ads_click:',
    '?': ':material/check_circle:',
}

# Add some common ones
replacements['??'] = ':material/help:'
replacements['??'] = ':material/shopping_cart:'
replacements['??'] = ':material/person:'
replacements['???'] = ':material/delete:'
replacements['??'] = ':material/chat:'
replacements['??'] = ':material/push_pin:'
replacements['??'] = ':material/folder:'
replacements['??'] = ':material/trending_down:'
replacements['?'] = ':material/add:'
replacements['?'] = ':material/remove:'
replacements['??'] = ':material/attach_money:'
replacements['?'] = ':material/priority_high:'

for root, dirs, files in os.walk('tabs'):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
                
            for emoji, mat in replacements.items():
                text = text.replace(emoji, mat)
                
            # catch any other emojis that might be left
            # Just blindly regex anything > 0x2000 that isn't a known punctuation, but be careful
            # We will just write it back
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()
for emoji, mat in replacements.items():
    text = text.replace(emoji, mat)
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Replaced emojis in tabs and app.py")
