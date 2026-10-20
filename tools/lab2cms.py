"""lab2cms – OFF SCRIPT Lab -> CMS-Transfer (lokal, schreibt nichts nach Webflow).

Eingaben (alles nur gelesen):
  --lab      veroeffentlichtes Lab-HTML (Staging)            -> Markup der Ausgabe (Wrapper + Embeds)
  --head     Page-Head-Code der Lab-Seite (API-Export)       -> Styles/Skripte/Preloads, die vor dem Body gelten
  --footer   Page-Footer-Code der Lab-Seite (API-Export)     -> Styles/Skripte am Seitenende
  --manifest Ausgaben-Manifest (JSON)                        -> Paket-ID, Wurzeln der Ausgabe, Lab-only-Bloecke, Lesefassung

Ausgaben (--out):
  dist/issue.min.css, dist/issue.min.js   Paket (Inhalt in Dokument-Reihenfolge, nicht umgeschrieben)
  rt.html                                 Rich-Text-Wert fuer das CMS (Embeds < LIMIT Zeichen)
  sri.json, report.json                   Pruefsummen, Chunk-Groessen, Roundtrip-Ergebnis

Grundregel: Nichts wird inhaltlich umgeschrieben. Styles/Skripte werden nur verschoben, Markup nur in Chunks geteilt.
Der Roundtrip setzt die Chunks so zusammen, wie es der Loader im Browser tut, und muss das Original-Markup
(ohne Style/Skript-Knoten) zeichengenau ergeben – sonst bricht der Build ab.
"""
import argparse, base64, hashlib, html, json, os, re, sys

INVISIBLE = re.compile('[\\u00a0\\u00ad\\u2000-\\u200f\\u2028\\u2029\\u202f\\u205f\\u2060\\u3000\\ufeff]')
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
RAW = {'style', 'script', 'textarea', 'title'}
ATOMIC = {'svg', 'math', 'picture', 'video', 'audio', 'pre', 'textarea', 'select', 'iframe', 'canvas', 'template', 'p', 'h1',
          'h2', 'h3', 'h4', 'h5', 'h6', 'button', 'a', 'span', 'blockquote'}


# ---------------------------------------------------------------- verlustfreier HTML-Baum
class El:
    def __init__(s, tag, start, attrs):
        s.tag, s.start, s.attrs, s.kids, s.end = tag, start, attrs, [], ''

    def html(s):
        return s.start + ''.join(k if isinstance(k, str) else k.html() for k in s.kids) + s.end


ATTR = re.compile(r'''([^\s"'>/=]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>]+)))?''')


def attrs_of(start):
    inner = re.match(r'<[a-zA-Z][^\s/>]*(.*?)/?>$', start, re.S).group(1)
    out = []
    for m in ATTR.finditer(inner):
        v = m.group(2) if m.group(2) is not None else m.group(3) if m.group(3) is not None else m.group(4) if m.group(4) is not None else ''
        out.append([m.group(1), html.unescape(v)])
    return out


TOK = re.compile(r'<!--.*?-->|<(/?)([a-zA-Z][a-zA-Z0-9-]*)((?:[^>"\']|"[^"]*"|\'[^\']*\')*)>', re.S)


def parse(src):
    """Fragment -> Liste von Knoten (str = Text/Kommentar, El = Element). Erwartet wohlgeformtes Webflow-HTML."""
    root = El('#root', '', []); stack = [root]; pos = 0
    while True:
        m = TOK.search(src, pos)
        if not m:
            if pos < len(src): stack[-1].kids.append(src[pos:])
            break
        if m.start() > pos: stack[-1].kids.append(src[pos:m.start()])
        tok = m.group(0)
        if tok.startswith('<!--'):
            stack[-1].kids.append(tok); pos = m.end(); continue
        close, name = m.group(1), m.group(2).lower()
        if close:
            if stack[-1].tag != name:
                raise SystemExit('Nicht wohlgeformt: </%s> bei offenem <%s> (Pos %d)' % (name, stack[-1].tag, m.start()))
            stack[-1].end = tok; stack.pop(); pos = m.end(); continue
        e = El(name, tok, attrs_of(tok)); stack[-1].kids.append(e)
        if name in RAW:
            j = src.lower().index('</' + name, m.end()); k = src.index('>', j) + 1
            e.kids.append(src[m.end():j]); e.end = src[j:k]; pos = k; continue
        if name not in VOID and not tok.endswith('/>'): stack.append(e)
        pos = m.end()
    if len(stack) != 1: raise SystemExit('Nicht geschlossen: <%s>' % stack[-1].tag)
    assert ''.join(k if isinstance(k, str) else k.html() for k in root.kids) == src, 'Parser-Roundtrip fehlgeschlagen'
    return root.kids


