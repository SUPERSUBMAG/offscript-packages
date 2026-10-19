# OFF SCRIPT – Pakete

Technische Pakete für die Storytelling-Ausgaben von **OFF SCRIPT** (SUPERSUB). Jede Ausgabe hat ein eigenes Design; dieses Repository liefert nur deren Code (CSS/JS). Die Inhalte stehen im Webflow-CMS.

## Aufbau

```
packages/<ausgabe>/<version>/issue.min.css   Paket-CSS (aus dem freigegebenen Lab erzeugt)
packages/<ausgabe>/<version>/issue.min.js    Paket-JS
issues/<ausgabe>/manifest.json               Transfer-Einstellungen der Ausgabe (lab2cms)
loader/<version>/                            Loader-Code für das Articles Template (Referenz)
releases.json                                Verzeichnis aller freigegebenen Versionen mit SRI-Prüfsummen
tools/lab2cms.py                             Lab → Paket + Rich Text
tools/osfix.py                               gezielte Textkorrekturen im CMS, Drei-Wege-Abgleich
tools/verify.py                              Prüfung: Vollständigkeit, SRI, Unveränderlichkeit
```

## Adressen (jsDelivr, GitHub)

```
https://cdn.jsdelivr.net/gh/SUPERSUBMAG/offscript-packages@<ausgabe>-<version>/packages/<ausgabe>/<version>/issue.min.css
https://cdn.jsdelivr.net/gh/SUPERSUBMAG/offscript-packages@<ausgabe>-<version>/packages/<ausgabe>/<version>/issue.min.js
```

Beispiel OS001: `…/offscript-packages@os001-4.4.10/packages/os001/4.4.10/issue.min.js`

Die Adresse ist immer an einen **Tag** gebunden, nie an `main`. Zusätzlich prüft der Browser jede Datei per SRI. Weicht eine Datei ab, wird sie nicht ausgeführt; die Seite zeigt dann die Lesefassung.

## Regeln

1. **Freigegebene Versionen sind unveränderlich.** Jede Änderung, auch am Musikplayer, ergibt eine neue Version (z. B. `4.4.11`) mit neuem Ordner, neuem Tag und neuem Eintrag in `releases.json`.
2. Ein Tag wird genau einmal gesetzt und nie verschoben oder gelöscht (Ruleset schützt `os*`-Tags).
3. Änderungen nur per Pull Request. `verify` muss grün sein: Es lehnt geänderte oder entfernte freigegebene Versionen ab.
4. Keine Zugangsdaten, keine Rohdaten und keine unveröffentlichten Artikeltexte im Repository. Das Repository ist öffentlich, weil jsDelivr nur öffentliche Repositories ausliefert.

## Neue Version freigeben

1. Lab freigeben, dann `python3 tools/lab2cms.py … --out <ordner>` ausführen.
2. Dateien nach `packages/<ausgabe>/<version>/` kopieren und einen Eintrag in `releases.json` mit SRI und Größe anlegen.
3. `python3 tools/verify.py` lokal ausführen, dann einen Pull Request öffnen und mergen.
4. Tag `<ausgabe>-<version>` auf den Merge-Commit setzen und pushen.
5. Den Rich Text im CMS mit `lab2cms` neu erzeugen (Ladeweg mit den neuen Adressen und SRI). Vorhandene CMS-Korrekturen mit `osfix merge` übernehmen.

## Neue Ausgabe (OS002 …)

Neuer Ordner `issues/os002/manifest.json` (Wurzel-Elemente, Lab-only-Blöcke, Vorab-Zustand). Paket-Code, Gestaltung und Animationen sind frei; der Loader im Template bleibt gleich.
