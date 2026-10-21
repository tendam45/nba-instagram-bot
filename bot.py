import os,json,time,hashlib,datetime as dt
from pathlib import Path
from urllib.parse import quote
import requests,feedparser
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).parent; DOC=ROOT/'docs'; IMG=DOC/'images'; IMG.mkdir(parents=True,exist_ok=True)
STATE=ROOT/'state.json'; state=json.loads(STATE.read_text()) if STATE.exists() else {'posted':[]}
S=requests.Session(); S.headers.update({'User-Agent':'NBAEditorialBot/1.0 (personal educational project)'})
DRY=os.getenv('DRY_RUN','true').lower()!='false'
MODE=os.getenv('POST_MODE','scores')
BASE=os.environ.get('PUBLIC_BASE_URL','').rstrip('/')
TOKEN=os.getenv('IG_ACCESS_TOKEN',''); IG=os.getenv('IG_USER_ID',''); VERSION=os.getenv('GRAPH_VERSION','v24.0')
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def font(n): return ImageFont.truetype(FONT,n)
def fetch_json(url):
 r=S.get(url,timeout=25); r.raise_for_status(); return r.json()
def games():
 # ESPN's public endpoint is undocumented; it can change or restrict automated access.
 return fetch_json('https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates='+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d'))['events']
def candidate_scores():
 # Only publish completed games. Limit to a single post per run.
 for e in games():
  comp=e['competitions'][0]; status=e.get('status',{}).get('type',{})
  if not status.get('completed'): continue
  teams=comp['competitors']; home=next(x for x in teams if x['homeAway']=='home'); away=next(x for x in teams if x['homeAway']=='away')
  yield {'key':'score:'+e['id'],'headline':'FINAL SCORE','line1':away['team']['abbreviation']+' '+str(away['score']),'line2':home['team']['abbreviation']+' '+str(home['score']),'caption':f"FINAL: {away['team']['displayName']} {away['score']} — {home['team']['displayName']} {home['score']}. #NBA #Basketball #NBAScores",'source':e.get('links',[{}])[0].get('href','')}
def candidate_news():
 # RSS headlines are not independently verified; do NOT auto-publish by default.
 url='https://news.google.com/rss/search?q='+quote('NBA trade official announced when:1d')+'&hl=en-US&gl=US&ceid=US:en'
 feed=feedparser.parse(S.get(url,timeout=25).content)
 for item in feed.entries[:5]:
  yield {'title':item.title,'url':item.link}
def graphic(post):
 im=Image.new('RGB',(1080,1350),'#10131e'); d=ImageDraw.Draw(im)
 d.rectangle((0,0,1080,22),fill='#ff7134'); d.text((75,110),'COURTSIDE DAILY',font=font(42),fill='white')
 d.text((75,320),post['headline'],font=font(76),fill='#ff7134')
 d.text((75,540),post['line1'],font=font(85),fill='white')
 d.text((75,705),post['line2'],font=font(85),fill='white')
 d.text((75,1200),'NBA • SCORES • NEWS',font=font(32),fill='#aaaaaa')
 name=hashlib.sha256(post['key'].encode()).hexdigest()[:20]+'.jpg'; path=IMG/name
 im.save(path,quality=90); return name
def graph_post(endpoint,params):
 r=S.post(f'https://graph.facebook.com/{VERSION}/{endpoint}',data=params,timeout=45)
 try: data=r.json()
 except Exception: raise RuntimeError('Meta returned non-JSON: '+r.text[:300])
 if not r.ok or 'error' in data: raise RuntimeError('Meta API: '+json.dumps(data))
 return data
def publish(post,name):
 if not (BASE and TOKEN and IG): raise RuntimeError('Set PUBLIC_BASE_URL, IG_ACCESS_TOKEN, IG_USER_ID')
 url=f'{BASE}/images/{name}'
 # GitHub Pages deployment must finish before Meta can fetch this public image.
 for attempt in range(12):
  try:
   r=S.get(url,timeout=20)
   if r.ok and r.headers.get('Content-Type','').startswith('image/') and len(r.content)>1000: break
  except requests.RequestException: pass
  time.sleep(15)
 else: raise RuntimeError('Public image not ready: '+url)
 container=graph_post(f'{IG}/media',{'image_url':url,'caption':post['caption'],'access_token':TOKEN})['id']
 # Images usually process quickly, but check status before publish.
 for _ in range(12):
  r=S.get(f'https://graph.facebook.com/{VERSION}/{container}',params={'fields':'status_code','access_token':TOKEN},timeout=20);r.raise_for_status()
  status=r.json().get('status_code','')
  if status=='FINISHED': break
  if status=='ERROR': raise RuntimeError('Instagram media processing failed')
  time.sleep(10)
 else: raise RuntimeError('Instagram container processing timed out')
 return graph_post(f'{IG}/media_publish',{'creation_id':container,'access_token':TOKEN})['id']
def main():
 if MODE=='news':
  print('News discovery only; headlines require verification:',json.dumps(list(candidate_news())[:3]));return
 pending=ROOT/'pending.json'
 if pending.exists() and not DRY:
  q=json.loads(pending.read_text())
  if q['key'] not in state['posted']:
   mid=publish(q,q['image']);state['posted'].append(q['key']);STATE.write_text(json.dumps(state,indent=2));print('Published',mid)
  pending.unlink(missing_ok=True)
  return
 candidates=[p for p in candidate_scores() if p['key'] not in state['posted']]
 if not candidates: print('No new completed games');return
 p=candidates[0];name=graphic(p);print('Generated:',name,p['caption'])
 if DRY: print('DRY_RUN: not publishing');return
 # Queue image, then publish on a later run once GitHub Pages is live.
 p['image']=name;pending.write_text(json.dumps(p,indent=2));print('Queued for next run after Pages deploy')
if __name__=='__main__': main()