def walk(nodes):
    for n in nodes:
        if isinstance(n, El):
            yield n
            yield from walk(n.kids)


def ser(nodes): return ''.join(k if isinstance(k, str) else k.html() for k in nodes)


def has_class(e, c): return any(a[0] == 'class' and c in a[1].split() for a in e.attrs)


# ---------------------------------------------------------------- Code einsammeln
def collect(nodes, css, js, data, links, where):
    """Style/Skript/Preload-Knoten in Dokument-Reihenfolge einsammeln und aus dem Baum entfernen."""
    keep = []
    for n in nodes:
        if isinstance(n, El) and n.tag == 'style':
            media = dict(n.attrs).get('media')
            css.append(('@media %s{%s}' % (media, n.kids[0])) if media else n.kids[0]); continue
        if isinstance(n, El) and n.tag == 'script':
            a = dict(n.attrs)
            if 'src' in a: raise SystemExit('Externes Skript im Lab-Code (%s): %s – nicht unterstuetzt' % (where, a['src']))
            if a.get('type') == 'application/json': data.append([a.get('id'), n.kids[0]]); continue
            js.append(n.kids[0]); continue
        if isinstance(n, El) and n.tag == 'link' and dict(n.attrs).get('rel') in ('preload', 'preconnect', 'modulepreload'):
            links.append(n.html()); continue
        if isinstance(n, El): n.kids = collect(n.kids, css, js, data, links, where)
        keep.append(n)
    return keep


def strip_lab_only(src, markers):
    """Lab-only-Bloecke entfernen: vom Marker-Kommentar bis vor den naechsten Kommentar."""
    for mk in markers:
        i = src.find('<!-- ' + mk)
        if i < 0: raise SystemExit('Lab-only-Marker nicht gefunden: ' + mk)
        j = src.find('<!--', src.index('-->', i))
        src = src[:i] + (src[j:] if j >= 0 else '')
    return src


# ---------------------------------------------------------------- Chunking + Roundtrip
class Chunker:
    def __init__(s, limit): s.limit, s.chunks, s.n, s.raw = limit, [], 0, {}

    def wid(s): s.n += 1; return 'w%d' % s.n

    def marker(s, path):
        return '<template data-os-chunk="%s"></template>' % html.escape(json.dumps({'p': path}, ensure_ascii=False, separators=(',', ':')), quote=True)

    def emit(s, nodes, path):
        cur, size, base = [], 0, len(s.marker(path))
        for n in nodes:
            h = n if isinstance(n, str) else n.html()
            if base + size + len(h) <= s.limit:
                cur.append(h); size += len(h); continue
            if cur: s.chunks.append((path, ''.join(cur))); cur, size = [], 0
            if base + len(h) <= s.limit:
                cur.append(h); size = len(h); continue
            if isinstance(n, str) or n.tag in ATOMIC or not any(isinstance(k, El) for k in n.kids):
                raise SystemExit('Element zu gross und nicht teilbar (%d Zeichen): %s' % (len(h), (h[:80] if isinstance(h, str) else h)))
            w = s.wid(); s.raw[w] = n.start
            s.emit(n.kids, path + [[w, n.tag, n.attrs]])
        if cur: s.chunks.append((path, ''.join(cur)))


def rebuild(chunks, raw):
    """Zusammensetzen wie der Loader: Wrapper aus dem Pfad anlegen, Chunk-Inhalt anhaengen, Embed-Hülle verwerfen."""
    top, wraps = [], {}

    def node(path):
        kids = top
        for wid, tag, attrs in path:
            if wid not in wraps:
                assert attrs_of(raw[wid]) == attrs and raw[wid].lower().startswith('<' + tag), wid
                w = [raw[wid], [], '</%s>' % tag]; wraps[wid] = w; kids.append(w)
            kids = wraps[wid][1]
        return kids

    for path, content in chunks:
        node(path).append(content)

    def out(items): return ''.join(x if isinstance(x, str) else x[0] + out(x[1]) + x[2] for x in items)
    return out(top)


