"""Check every formatting property in the report against Power BI Desktop's own theme schema."""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
src = Path(r"C:\Program Files\WindowsApps\Microsoft.MicrosoftPowerBIDesktop_2.159.1231.0_x64__8wekyb3d8bbwe\bin\WebView2Resources\minerva\scripts\desktop.reportThemeSchema.json.min.js").read_text(encoding='utf-8', errors='ignore')
a = src.find("JSON.parse('") + len("JSON.parse('"); b = src.rfind("')")
BS = chr(92)  # backslash
def js_unescape(text):
    """Undo the JS single-quoted string escaping (\\\\ -> \\, \\' -> ')."""
    out, i = [], 0
    while i < len(text):
        if text[i] == BS and i + 1 < len(text) and text[i + 1] in (BS, "'"):
            out.append(text[i + 1]); i += 2
        elif text[i] == BS and i + 1 < len(text) and text[i + 1] == "x":
            out.append(BS + "u00" + text[i + 2:i + 4]); i += 4
        else:
            out.append(text[i]); i += 1
    return "".join(out)
raw = js_unescape(src[a:b]).replace(BS + "'", "'")
schema = json.loads(raw)
defs = schema['definitions']

def props(vtype):
    d = defs.get(f'visual-{vtype}')
    if d is None:
        return None
    out = {}
    def collect(dd):
        if '$ref' in dd:
            collect(defs[dd['$ref'].split('/')[-1]])
        for k, v in dd.get('properties', {}).items():
            it = v.get('items', {})
            if '$ref' in it:
                it = defs[it['$ref'].split('/')[-1]]
            out.setdefault(k, set()).update(it.get('properties', {}).keys())
        for sub in dd.get('allOf', []) + dd.get('anyOf', []) + dd.get('oneOf', []):
            collect(sub)
    collect(d)
    return out

bad = 0
for f in Path(sys.argv[1]).glob('*/visuals/*/visual.json'):
    v = json.loads(f.read_text(encoding='utf-8')); t = v['visual']['visualType']
    P = props(t)
    if P is None:
        print('no schema for', t); continue
    for group in ('objects', 'visualContainerObjects'):
        for obj, entries in v['visual'].get(group, {}).items():
            if obj not in P:
                print(f'{t}: unknown object "{obj}"'); bad += 1; continue
            for e in entries:
                for prop in e.get('properties', {}):
                    if prop not in P[obj]:
                        print(f'{t}: {obj}.{prop} not in schema (has: {sorted(P[obj])[:12]})'); bad += 1
print('property problems:', bad)
