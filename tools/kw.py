# usage: kw.py URL "kw1|kw2" [width]
import sys,re,html,subprocess,tempfile,os
u=sys.argv[1];pat=re.compile(sys.argv[2],re.I);w=int(sys.argv[3]) if len(sys.argv)>3 else 300
f=tempfile.mktemp()
code=subprocess.run(['curl','-sSL','-m','30','-A','Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36','-o',f,'-w','%{http_code} %{content_type}',u],capture_output=True,text=True).stdout
b=open(f,'rb').read() if os.path.exists(f) else b''
if b[:4]==b'%PDF':
  t=subprocess.run(['pdftotext','-layout',f,'-'],capture_output=True,text=True,errors='ignore').stdout
else:
  t=b.decode('utf-8','ignore');t=re.sub(r'(?s)<(script|style)\b.*?</\1>','',t);t=re.sub(r'<br\s*/?>|</(p|tr|li|h\d|div)>','\n',t);t=re.sub(r'<[^>]+>',' ',t);t=html.unescape(t)
t=re.sub(r'[ \t]+',' ',t);t=re.sub(r'\n\s*\n+','\n',t)
print('HTTP',code,'len',len(t))
seen=-10**9;n=0
for m in pat.finditer(t):
  if m.start()-seen<w: continue
  seen=m.start();n+=1
  print('…'+t[max(0,m.start()-w//2):m.start()+w].replace('\n',' / ')+'…')
  if n>=8: break