def canon(nodes):
    """Vergleichsform des Originals: Start-Tags so, wie der Loader sie per setAttribute erzeugt (Attribut-Reihenfolge bleibt)."""
    out = []
    for n in nodes:
        if isinstance(n, str): out.append(n); continue
        start = '<%s%s>' % (n.tag, ''.join(' %s="%s"' % (a, html.escape(v, quote=True)) if v != '' else ' %s=""' % a for a, v in n.attrs))
        out.append(start + canon(n.kids) + n.end if n.tag not in VOID else start)
    return ''.join(out)


def split_css(css, limit):
    """CSS verlustfrei an Regelgrenzen (Klammertiefe 0, ausserhalb von Strings/Kommentaren) in Stuecke <= limit teilen."""
    cuts, depth, i, n, q = [0], 0, 0, len(css), None
    last_ok = 0
    while i < n:
        c = css[i]
        if q:
            if c == '\\': i += 2; continue
            if c == q: q = None
        elif css.startswith('/*', i):
            k = css.find('*/', i + 2); i = (n if k < 0 else k + 2); continue
        elif c in '"\'': q = c
        elif c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0: last_ok = i + 1
        elif c == ';' and depth == 0: last_ok = i + 1
        if i + 1 - cuts[-1] > limit:
            if last_ok <= cuts[-1]: raise SystemExit('CSS-Regel groesser als Embed-Grenze')
            cuts.append(last_ok)
        i += 1
    cuts.append(n)
    return [css[cuts[k]:cuts[k + 1]] for k in range(len(cuts) - 1) if cuts[k + 1] > cuts[k]]


def sri(b): return 'sha384-' + base64.b64encode(hashlib.sha384(b).digest()).decode()


