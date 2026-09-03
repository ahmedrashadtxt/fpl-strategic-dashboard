import os

charmap = {
    128161: ':material/lightbulb:',
    9999: ':material/edit:',
    127769: ':material/dark_mode:',
    127774: ':material/light_mode:',
    128073: ':material/arrow_right_alt:',
    128100: ':material/person:',
    128081: ':material/emoji_events:',
    128220: ':material/receipt_long:',
    128994: ':material/circle:',
    127967: ':material/stadium:',
    128202: ':material/bar_chart:',
    128300: ':material/search:',
    128308: ':material/circle:',
    11088: ':material/star:',
    128737: ':material/shield:',
    127894: ':material/emoji_events:',
    128070: ':material/arrow_upward:',
    128274: ':material/lock:',
    128203: ':material/content_paste:',
    128260: ':material/sync:',
    9989: ':material/check_circle:',
    9203: ':material/hourglass_bottom:',
    127919: ':material/my_location:',
    128269: ':material/search:',
    9201: ':material/timer:',
    127963: ':material/account_balance:',
    128214: ':material/menu_book:',
    9888: ':material/warning:',
    127775: ':material/star:',
    127922: ':material/casino:',
    127314: ':material/looks_one:',
    127333: ':material/looks_two:',
    9881: ':material/settings:',
    9876: ':material/swords:',
    128736: ':material/build:',
    9878: ':material/balance:',
    9889: ':material/bolt:',
    128240: ':material/newspaper:',
    129681: ':material/chair:',
    128200: ':material/trending_up:',
    128201: ':material/trending_down:',
    128197: ':material/calendar_month:',
    127183: ':material/style:',
    128101: ':material/group:',
    10060: ':material/close:',
    128190: ':material/save:',
    128640: ':material/rocket:',
    9940: ':material/block:',
    128683: ':material/do_not_disturb:',
}

for root, dirs, files in os.walk('.'):
    if '.git' in root or '.venv' in root: continue
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    text = f.read()
            except Exception:
                try:
                    with open(filepath, 'r', encoding='utf-16') as f:
                        text = f.read()
                except Exception:
                    continue
            
            new_text = ""
            for c in text:
                if ord(c) > 8192 and c not in '£·°—‘’“”✓─┬┼┴│┌┐└┘':
                    if ord(c) in charmap:
                        new_text += charmap[ord(c)] + " "
                    elif ord(c) == 65039:
                        pass # Variation selector
                    else:
                        pass # Strip it
                else:
                    new_text += c
            
            # Remove double spaces created by adding " " after material icons
            new_text = new_text.replace(':material/lightbulb: ', ':material/lightbulb: ')
            new_text = new_text.replace(':material/stadium: ', ':material/stadium: ')
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_text)

print("Done stripping and mapping emojis.")
