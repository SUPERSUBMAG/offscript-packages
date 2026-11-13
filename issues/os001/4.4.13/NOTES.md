# os001 4.4.13

Basis: 4.4.11 (Dateien zeichengleich übernommen), Kopfkommentar/Paket-ID angepasst, am Ende ergänzt: Scrollbalken an der Navbar.
Ersetzt 4.4.12 (nie im CMS verwendet): Dort blieb der Balken nach einem Sprung (Neuladen mitten im Artikel, Anker) von einer hellen in eine schwarze Fläche Ziegelrot, weil Ziegel auf Schwarz knapp über Kontrast 3 liegt.

## Scrollbalken an der Navbar (wie Layout „Selected“)
- 3 px hoch, direkt unter Navbar + Border, ohne Track; ausgeblendet bei offenem Mega-Menü und im Lesemodus (`os-pkg-failed`).
- Start: Anfang `.os001-hero`; Ende: Ende `.os026-story` erreicht den unteren Viewportrand (Logik wie Selected).
- Farbe: Creme `#F0E4CB` (wie Schriftzug/Logo); auf heller Fläche der Farb-Engine (`.os001-bglayer`, Creme-Kapitel) Ziegelrot `#8E4C36` (OS001-Palette „story“).
- Regel 4.4.13: immer die kontrastreichere der beiden Farben zur Fläche unter der Navbar; Wechsel erst bei 20 % Kontrastvorsprung (kein Flackern im Übergang).
- Eigene Klassen `.os-progress` / `.os-progress__bar` (kein Eingriff in das Articles Template, keine Kollision mit `.oc-progress`).
