"""osfix – sichere Einzelkorrekturen im Rich Text einer OFF-SCRIPT-Ausgabe (Prototyp, lokal).

Zwei Funktionen:
  fix    Eine Textstelle gezielt ersetzen. Nur Textknoten werden angefasst (nie Tags, Attribute, Marker, Styles).
         Abbruch, wenn die Stelle fehlt, mehrdeutig ist, ueber Tag-Grenzen laeuft oder ein Embed die Grenze ueberschreitet.
         Ergebnis: neuer Rich Text + Journal-Eintrag; Pruefung: ausser dieser Stelle ist alles zeichengleich.
  merge  Drei-Wege-Abgleich fuer einen erneuten Lab-Transfer: Basis (letzter Transfer), CMS-Stand (mit Korrekturen),
         neuer Lab-Stand. Textaenderungen aus dem CMS werden uebernommen, solange das Lab dieselbe Stelle nicht
         ebenfalls geaendert hat. Konflikte und Strukturaenderungen im CMS stoppen den Lauf.
"""
import hashlib, html, json, re, sys, datetime
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from lab2cms import parse, El, ser, INVISIBLE


def enc(t):
    t = t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return INVISIBLE.sub(lambda m: '&#x%x;' % ord(m.group(0)), t)

SKIP = {'template', 'style', 'script'}
EMBED = "<div data-rt-embed-type='true'>"


def texts(nodes, path=()):
    """Alle editierbaren Textknoten mit stabilem Pfad (Kind-Indizes) – ohne Marker, Styles, Skripte, Kommentare."""
    for i, n in enumerate(nodes):
        if isinstance(n, str):
            if not n.startswith('<!--') and n.strip(): yield path + (i,), nodes, i
        elif n.tag not in SKIP:
            yield from texts(n.kids, path + (i,))


def sha(s): return hashlib.sha256(s.encode()).hexdigest()[:16]


def skeleton(rt):
    """Alles ausser Textinhalt: Tags, Attribute, Marker – zum Nachweis, dass nur Text geaendert wurde."""
    return re.sub(r'>[^<]*<', '><', rt)


def embeds_ok(rt, limit=10000):
    sizes = [len(EMBED) + len(p) for p in rt.split(EMBED)[1:]]
    return max(sizes) < limit, sizes


def fix(rt, old, new, nth=None):
    tree = parse(rt)
    old_h, new_h = html.escape(old, quote=False), html.escape(new, quote=False)
    occ = [(p, lst, i, m.start()) for p, lst, i in texts(tree) for m in re.finditer(re.escape(old_h), lst[i])]
    if not occ:   # Stelle enthaelt Entitaeten (z. B. geschuetztes Leerzeichen): dekodiert suchen, verlustfrei neu kodieren
        dec = [(p, lst, i) for p, lst, i in texts(tree) if old in html.unescape(lst[i]) and enc(html.unescape(lst[i])) == lst[i]]
        if not dec:
            rx = re.compile(re.escape(old).replace('\\ ', '[ \u00a0\u202f]'))
            soft = [html.unescape(lst[i]) for p, lst, i in texts(tree) if rx.search(html.unescape(lst[i]))]
            if soft:
                raise SystemExit('Stelle enthaelt ein geschuetztes Leerzeichen (im Text: %r). Bitte bestaetigen, ob es erhalten bleiben soll.' % rx.search(soft[0]).group(0))
        if len(dec) == 1 and html.unescape(dec[0][1][dec[0][2]]).count(old) == 1:
            p, lst, i = dec[0]; before = lst[i]; k = before.index(enc(old)) if enc(old) in before else 0
            lst[i] = enc(html.unescape(before).replace(old, new, 1)); old_h = enc(old)
            occ = None
        else:
            plain = re.sub(r'<[^>]+>', '', rt)
            raise SystemExit('Stelle nicht gefunden' + (' (laeuft ueber Tag-Grenzen – bitte kuerzer waehlen)' if html.unescape(plain).count(old) else ''))
    if occ and len(occ) > 1 and nth is None:
        raise SystemExit('Mehrdeutig: %d Treffer. Bitte mit Kontext oder nth angeben: %s' % (len(occ), [html.unescape(lst[i])[max(0, k - 30):k + 50] for _, lst, i, k in occ]))
    if occ is not None:
        p, lst, i, k = occ[(nth or 1) - 1]
        before = lst[i]
        lst[i] = before[:k] + new_h + before[k + len(old_h):]
    out = ser(tree)
    # Nachweise
    assert skeleton(out) == skeleton(rt), 'Struktur veraendert – Abbruch'
    ok, sizes = embeds_ok(out)
    if not ok: raise SystemExit('Embed-Grenze ueberschritten: %s' % max(sizes))
    d = [x for x in zip(re.findall(r'>([^<]*)<', rt), re.findall(r'>([^<]*)<', out)) if x[0] != x[1]]
    assert len(d) == 1, 'Mehr als eine Textstelle veraendert'
    entry = {'zeit': datetime.datetime.now().isoformat(timespec='seconds'), 'pfad': list(p), 'alt': old, 'neu': new,
             'kontext': html.unescape(before[max(0, k - 40):k + len(old_h) + 40]), 'rt_vorher': sha(rt), 'rt_nachher': sha(out)}
    return out, entry


