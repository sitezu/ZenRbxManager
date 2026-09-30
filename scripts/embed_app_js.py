"""Keep the canonical JS source in sync with the self-contained desktop HTML.

Run after editing web/assets/app.js. The embedded script runs at the end of body.
The server substitutes ZEN_TOKEN at request time; never embed a real token.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
html_file = ROOT / 'web/index.html'
js_file = ROOT / 'web/assets/app.js'
start = '<!-- BEGIN EMBEDDED APP SCRIPT -->'
end = '<!-- END EMBEDDED APP SCRIPT -->'
html = html_file.read_text(encoding='utf-8')
js = js_file.read_text(encoding='utf-8').rstrip()
if '</script' in js.lower():
    raise ValueError('JavaScript contains an HTML script-closing tag; cannot embed it directly.')
block = f'{start}\n<script>\n{js}\n</script>\n{end}'
if start in html:
    html, count = re.subn(re.escape(start) + r'.*?' + re.escape(end), lambda _: block, html, count=1, flags=re.S)
    assert count == 1 and html.count(start) == 1 and html.count(end) == 1
else:
    assert html.count('</body>') == 1
    html = html.replace('</body>', block + '\n</body>')
html_file.write_text(html, encoding='utf-8')
print('Embedded JavaScript into', html_file, '(', len(js), 'characters )')
