import re

with open('tabs/simulator.py', 'r', encoding='utf-8') as f:
  text = f.read()

# 1. Change columns from 4 to 3
text = text.replace('b1, b2, b3, b4 = st.columns(4)', 'b1, b2, b3 = st.columns(3)')

# 2. Remove b3 block for budget dream 15, and change b4 to b3
b3_pattern = r'\s*with b3:\n\s*if st\.button\(":material/star:Budget Dream 15".*?st\.rerun\(\)'
text = re.sub(b3_pattern, '', text, flags=re.DOTALL)
text = text.replace('with b4:', 'with b3:')

# 3. Remove compare_mode options that include Budget Dream 15?
# Let's see if compare_mode has Budget Dream 15
# I'll just change the text if compare_mode includes it
# If the user says "remove the budget dream 15 in simulator.py", I will also remove it from compare_mode
