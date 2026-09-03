import re

with open('tabs/simulator.py', 'r', encoding='utf-8') as f:
  text = f.read()

pattern = r'banner_bg = "linear-gradient.*?</span>\n\s*</div>\n\s*</div>\n\s*"""'
repl = '''banner_bg = "#151d24" if is_dark else "#ffffff"
  banner_border = "rgba(255, 255, 255, 0.08)" if is_dark else "#e2e8f0"
  
  st.markdown(
    f"""
    <div style="background-color:{banner_bg}; border:1px solid {banner_border}; border-radius:8px; padding:0.85rem 1.1rem; margin:0.4rem 0 1.5rem 0; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
          <span style="font-size:1rem; font-weight:700; color:{text_main};">:material/casino:Monte Carlo Gameweek Simulator</span><br>
          <span style="font-size:0.8rem; color:{text_sub};">Stress-test your squad across thousands of probabilistic match outcomes.</span>
        </div>
      </div>
    </div>
    """'''
text = re.sub(pattern, repl, text, flags=re.DOTALL)

with open('tabs/simulator.py', 'w', encoding='utf-8') as f:
  f.write(text)
print("Fixed simulator banner")