def merge(base, cms, lab):
    """Drei-Wege-Abgleich auf Textknoten-Ebene. Struktur muss in Basis und CMS gleich sein."""
    if skeleton(base) != skeleton(cms):
        raise SystemExit('Struktur im CMS weicht vom letzten Transfer ab – manuelle Pruefung noetig')
    B = {p: lst[i] for p, lst, i in texts(parse(base))}
    C = {p: lst[i] for p, lst, i in texts(parse(cms))}
    corrections = [(p, B[p], C[p]) for p in B if B[p] != C[p]]
    L = parse(lab)
    Ltexts = list(texts(L))
    report, conflicts = [], []
    for p, b, c in corrections:
        # Stelle im neuen Lab-Stand finden: zuerst gleicher Pfad mit unveraendertem Basistext, sonst eindeutiger Basistext
        cand = [(q, lst, i) for q, lst, i in Ltexts if q == p and lst[i] == b] or [(q, lst, i) for q, lst, i in Ltexts if lst[i] == b]
        if len(cand) == 1:
            q, lst, i = cand[0]; lst[i] = c; report.append({'pfad': list(p), 'uebernommen': html.unescape(c)[:80]})
        elif any(q == p for q, _, _ in Ltexts):
            conflicts.append({'pfad': list(p), 'cms': html.unescape(c)[:80], 'lab': html.unescape([lst[i] for q, lst, i in Ltexts if q == p][0])[:80]})
        else:
            conflicts.append({'pfad': list(p), 'cms': html.unescape(c)[:80], 'lab': 'Stelle im Lab nicht mehr vorhanden'})
    if conflicts:
        return None, report, conflicts
    return ser(L), report, []


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest='cmd', required=True)
    f = sp.add_parser('fix'); f.add_argument('rt'); f.add_argument('alt'); f.add_argument('neu'); f.add_argument('--nth', type=int); f.add_argument('--out', required=True); f.add_argument('--journal', required=True)
    m = sp.add_parser('merge'); m.add_argument('basis'); m.add_argument('cms'); m.add_argument('lab'); m.add_argument('--out', required=True)
    a = ap.parse_args()
    if a.cmd == 'fix':
        out, e = fix(open(a.rt).read(), a.alt, a.neu, a.nth)
        open(a.out, 'w').write(out)
        j = json.load(open(a.journal)) if __import__('os').path.exists(a.journal) else []
        j.append(e); json.dump(j, open(a.journal, 'w'), indent=1, ensure_ascii=False)
        print(json.dumps(e, ensure_ascii=False))
    else:
        out, rep, conf = merge(open(a.basis).read(), open(a.cms).read(), open(a.lab).read())
        print(json.dumps({'uebernommen': rep, 'konflikte': conf}, ensure_ascii=False, indent=1))
        if out is None: sys.exit(2)
        open(a.out, 'w').write(out)