def main():
    ap = argparse.ArgumentParser()
    for k in ('lab', 'head', 'footer', 'manifest', 'out'): ap.add_argument('--' + k, required=True)
    ap.add_argument('--vgwort', default=None,
                    help='vollstaendige VG-WORT-Zaehlmarke (https://vgNN.met.vgwort.de/na/<32 hex>); nur fuer die deutsche Fassung. '
                         'Wird als letztes, eigenes Embed ohne Chunk-Marker angehaengt (statisch im HTML, kein JS, genau einmal).')
    ap.add_argument('--mode', choices=('cdn', 'inline-sync', 'inline-async'), default='cdn',
                    help='Ladeweg im Start-Teil des Rich Text: Paket-CSS+JS vom CDN (Loader-Gate) | CSS inline + JS synchron | CSS inline + JS asynchron (Gate)')
    a = ap.parse_args()
    M = json.load(open(a.manifest)); LIMIT = M.get('embed_limit', 9800)
    lab = open(a.lab).read(); head = open(a.head).read(); foot = open(a.footer).read()
    # 1) Page-Code: Lab-only entfernen
    head = strip_lab_only(head, M.get('lab_only', {}).get('head', []))
    foot = strip_lab_only(foot, M.get('lab_only', {}).get('footer', []))
    hn = parse(head); fn = parse(foot)
    # 2) Ausgabe im Lab-Body finden: Wurzel-Elemente laut Manifest (direkte Body-Kinder)
    b0 = lab.index('<body'); b1 = lab.index('>', b0) + 1; b2 = lab.rindex('</body>')
    body = parse(lab[b1:b2])
    roots = [n for n in body if isinstance(n, El) and any(has_class(n, c) for c in M['roots'])]
    if [r for c in M['roots'] for r in roots if has_class(r, c)].__len__() != len(M['roots']):
        raise SystemExit('Wurzeln nicht eindeutig gefunden: %s' % [r.start[:60] for r in roots])
    # Sicherheitscheck: Wurzeln stehen im Lab direkt hintereinander (nur Leerraum dazwischen)
    idx = [body.index(r) for r in roots]
    if any(isinstance(body[i], El) for i in range(idx[0], idx[-1] + 1) if body[i] not in roots):
        raise SystemExit('Zwischen den Wurzeln liegen weitere Elemente')
    # 3) Code einsammeln, Dokument-Reihenfolge wie im Lab: Head -> Body der Ausgabe -> Footer
    css, pre, main_js, data, links = [], [], [], [], []
    rest = collect(hn, css, pre, data, links, 'head')
    if any(isinstance(n, El) and n.tag != 'meta' for n in rest) or any(isinstance(n, El) and n.tag == 'meta' and dict(n.attrs).get('name') != 'robots' for n in rest):
        raise SystemExit('Unerwartete Elemente im Page-Head-Code: %s' % [n.start[:60] for n in rest if isinstance(n, El)])
    markup_roots = collect(roots, css, main_js, data, links, 'body')
    rest = collect(fn, css, main_js, data, links, 'footer')
    if any(isinstance(n, El) for n in rest): raise SystemExit('Unerwartete Elemente im Page-Footer-Code')
    # 4a) Paket (Bytes) – Ladeweg im Rich Text braucht die Pruefsummen
    pid = M['package']
    cssb = ('/* OFF SCRIPT %s – Paket, aus Lab %s erzeugt (lab2cms). Inhalt unveraendert, Reihenfolge wie im Lab. */\n' % (pid, M['lab_version']) + '\n'.join(css)).encode()
    J = json.dumps
    jsb = ('/* OFF SCRIPT %s – Paket, aus Lab %s erzeugt (lab2cms). Skripte unveraendert, global ausgefuehrt. */\n' % (pid, M['lab_version']) +
           '(function(){var L=window.OSL,O=window.OSIssue={id:%s,errors:[],ran:{}};\n' % J(pid) +
           'var D=%s,PRE=%s,MAIN=%s;\n' % (J(data, ensure_ascii=False), J(pre, ensure_ascii=False), J(main_js, ensure_ascii=False)) +
           'function run(l,k){for(var i=0;i<l.length;i++){try{(0,eval)(l[i]+"\\n//# sourceURL=%s-"+k+"-"+i+".js");}catch(e){O.errors.push([k,i,String(e)]);}}O.ran[k]=1;}\n' % pid.split('@')[0] +
           'O.pre=function(){if(O.ran.pre)return;D.forEach(function(d){if(!document.getElementById(d[0])){var s=document.createElement("script");s.type="application/json";s.id=d[0];s.textContent=d[1];document.head.appendChild(s);}});run(PRE,"pre");};\n'
           'O.main=function(){if(O.ran.main||(window.OSL&&OSL.failed))return;O.pre();run(MAIN,"main");};\n'
           '/* Loader mit Gate (OSL.manual): der Loader bestimmt den Zeitpunkt. Sonst (synchron): Kopf-Teil sofort. */\n'
           'if(L&&L.manual){L.ready(O);return;}\n'
           'if(L&&(L.failed||(L.check&&!L.check()))){O.skipped=String(L.failed);return;}\n'
           'O.pre();\n'
           '})();\n').encode()
    # 4) Chunks fuer den Rich Text: Start-Teil (Ladeweg, Vorab-Zustand, Preloads), dann Markup
    ch = Chunker(LIMIT)
    fallback = M.get('reading_hide')
    base = M['cdn_base'].format(package=pid.split('@')[0], version=pid.split('@')[1])
    S = {'css': sri(cssb), 'js': sri(jsb)}
    lead = ''
    if M.get('pre_paint'):
        lead += '<template data-os-pre="%s"></template>' % html.escape(json.dumps(M['pre_paint'], ensure_ascii=False, separators=(',', ':')), quote=True)
    lead += ''.join(links)
    if fallback:
        lead += '<style data-os-fallback>%s{display:none!important}</style>' % ','.join('html.os-pkg-failed .os-issue-rt ' + x for x in fallback)
    js_async = '<script async fetchpriority="high" src="%sissue.min.js" integrity="%s" crossorigin="anonymous" onerror="OSL.jsFail(\'js\')"></script>' % (base, S['js'])
    boot = []
    if a.mode == 'cdn':
        lead = '<script>OSL.gate()</script>' + lead + ('<link id="os-pkg-css" rel="stylesheet" href="%sissue.min.css" integrity="%s" crossorigin="anonymous" onload="OSL.cssLoaded()" onerror="OSL.fail(\'css\')">' % (base, S['css'])) + js_async
    else:
        if a.mode == 'inline-async': lead = '<script>OSL.gate({inlineCss:true})</script>' + lead + js_async
        css_txt = cssb.decode()
        assert '</style' not in css_txt.lower() and not INVISIBLE.search(css_txt)
        parts = split_css(css_txt, LIMIT - 400)
        boot = ['<style data-os-css="%d/%d">%s</style>' % (k + 1, len(parts), c) for k, c in enumerate(parts)]
        boot[-1] += ('<script>OSL.cssLoaded()</script>' if a.mode == 'inline-async' else
                     '<script src="%sissue.min.js" integrity="%s" crossorigin="anonymous" onerror="OSL.fail(\'js\')"></script>' % (base, S['js']))
        assert ''.join(p for p in parts) == css_txt, 'CSS-Aufteilung nicht verlustfrei'
    ch.chunks.append(([], lead))
    for b in boot: ch.chunks.append(([], b))
    boot_n = len(ch.chunks)
    ch.emit(markup_roots, [])
    # 5) Roundtrip: zusammensetzen wie der Loader und mit dem Original vergleichen
    rebuilt = rebuild(ch.chunks[boot_n:], ch.raw)
    original = ser(markup_roots)
    ok = rebuilt == original
    os.makedirs(a.out + '/dist', exist_ok=True)
    open(a.out + '/dist/issue.min.css', 'wb').write(cssb); open(a.out + '/dist/issue.min.js', 'wb').write(jsb)
    rt = ''.join("<div data-rt-embed-type='true'>%s%s</div>" % (ch.marker(p), c) for p, c in ch.chunks)
    if a.vgwort:
        if not re.fullmatch(r'https://vg\d{2}\.met\.vgwort\.de/na/[0-9a-f]{32}', a.vgwort): raise SystemExit('VG-WORT-Zaehlmarke ungueltig: ' + a.vgwort)
        rt += ("<div data-rt-embed-type='true'><div class=\"vg-wort-code\" style=\"display:block;width:0;height:0;overflow:hidden;line-height:0\">"
               "<img src=\"%s\" width=\"1\" height=\"1\" alt=\"\" loading=\"eager\"></div></div>" % a.vgwort)
    # Unsichtbare/mehrdeutige Zeichen als Entitaeten (uebertragungssicher, im DOM identisch); nie in Style/Skript-Rohtext
    for raw in re.findall(r'<(?:style|script)\b[^>]*>(.*?)</(?:style|script)>', rt, re.S):
        assert not INVISIBLE.search(raw), 'Unsichtbares Zeichen in Style/Skript'
    rt = INVISIBLE.sub(lambda m: '&#x%x;' % ord(m.group(0)), rt)
    open(a.out + '/rt.html', 'w').write(rt)
    json.dump(S, open(a.out + '/sri.json', 'w'), indent=1)
    sizes = [len(ch.marker(p)) + len(c) for p, c in ch.chunks]
    rep = {'package': pid, 'mode': a.mode, 'cdn_base': base, 'start_chunks': boot_n, 'roundtrip_identisch': ok, 'chunks': len(sizes), 'chunk_max': max(sizes), 'chunk_sizes': sizes,
           'limit': LIMIT, 'wrapper': ch.n, 'css_bytes': len(cssb), 'js_bytes': len(jsb), 'styles': len(css), 'skripte_pre': len(pre),
           'skripte_main': len(main_js), 'daten': [d[0] for d in data], 'preloads': len(links), 'rt_zeichen': len(rt), 'vgwort': a.vgwort, 'sri': S}
    json.dump(rep, open(a.out + '/report.json', 'w'), indent=1, ensure_ascii=False)
    print(json.dumps({k: v for k, v in rep.items() if k != 'chunk_sizes'}, ensure_ascii=False))
    if not ok:
        i = next(i for i in range(min(len(rebuilt), len(original))) if rebuilt[i] != original[i])
        print('ROUNDTRIP-DIFF @', i, repr(original[i - 80:i + 80]), '\n vs', repr(rebuilt[i - 80:i + 80])); sys.exit(1)


if __name__ == '__main__':
    main()
