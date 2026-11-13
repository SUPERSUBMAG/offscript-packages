# os001 4.4.14

Basis: 4.4.11 (Dateien zeichengleich übernommen), Kopfkommentar/Paket-ID angepasst, am Ende ergänzt: Scrollbalken an der Navbar.
Ersetzt 4.4.12 und 4.4.13 (beide nie im CMS verwendet). 4.4.12: Dort blieb der Balken nach einem Sprung (Neuladen mitten im Artikel, Anker) von einer hellen in eine schwarze Fläche Ziegelrot, weil Ziegel auf Schwarz knapp über Kontrast 3 liegt.

## Scrollbalken an der Navbar (wie Layout „Selected“)
- 3 px hoch, direkt unter Navbar + Border, ohne Track; ausgeblendet bei offenem Mega-Menü und im Lesemodus (`os-pkg-failed`).
- Start: Anfang `.os001-hero`; Ende: Ende `.os026-story` erreicht den unteren Viewportrand (Logik wie Selected).
- Farbe: Creme `#F0E4CB` (wie Schriftzug/Logo); auf heller Fläche der Farb-Engine (`.os001-bglayer`, Creme-Kapitel) Ziegelrot `#8E4C36` (OS001-Palette „story“).
- 4.4.13: Farbwahl lief teils vor dem Rendern der Farb-Engine (Scroll-Reihenfolge) und blieb dann bis zum nächsten Scrollen falsch; 4.4.14 bestimmt die Farbe einen Frame später plus Nachlauf nach Scroll-Ende (Test: 36 Sprünge, 0 Abweichungen; 4.4.13: 22).
- Regel: immer die kontrastreichere der beiden Farben zur Fläche unter der Navbar; Wechsel erst bei 20 % Kontrastvorsprung (kein Flackern im Übergang).
- Eigene Klassen `.os-progress` / `.os-progress__bar` (kein Eingriff in das Articles Template, keine Kollision mit `.oc-progress`).
