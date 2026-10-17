"""Builds data/municipalities.json from official raw sources in data/raw/.
Sources: Census 2020 county subdivision codes; NJ Treasury Div. of Taxation 2025 General Tax Rates PDF
and 2026 County Equalization Tables; NJ.gov County & Municipal Web Sites directory; DCA Fire Code Enforcement directory (2021)."""
import json,re,difflib,os
R='data/raw/'
COUNTIES=[('001','Atlantic','Atlantic'),('009','Cape May','CapeMay'),('011','Cumberland','Cumberland'),('033','Salem','Salem'),
          ('015','Gloucester','Gloucester'),('007','Camden','Camden'),('005','Burlington','Burlington'),('029','Ocean','Ocean')]
def norm(s):
  s=s.lower().replace('&','and');s=re.sub(r'\bboro\b','borough',s);s=re.sub(r'\btwp\b','township',s)
  s=re.sub(r'[^a-z ]','',s.replace('-',' '));s=re.sub(r'\s+',' ',s).strip()
  s=re.sub(r'\bcity city$','city',s)
  return s
# --- census
cen=[l.rstrip('\n').split('|') for l in open(R+'st34_nj_cousub2020.txt')][1:]
# --- tax rates 2025 (pdf text)
tx={};cur=None
for l in open(R+'tr2025.txt'):
  m=re.match(r'^\s+(\w[\w ]+?) County\s*$',l)
  if m: cur=m.group(1).strip();continue
  m=re.match(r'^(\S.*?)\s{2,}(\d+\.\d+)\s+(\d+\.\d+)\s*$',l)
  if m and cur: tx.setdefault(cur,{})[norm(m.group(1))]=(m.group(1).strip(),float(m.group(2)),float(m.group(3)))
eq=json.load(open(R+'eq2026.json'))
links=json.load(open(R+'njgov_links.json'))
lnorm={}
for k,v in links.items():
  lnorm.setdefault(norm(k),(k,v))
lea=json.load(open(R+'lea_parsed.json'))
leaby={}
for v in lea.values(): leaby.setdefault(v['code'][:2],[]).append(v)
LEAC={'Atlantic':'01','Burlington':'03','Camden':'04','Cape May':'05','Cumberland':'06','Gloucester':'08','Ocean':'15','Salem':'17'}
MANUAL_LINK={ # verified by fetching the site (title/county mention) on 2026-10-17
 'Avalon borough':('Avalon (official site)','https://avalonboro.net/'),
 'Cape May Point borough':('Cape May Point (official site)','https://www.capemaypoint.org/'),
 'Port Republic city':('Port Republic (NJ.gov directory lists as "Port Republic Borough")',None),
 'Berlin borough':('Berlin','https://www.berlinnj.org/'),
 'Bordentown city':('Bordentown, City of','https://www.cityofbordentown.com/'),
 'Gloucester City city':('Gloucester City','https://www.cityofgloucester.org/'),
}
# NJ.gov directory entries whose name is ambiguous statewide and that point to a town in ANOTHER county (or unconfirmed): never use
EXCLUDE_LINK={'Washington township','Springfield township','Ocean township','Fairfield township','Greenwich township'}
def slug(s): return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')
LEAFIX={'Penns Grove borough':'1707','Pilesgrove township':'1709','Pittsgrove township':'1710','Upper Pittsgrove township':'1714','Edgewater Park township':'0312','Plumsted township':'1523','Stone Harbor borough':'0510'}
def strict(key,cands):
  if key in cands: return key
  base=lambda s:re.sub(r'\b(city|borough|township|town)\b','',s).strip()
  typ=lambda s:(re.findall(r'\b(city|borough|township|town)\b',s) or [None])[-1]
  hits=[c for c in cands if base(c)==base(key) and typ(c) in (None,typ(key))]
  allb=[base(x) for x in cands]
  return hits[0] if len(hits)==1 and allb.count(base(key))==1 else None
def match(key,cands):
  if key in cands: return key
  # try without type words
  base=lambda s:re.sub(r'\b(city|borough|township|town)\b','',s).strip()
  b={base(c):c for c in cands}
  if base(key) in b and list(map(base,cands)).count(base(key))==1: return b[base(key)]
  m=difflib.get_close_matches(key,list(cands),n=1,cutoff=0.86)
  return m[0] if m else None
out=[];issues=[]
for fp,cn,ek in COUNTIES:
  eqd={norm(n):(n,r,tv) for n,r,tv in eq[ek]}
  for st,sfp,cfp,cname,csfp,ns,name,cls,fs in cen:
    if cfp!=fp or csfp=='00000': continue
    if name=='Pine Valley borough':
      issues.append('Pine Valley borough (Census 2020) merged into Pine Hill borough effective 2022; omitted (not in 2025 tax-rate or 2026 equalization tables).');continue
    disp=re.sub(r' (city|borough|township|town)$',lambda m:' '+m.group(1).title(),name)
    disp=disp.replace('City City','City')
    k=norm(name)
    t=match(k,tx[cn]);e=match(k,eqd)
    if not t: issues.append(f'no tax match {name}')
    if not e: issues.append(f'no eq match {name}')
    web=None
    if name in MANUAL_LINK:
      lab,u=MANUAL_LINK[name]
      if u is None: u=links.get('Port Republic Borough')
      web=dict(label=lab,url=u) if u else None
    elif name not in EXCLUDE_LINK:
      lk=strict(k,lnorm)
      if lk: web=dict(label=lnorm[lk][0],url=lnorm[lk][1])
    # LEA (DCA 2021 directory)
    cands={norm(v['name']):v for v in leaby.get(LEAC[cn],[]) if not v['code'].endswith('00')}
    mm=strict(k,cands) or LEAFIX.get(name);lc=cands.get(mm) if mm in cands else (lea.get(mm) if mm else None)
    out.append(dict(slug=slug(cn+'-'+disp.replace(' City','-city') if False else disp)+'-'+slug(cn)+'-county' if False else slug(disp), name=disp, census_name=name, geoid='34'+fp+csfp, county=cn,
      tax=dict(name=t and tx[cn][t][0], general_rate=t and tx[cn][t][1], effective_rate=t and tx[cn][t][2]) if t else None,
      eq=dict(name=eqd[e][0], ratio=round(eqd[e][1],2), true_value=eqd[e][2]) if e else None,
      website=web,
      lea=dict(code=lc['code'],dir_name=lc['name'],enf=lc['enf'],smoke_name=lc['smoke_name'],smoke_addr=lc['smoke_addr'],smoke_phone=lc['smoke_phone'],page=lc['page']) if lc else None))
# disambiguate slugs
from collections import Counter
c=Counter(o['slug'] for o in out)
for o in out:
  if c[o['slug']]>1: o['slug']=o['slug']+'-'+slug(o['county'])
json.dump(out,open('data/municipalities.json','w'),indent=1)
print(len(out),'municipalities');print('\n'.join(issues))
print('no website:',[o['name'] for o in out if not o['website']])
print('no lea:',[o['name'] for o in out if not o['lea']])
