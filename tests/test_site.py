"""Static marketing page checks; no third-party web dependencies required."""
from html.parser import HTMLParser
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.hrefs = []
        self.title = ''
        self._inside_title = False

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == 'title':
            self._inside_title = True
        if 'id' in attributes:
            self.ids.add(attributes['id'])
        if tag == 'a':
            self.hrefs.append(attributes.get('href'))

    def handle_endtag(self, tag):
        if tag == 'title':
            self._inside_title = False

    def handle_data(self, data):
        if self._inside_title:
            self.title += data


def test_website_has_real_product_copy_and_valid_internal_links():
    html = (ROOT / 'site/index.html').read_text(encoding='utf-8')
    page = Page()
    page.feed(html)
    assert 'ZenRbxManager' in page.title
    assert 'Macro recorder' not in html and 'Auto clicker' not in html
    assert '0/68' not in html and 'ZenTask-Setup' not in html
    assert 'https://github.com/sitezu/ZenRbxManager' in page.hrefs
    assert 'ZenRbxManager-v0.1.0-preview.exe' in html
    assert 'This is a preview' in html
    assert 'sitezu.github.io/ZenRbxManager/' in html
    assert all(href[1:] in page.ids for href in page.hrefs if href.startswith('#'))
    assert '/*REFERENCE_CSS*/' not in html
    assert (ROOT / 'site/Zentask-MIT-LICENSE.txt').exists()
    assert (ROOT / 'site/og.png').stat().st_size < 1_000_000


def test_html_visual_reference_keeps_original_ui():
    html = (ROOT / 'web/index.html').read_text(encoding='utf-8')
    assert 'ZenTask-inspired visual layer' in html
    assert 'linear-gradient(135deg,#6366f1,#a855f7)' in html
    assert '<!-- BEGIN EMBEDDED APP SCRIPT -->' in html
    assert '<script src=' not in html
    assert 'width: 100vw;' in html and 'height: 100vh;' in html
    assert 'background-color: #090a0f;' in html
    assert '/*ZEN_TOKEN*/' not in html
    assert 'id="accountList"' in html
    assert (ROOT / 'src/native_ui.py').exists()
    assert 'data-username="ZenMaster99"' not in html


def test_site_is_tiny_without_zentask_media():
    site = ROOT / 'site'
    size = sum(p.stat().st_size for p in site.rglob('*') if p.is_file())
    assert size < 1_000_000
    assert not any(p.suffix in ('.mp4', '.gif') for p in site.rglob('*'))
