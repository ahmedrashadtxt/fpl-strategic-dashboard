import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('col_tgl1, col_tgl2, col_tgl3, col_tgl4 = st.columns([1.5, 1.6, 1.6, 3.5], vertical_alignment="center")', 'col_tgl1, col_tgl2, col_tgl3, col_tgl4, col_pad = st.columns([1.3, 1.4, 1.4, 3.0, 3.5], vertical_alignment="center")')

with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Fixed columns")
