"""Prueft das Repository gegen releases.json.

- Jede freigegebene Version: Dateien vorhanden, SRI und Groesse stimmen (unveraenderlich).
- Keine fremden Dateien in einem freigegebenen Versionsordner.
- Mit --against <git-ref>: kein freigegebener Versionsordner wurde gegenueber diesem Stand veraendert
  (verhindert nachtraegliche Aenderungen; neue Versionen bekommen einen neuen Ordner).
Aufruf: python3 tools/verify.py [--against origin/main]
"""
import base64, hashlib, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sri(path):
    return 'sha384-' + base64.b64encode(hashlib.sha384(open(path, 'rb').read()).digest()).decode()


def main():
    rel = json.load(open(os.path.join(ROOT, 'releases.json')))
    errors, seen = [], set()
    for r in rel['releases']:
        key = (r['issue'], r['version'])
        if key in seen: errors.append('Version doppelt: %s@%s' % key)
        seen.add(key)
        if r['tag'] != '%s-%s' % key: errors.append('Tag-Name passt nicht: %s' % r['tag'])
        d = os.path.join(ROOT, 'packages', r['issue'], r['version'])
        if not os.path.isdir(d): errors.append('Ordner fehlt: %s' % d); continue
        present = sorted(os.listdir(d)); expected = sorted(r['files'])
        if present != expected: errors.append('%s@%s: Dateien %s, erwartet %s' % (key + (present, expected)))
        for f, meta in r['files'].items():
            p = os.path.join(d, f)
            if not os.path.isfile(p): continue
            if sri(p) != meta['sri']: errors.append('%s@%s/%s: SRI weicht ab' % (key + (f,)))
            if os.path.getsize(p) != meta['bytes']: errors.append('%s@%s/%s: Groesse weicht ab' % (key + (f,)))
    if '--against' in sys.argv:
        ref = sys.argv[sys.argv.index('--against') + 1]
        try:
            old = json.loads(subprocess.check_output(['git', 'show', '%s:releases.json' % ref], cwd=ROOT, stderr=subprocess.DEVNULL))
        except subprocess.CalledProcessError:
            old = {'releases': []}
        new = {(r['issue'], r['version']): r for r in rel['releases']}
        for r in old['releases']:
            k = (r['issue'], r['version'])
            if k not in new: errors.append('Freigegebene Version entfernt: %s@%s' % k); continue
            if r['files'] != new[k]['files'] or r['tag'] != new[k]['tag']:
                errors.append('Freigegebene Version veraendert: %s@%s (neue Version anlegen statt aendern)' % k)
    for e in errors: print('FEHLER', e)
    print('OK' if not errors else '%d Fehler' % len(errors))
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
