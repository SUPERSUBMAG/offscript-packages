"""OS001 4.4.11 – Release-Vorbereitung der Lab-Arbeitsfassung /os-lab-player (lokal, liest nur).
Entfernt ausschliesslich Lab-only-Teile; alles andere bleibt zeichengleich (wird geprueft):
 1. alter Player (.os029-mp[data-os-mp-old], nur noch Vergleichsversion)
 2. Lab-Schalter-Skript (data-ssmp-lab / ?mp=old) im Mount-Embed
 3. zwei Lab-Regeln (+Kommentar) fuer die ?mp=old-Umschaltung
"""
import sys,re,hashlib
sys.path.insert(0,'/home/claude/offscript-packages/tools')
from lab2cms import parse,walk,has_class
src=open(sys.argv[1]).read()
b0=src.index('<body'); b1=src.index('>',b0)+1; b2=src.rindex('</body>'); body=src[b1:b2]
old=[e for e in walk(parse(body)) if has_class(e,'os029-mp') and any(a[0]=='data-os-mp-old' for a in e.attrs)]
assert len(old)==1; OLD=old[0].html()
LABJS='<script>(function(){var d=document.documentElement;d.setAttribute("data-ssmp-lab","");if(/[?&]mp=old\\b/.test(location.search))d.classList.add("os-mp-old");})();</script>'
LABCSS='/* RADIO SUPERSUB V2 – Lab-Arbeitsfassung: Buehne wie in der freigegebenen Vorschau, alter Player nur mit ?mp=old */html:not(.os-mp-old) .os030-music>.os029-mp{display:none!important}html.os-mp-old .os030-music .os030-sounds{display:none!important}'
removed=[]
for s in (OLD,LABJS,LABCSS):
    assert body.count(s)==1,s[:60]; body=body.replace(s,'',1); removed.append(s)
for bad in ('data-os-mp-old','os-mp-old','mp=old','ssmp-lab"'):
    assert bad not in body.replace('hasAttribute("data-ssmp-lab")',''),bad
out=src[:b1]+body+src[b2:]
# Nachweis: Ausgabe + entfernte Teile = Original (Laengen) und Original ohne die Teile == Ausgabe
chk=src
for s in removed: chk=chk.replace(s,'',1)
assert chk==out
open(sys.argv[2],'w').write(out)
print('ok', len(src), len(out), [len(s) for s in removed], hashlib.sha256(src.encode()).hexdigest()[:16], hashlib.sha256(out.encode()).hexdigest()[:16])
