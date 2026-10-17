import sys,re,html,subprocess
u=sys.argv[1];n=int(sys.argv[2]) if len(sys.argv)>2 else 6000;kw=sys.argv[3] if len(sys.argv)>3 else None
r=subprocess.run(['curl','-sSL','-m','25','-A','Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36','-w','\n__CODE__%{http_code}',u],capture_output=True,text=True,errors='ignore').stdout
code=r.rsplit('__CODE__',1)[-1];t=r.rsplit('__CODE__',1)[0]
t=re.sub(r'(?s)<(script|style|nav|header|footer)\b.*?</\1>','',t);t=re.sub(r'(?s)<!--.*?-->','',t);t=re.sub(r'<br\s*/?>|</(p|tr|li|h\d|div)>','\n',t);t=re.sub(r'<[^>]+>','',t);t=html.unescape(t)
t=re.sub(r'[ \t]+',' ',t);t=re.sub(r'\n\s*\n+','\n',t)
i=0
if kw:
  i=t.lower().find(kw.lower());i=max(0,i-200)
print('HTTP',code);print(t[i:i+n])
