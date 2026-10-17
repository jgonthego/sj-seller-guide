(function(){
  // Town finder: search + chips
  document.querySelectorAll('.finder').forEach(function(f){
    var q=f.querySelector('#q'),cards=[].slice.call(f.querySelectorAll('.tcard')),cnt=f.querySelector('#count'),filt={f:'all',v:''};
    function run(){var s=(q.value||'').trim().toLowerCase(),n=0;
      cards.forEach(function(c){var ok=(!s||c.dataset.name.indexOf(s)>-1)&&(filt.f==='all'||c.dataset[filt.f]===filt.v);c.style.display=ok?'':'none';if(ok)n++;});
      if(cnt)cnt.textContent='Showing '+n+' of '+cards.length+' towns';}
    q&&q.addEventListener('input',run);
    f.querySelectorAll('.chip').forEach(function(b){b.addEventListener('click',function(){f.querySelectorAll('.chip').forEach(function(x){x.classList.remove('on')});b.classList.add('on');filt={f:b.dataset.f,v:b.dataset.v};run();});});
    run();
  });
  // Transfer fee calculator (mirrors build.py rtf()/gpf())
  var p=document.getElementById('cprice');
  if(p&&window.RTF){var R=window.RTF,red=document.getElementById('cred'),cl=document.getElementById('cclass');
    function tiers(x,t){var f=0;t.forEach(function(r){if(x>r[0]){var top=r[1]===null?x:Math.min(x,r[1]);f+=(top-r[0])/500*r[2];}});return f;}
    function fmt(n){return '$'+Math.round(n).toLocaleString('en-US');}
    function calc(){var x=parseFloat((p.value||'').replace(/[^0-9.]/g,''))||0;
      var k=(red.checked?'reduced':'standard')+(x<=350000?'_le350':'_gt350');var r=tiers(x,R[k]);var g=0;
      if(cl.value==='res')R.gpf.forEach(function(t){if(x>t[0]&&(t[1]===null||x<=t[1]))g=x*t[2]/100;});
      document.getElementById('o-rtf').textContent=fmt(r);document.getElementById('o-gpf').textContent=g?fmt(g):'$0 (n/a)';document.getElementById('o-tot').textContent=fmt(r+g);}
    [p,red,cl].forEach(function(el){el.addEventListener('input',calc);el.addEventListener('change',calc);});calc();}
  // Checklist persistence
  var ck=document.querySelectorAll('.checks input');
  if(ck.length){var key='sjsg-checklist';var st={};try{st=JSON.parse(localStorage.getItem(key)||'{}')}catch(e){}
    ck.forEach(function(c,i){c.checked=!!st[i];c.addEventListener('change',function(){st[i]=c.checked;try{localStorage.setItem(key,JSON.stringify(st))}catch(e){}});});}
})();
