import re

with open('tabs/simulator.py', 'r', encoding='utf-8') as f:
  text = f.read()

# 1. Change columns from 4 to 3
text = text.replace('b1, b2, b3, b4 = st.columns(4)', 'b1, b2, b3 = st.columns(3)')

# 2. Remove b3 block for budget dream 15, and change b4 to b3
b3_pattern = r'\s*with b3:\n\s*if st\.button\(":material/star:Budget Dream 15".*?st\.rerun\(\)'
text = re.sub(b3_pattern, '', text, flags=re.DOTALL)
text = text.replace('with b4:', 'with b3:')

# 3. Fix compare_mode
compare_pattern = r'compare_mode = None\n\s*if compare_rival:\n\s*compare_mode = st\.radio\("Benchmark:", \["My Current Squad vs Transfer Plan", "My Squad vs Dream 15"\], label_visibility="collapsed"\)'
compare_repl = r'''compare_mode = None
    if compare_rival:
      compare_mode = "My Current Squad vs Transfer Plan"
      st.caption("Benchmark:My Active Squad vs Post-Transfer Plan")'''
text = re.sub(compare_pattern, compare_repl, text, flags=re.DOTALL)

with open('tabs/simulator.py', 'w', encoding='utf-8') as f:
  f.write(text)
print("Removed Dream 15 UI from simulator")
