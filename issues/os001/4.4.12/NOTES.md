# os001 4.4.12

Basis: 4.4.11 (Dateien zeichengleich übernommen), nur Kopfkommentar/Paket-ID angepasst und am Ende ergänzt:

## Scrollbalken an der Navbar (wie Layout „Selected“)
- 3 px hoch, direkt unter Navbar + Border, ohne Track; ausgeblendet bei offenem Mega-Menü und im Lesemodus (`os-pkg-failed`).
- Start: Anfang `.os001-hero`; Ende: Ende `.os026-story` erreicht den unteren Viewportrand (Logik wie Selected).
- Farbe: Creme `#F0E4CB` (wie Schriftzug/Logo). Liegt unter der Navbar eine helle Fläche der Farb-Engine (`.os001-bglayer`, z. B. Creme-Kapitel), wechselt der Balken auf Ziegelrot `#8E4C36` (OS001-Palette „story“). Wahl nach Kontrast mit Hysterese (WCAG-Kontrast ≥ 3).
- Eigene Klassen `.os-progress` / `.os-progress__bar` (kein Eingriff in das Articles Template, keine Kollision mit `.oc-progress`).
