"""Harris Hub v2: public news with scholarly-record enrichment; no API keys."""
import datetime as dt
import email.utils
import html
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'data' / 'feeds.json'
QUERIES = {
    'comics': ['Golden Age comic books auction Batman Wonder Woman', 'comic book collecting vintage price guide'],
    'research': ['global health politics health policy governance', 'health technology assessment policy diffusion', 'Thailand health policy universal coverage'],
    'scifi': ['science fiction TV series premiere renewal', 'new science fiction books post apocalyptic'],
    'sports': ['college football SEC Big Ten AP top 25 Wisconsin LSU'],
    'lastz': ['Last Z Survival Shooter updates redeem codes'],
}
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; HarrisHub/2.0; public research dashboard)', 'Accept': 'application/rss+xml,application/xml,application/json,text/xml,*/*'}

def request(url, tries=2):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=18) as response:
                return response.read(2500000)
        except Exception as exc:
            print('Request failed', i + 1, str(exc)[:160])
            if i + 1 < tries:
                time.sleep(2)
    return None

def rss_items(data, source):
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return []
    items = []
    for el in root.findall('./channel/item')[:12]:
        title = html.unescape(el.findtext('title') or '').strip()
        url = (el.findtext('link') or '').strip()
        if title and url.startswith(('https://', 'http://')):
            items.append({'title': title[:220], 'url': url, 'source': source, 'date': (el.findtext('pubDate') or '')[:45]})
    return items

def news(query):
    q = urllib.parse.quote(query)
    sources = [('Google News', f'https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en'), ('Bing News', f'https://www.bing.com/news/search?q={q}&format=rss')]
    for name, url in sources:
        data = request(url)
        if data:
            items = rss_items(data, name)
            if items:
                print('Retrieved', len(items), name, query)
                return items
    return []

def openalex():
    topics = ['health technology assessment', 'global health governance', 'Thailand universal health coverage', 'politics of public health']
    results = []
    for topic in topics:
        params = urllib.parse.urlencode({'search': topic, 'filter': 'from_publication_date:2025-01-01', 'per-page': 12, 'sort': 'publication_date:desc', 'select': 'id,title,publication_date,doi,primary_location,authorships'})
        data = request('https://api.openalex.org/works?' + params)
        if not data:
            continue
        try:
            works = json.loads(data).get('results', [])
        except (ValueError, TypeError):
            continue
        for w in works:
            title = w.get('title') or ''
            url = w.get('doi') or (w.get('primary_location') or {}).get('landing_page_url') or w.get('id')
            if title and url and url.startswith('https://'):
                authors = ', '.join(a.get('author', {}).get('display_name', '') for a in w.get('authorships', [])[:3])
                results.append({'id': w.get('id'), 'title': title[:220], 'url': url, 'source': 'OpenAlex • '+authors[:80], 'date': w.get('publication_date', ''), 'why': 'Matches your research interests in '+topic, 'score': 30})
        time.sleep(.3)
    return results

def unique(items, cap=20):
    seen = set()
    out = []
    for item in items:
        key = re.sub(r'\W+', '', item['title'].lower())[:100]
        if key not in seen:
            seen.add(key)
            out.append(item)
        if len(out) >= cap:
            break
    return out

def main():
    previous = {}
    if OUT.exists():
        try:
            previous = json.loads(OUT.read_text(encoding='utf-8'))
        except (ValueError, OSError):
            pass
    feeds = {}
    fresh = 0
    for category, queries in QUERIES.items():
        items = openalex() if category == 'research' else []
        for q in queries:
            items.extend(news(q))
            time.sleep(.5)
        items = unique(items)
        if items:
            fresh += len(items)
            feeds[category] = items
        else:
            feeds[category] = previous.get('feeds', {}).get(category, [])
        print(category, len(feeds[category]))
    if fresh == 0 and not any(feeds.values()):
        raise RuntimeError('No sources available and no previously saved headlines.')
    updated = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC') if fresh else previous.get('updated', '')
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({'updated': updated, 'feeds': feeds}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('Fresh items:', fresh)

if __name__ == '__main__':
    main()
