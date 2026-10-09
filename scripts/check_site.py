from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

root = Path(__file__).resolve().parent.parent

class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []; self.ids = set(); self.tags = []; self.lang = None; self.viewport = False
    def handle_starttag(self, tag, pairs):
        attrs = dict(pairs); self.tags.append(tag)
        if tag == 'html': self.lang = attrs.get('lang')
        if tag == 'meta' and attrs.get('name') == 'viewport': self.viewport = True
        if 'id' in attrs: self.ids.add(attrs['id'])
        for key in ['href', 'src']:
            if key in attrs: self.links.append((tag, attrs[key]))

pages = {}
for path in root.glob('*.html'):
    page = Page(); page.feed(path.read_text()); pages[path.name] = page
    assert page.lang == 'en' and page.viewport and 'title' in page.tags and 'main' in page.tags, path
    assert 'script' not in page.tags and 'iframe' not in page.tags, path
    assert 'password=' not in path.read_text() and 'Bearer ' not in path.read_text(), 'Potential credential in public content'
assert set(pages) == {'index.html','support.html','privacy.html'}
for name,page in pages.items():
    for tag, link in page.links:
        parts = urlsplit(link)
        if parts.scheme:
            assert parts.scheme == 'https' and tag == 'a', f'Unexpected external resource: {link}'
            continue
        target = unquote(parts.path) or name
        assert (root / target).is_file(), f'Broken local link: {link}'
        if parts.fragment: assert parts.fragment in pages[target].ids, f'Broken anchor: {link}'
print('3 pages validated: local navigation, mobile metadata, content landmarks and no external embeds.')
