"""Free public RSS headline updater for Harris Hub. No keys or subscriptions required."""
import json, re, html, datetime, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path

QUERIES = {
 'comics': ['Golden Age comic books auction Batman Wonder Woman', 'comic book collecting vintage price guide'],
 'research': ['global health politics health policy governance', 'health technology assessment policy diffusion', 'Thailand health policy universal coverage'],
 'scifi': ['science fiction TV series premiere renewal', 'new science fiction books post apocalyptic'],
 'sports': ['college football SEC Big Ten AP top 25 Wisconsin LSU'],
 'lastz': ['Last Z Survival Shooter updates redeem codes'],
}
UA = {'User-Agent': 'Mozilla/5.0 (compatible; HarrisHub/1.0; personal RSS reader)'}

def collect(query):
    url='https://news.google.com/rss/search?q='+urllib.parse.quote(query)+'&hl=en-US&gl=US&ceid=US:en'
    try:
        req=urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=18) as r:
            data=r.read(2_000_000)
        root=ET.fromstring(data)
        results=[]
        for item in root.findall('./channel/item')[:8]:
            title=html.unescape(''.join(item.findtext('title','').splitlines())).strip()
            link=item.findtext('link','').strip()
            date=item.findtext('pubDate','').strip()
            if not link.startswith('https://'):continue
            source=item.findtext('source','Google News')
            results.append({'title':title[:220], 'url':link, 'date':date[:35], 'source':source[:80]})
        return results
    except Exception as exc:
        print('RSS error', query, str(exc)[:150]);return []

p=Path(__file__).parent/'data'/'feeds.json'
previous={}
if p.exists():
    try:previous=json.loads(p.read_text())
    except (OSError,ValueError):pass
feeds={}
for category, queries in QUERIES.items():
    out=[];seen=set()
    for query in queries:
        for x in collect(query):
            key=re.sub(r'\W+','',x['title'].lower())[:100]
            if key not in seen:out.append(x);seen.add(key)
    feeds[category]=out[:12] if out else previous.get('feeds',{}).get(category,[])[:12]
p.parent.mkdir(exist_ok=True)
p.write_text(json.dumps({'updated':datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),'feeds':feeds},indent=2,ensure_ascii=False)+'\n')
print('Updated', {k:len(v) for k,v in feeds.items()})
