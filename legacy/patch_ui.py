"""
patch_ui.py  -  professional pastel redesign (lavender / soft green / soft pink).

Run from the folder that contains app.py:   python patch_ui.py

It does three things:
  1. writes style.css                  (the "CSS file": edit it, refresh the browser)
  2. writes .streamlit/config.toml     (colours, fonts, corner radius)
  3. patches app.py to load style.css, drop all emojis and add a top bar
Your logic is not touched. A backup is saved as app_before_ui.py.
You can run this script again at any time to restore the default look.
"""

import os
import re
import shutil
import sys

CSS = r'''/* style.css  -  edit this file to change the look of the app, then refresh the browser. */

@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Source+Serif+4:wght@500;600&display=swap");

:root {
  --ink: #2A2540;
  --muted: #6F6890;
  --line: #D9D1EC;
  --plum: #5B4B8A;
}

/* page frame */
.block-container { max-width: 900px; padding-top: 1.6rem; padding-bottom: 4rem; }
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }

/* top bar */
.topbar {
  display: flex; justify-content: space-between; align-items: center;
  padding-bottom: 0.7rem; margin-bottom: 1.8rem;
  border-bottom: 1px solid var(--line);
  font-size: 0.7rem; letter-spacing: 0.18em; text-transform: uppercase; color: var(--muted);
}
.topbar b { color: var(--ink); font-weight: 600; }

/* small uppercase label above a card title */
.eyebrow {
  font-size: 0.68rem; letter-spacing: 0.2em; text-transform: uppercase;
  color: #8A7FB0; font-weight: 600; margin-bottom: 0.1rem;
}

/* typography */
h1 { letter-spacing: -0.01em; }
h2, h3 { letter-spacing: -0.005em; }
[data-testid="stMetricValue"] { font-family: "Source Serif 4", Georgia, serif; }
[data-testid="stMetricLabel"] { text-transform: uppercase; letter-spacing: 0.1em; font-size: 0.72rem; }
hr { border-color: var(--line); }

/* buttons and upload box */
.stButton > button { font-weight: 500; letter-spacing: 0.02em; padding: 0.45rem 1.4rem; }
[data-testid="stFileUploaderDropzone"] { background: #FBFAFE; border: 1px dashed #BDB2DE; }
'''

TOML = '''# Theme for the app (restart "streamlit run app.py" after changing this file)
[theme]
base = "light"
primaryColor = "#5B4B8A"
backgroundColor = "#F6F3FB"
secondaryBackgroundColor = "#EDE8F7"
textColor = "#2A2540"

font = "Inter:https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap, sans-serif"
headingFont = "Source Serif 4:https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@500;600&display=swap, serif"
headingFontSizes = ["2rem", "1.5rem", "1.2rem"]
headingFontWeights = [600, 600, 600]

baseRadius = "small"
buttonRadius = "small"
borderColor = "#D9D1EC"
showWidgetBorder = true

# success = soft green, error = soft pink, warning = lavender, info = periwinkle
greenColor = "#4C9A73"
greenBackgroundColor = "#DFF0E6"
greenTextColor = "#2B6247"
redColor = "#B5475F"
redBackgroundColor = "#F8E3E8"
redTextColor = "#7E2A40"
yellowColor = "#8A78C2"
yellowBackgroundColor = "#E9E3F7"
yellowTextColor = "#4B3F72"
blueColor = "#7F8FD1"
blueBackgroundColor = "#E8EBF8"
blueTextColor = "#3A4682"

dataframeHeaderBackgroundColor = "#E6E0F4"
dataframeHeaderTextColor = "#3A3358"
dataframeBorderColor = "#D9D1EC"
codeBackgroundColor = "#EFEAF8"
linkColor = "#5B4B8A"
chartCategoricalColors = ["#8E7CC3", "#7FBF9E", "#E59AB0", "#B8A9E3", "#A5D6BC", "#F2C0CE"]

[client]
toolbarMode = "minimal"

[browser]
gatherUsageStats = false
'''

# 1 + 2: always (re)write the two design files
with open("style.css", "w", encoding="utf-8") as f:
    f.write(CSS)
os.makedirs(".streamlit", exist_ok=True)
if os.path.exists(".streamlit/config.toml"):
    shutil.copyfile(".streamlit/config.toml", ".streamlit/config.toml.bak")
with open(".streamlit/config.toml", "w", encoding="utf-8") as f:
    f.write(TOML)
print("Wrote style.css and .streamlit/config.toml")

# 3: patch app.py (only once)
with open("app.py", encoding="utf-8") as f:
    s = f.read()

if "def load_css" in s:
    sys.exit("app.py is already patched. The design files were refreshed. Restart the app to see them.")


def need(cond, what):
    if not cond:
        sys.exit(f"Could not patch app.py ({what}). app.py was NOT changed. Send me this message.")


# helper + top bar, injected right before the router
router = '{"home": home_page, "input": input_page, "result": result_page}[st.session_state.page]()'
need(s.count(router) == 1, "router line")
s = s.replace(router, '''def load_css():
    """Injects style.css (the app's stylesheet) into the page."""
    css = (Path(__file__).parent / "style.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


load_css()
st.markdown('<div class="topbar"><b>Social Media Safety Detector</b><span>Digital Threat Analysis</span></div>',
            unsafe_allow_html=True)

''' + router)

if "from pathlib import Path" not in s:
    need("import hashlib\n" in s, "imports")
    s = s.replace("import hashlib\n", "import hashlib\nfrom pathlib import Path\n", 1)

# icons on the welcome cards become module numbers
numbers = {"DEEPFAKE": "01", "SENTIMENT": "02", "FRAUD": "03", "PROPAGANDA": "04"}
s, n = re.subn(r'(\n    (DEEPFAKE|SENTIMENT|FRAUD|PROPAGANDA): \()"[^"]*"(, )',
               lambda m: f'{m.group(1)}"{numbers[m.group(2)]}"{m.group(3)}', s)
need(n == 4, "tool list")

old = '                st.subheader(f"{icon} {name}")\n'
need(s.count(old) == 1, "card title")
s = s.replace(old, '                st.markdown(f\'<div class="eyebrow">Module {icon}</div>\', unsafe_allow_html=True)\n'
                   '                st.subheader(name)\n')

# welcome page wording
s, n1 = re.subn(r'st\.title\("[^"]*Social Media Safety Detector"\)', 'st.title("Analysis Tools")', s)
s = s.replace('st.write("Welcome! Choose a tool to get started.")', 'st.write("Select a tool to begin an analysis.")')
s = s.replace('st.button("← Back")', 'st.button("Back")')
s = re.sub(r',\s*page_icon="[^"]*"', "", s)

# remove every emoji
s = re.sub("[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]", "", s)
s = re.sub(r'"## +', '"## ', s)

shutil.copyfile("app.py", "app_before_ui.py")
with open("app.py", "w", encoding="utf-8") as f:
    f.write(s)
print("Patched app.py. Backup saved as app_before_ui.py. Now run: streamlit run app.py")
