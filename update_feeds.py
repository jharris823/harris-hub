"""Harris Hub v2.2: scholarly discoveries and public news; no eBay API or listing storage."""
import datetime as dt
import html
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'data' / 'feeds.json'
HEADERS = {'User-Agent':'HarrisHub/2.1 (personal noncommercial discovery; contact via GitHub repo)', 'Accept':'application/json, application/rss+xml, application/xml, text/xml, */*'}
QUERIES = {
 'comics':['Golden Age comic books auction Batman Wonder Woman','comic book collecting vintage price guide'],
 'research':['global health politics health policy governance','health technology assessment policy diffusion','Thailand health policy universal coverage'],
 'scifi':['science fiction TV series premiere renewal','new science fiction books post apocalyptic'],
 'sports':['college football SEC Big Ten AP top 25 Wisconsin LSU'],
 'lastz':['Last Z Survival Shooter updates redeem codes'],
}
TOPICS = ['health technology assessment policy','Thailand universal health coverage','global health governance','political determinants of public health','policy diffusion health systems']

def get(url,headers=None,tries=2):
 for attempt in range(tries):
  try:
   req=urllib.request.Request(url,headers={**HEADERS,**(headers or {})})
   with urllib.request.urlopen(req,timeout=22) as response: return response.read(3000000)
  except (urllib.error.URLError,TimeoutError,OSError) as exc:
   print('Request failed:',str(exc)[:160]);time.sleep(1+attempt)
 return None

def rss(data,source):
 try: root=ET.fromstring(data)
 except ET.ParseError: return []
 out=[]
 for el in root.findall('./channel/item')[:12]:
  title=html.unescape(el.findtext('title') or '').strip();url=(el.findtext('link') or '').strip()
  if title and url.startswith(('https://','http://')):out.append({'title':title[:220],'url':url,'source':source,'date':(el.findtext('pubDate') or '')[:45]})
 return out

def news(query):
 q=urllib.parse.quote(query)
 for name,url in [('Google News',f'https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en'),('Bing News',f'https://www.bing.com/news/search?q={q}&format=rss')]:
  data=get(url,tries=1)
  if data:
   items=rss(data,name)
   if items:return items
 return []

def abstract_text(index):
 if not isinstance(index,dict):return ''
 tokens=[]
 for word,positions in index.items():
  for pos in positions:tokens.append((pos,word))
 return ' '.join(word for _,word in sorted(tokens))[:550]

def openalex():
 out=[]
 cutoff=(dt.date.today()-dt.timedelta(days=550)).isoformat()
 for topic in TOPICS:
  params=urllib.parse.urlencode({'search':topic,'filter':'from_publication_date:'+cutoff,'per_page':12,'sort':'publication_date:desc'})
  data=get('https://api.openalex.org/works?'+params,tries=1)
  if not data:continue
  try:works=json.loads(data).get('results',[])
  except (ValueError,TypeError):continue
  for w in works:
   title=w.get('title') or '';url=w.get('doi') or (w.get('best_oa_location') or {}).get('landing_page_url') or w.get('id')
   if not (title and isinstance(url,str) and url.startswith('https://')):continue
   authors=', '.join(a.get('author',{}).get('display_name','') for a in w.get('authorships',[])[:4])
   out.append({'id':w.get('id'),'title':title[:220],'url':url,'source':'OpenAlex','authors':authors[:160], 'date':w.get('publication_date',''), 'why':'Research match: '+topic, 'summary':abstract_text(w.get('abstract_inverted_index')),'kind':'publication','score':40})
  time.sleep(.35)
 return out

def unique(items,cap=50):
 seen=set();out=[]
 for item in items:
  key=str(item.get('id') or re.sub(r'\W+','',item.get('title','').lower())[:100])
  if key not in seen and item.get('url','').startswith('https://'):
   seen.add(key);out.append(item)
  if len(out)>=cap:break
 return out

def main():
 try:previous=json.loads(OUT.read_text(encoding='utf-8'))
 except (OSError,ValueError):previous={}
 discoveries=dict(previous.get('discoveries') or {})
 papers=unique(openalex(),45)
 if papers:discoveries['research']=papers
 else:print('Keeping previous scholarly discoveries')
 listings=unique(ebay_listings(),45)
 if listings:discoveries['comics']=listings
 else:print('Keeping previous listings if any; verify availability before buying')
 feeds={};fresh=bool(papers)
 for category,queries in QUERIES.items():
  items=[]
  for query in queries:items.extend(news(query));time.sleep(.2)
  items=unique(items,20)
  feeds[category]=items or previous.get('feeds',{}).get(category,[])
  fresh=fresh or bool(items)
  print(category,'news:',len(feeds[category]))
 if not fresh and not any(feeds.values()) and not any(discoveries.values()):raise RuntimeError('No available sources and no previous data')
 stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC') if fresh else previous.get('updated','')
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps({'updated':stamp,'feeds':feeds,'discoveries':discoveries},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print('Discovery counts:',{k:len(v) for k,v in discoveries.items()})

if __name__=='__main__':main()
