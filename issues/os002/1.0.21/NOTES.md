# os002 1.0.21

Basis: 1.0.20 (unverändert übernommen), nur Hero-Namen „Malik“/„Tillman“ angepasst.

## Problem
In flachen Desktop-Fenstern (Seitenverhältnis flacher als das 3:2-Foto) ragt das Foto unten über den sichtbaren Hero hinaus. Die Namen sitzen fest im Foto (Malik 63 %, Tillman 71 % der Bildhöhe) und wurden dadurch unten abgeschnitten (z. B. 1000 × 560, 1280 × 720, 1440 × 760, 1366 × 600). In schmalen Desktop-Fenstern (z. B. 768 × 900) ragten sie seitlich heraus; auf Tablets hochkant (Mobile-Layout, z. B. 768 × 1024) unten knapp.

## Vorgabe
Desktop: Die Namen liegen immer auf dem Boden, nie höher als im freigegebenen Layout (Bereich darüber = Sperrzone).

## Lösung (nur CSS, head)
- Desktop (min-width 768px und Seitenverhältnis > 4/5):
  - Position im Foto unverändert (Malik 63cqh, Tillman 71cqh).
  - Schriftgröße schrumpft bei Platzmangel, bis Tillman mit 24 px Abstand zum Hero-Rand Platz hat, höchstens um 25 %; zusätzlich Deckel 12.3vw wie bisher.
  - Reicht das nicht (sehr flache Fenster), wird der Hero so weit verlängert, dass Tillman vollständig im Bild liegt (unterhalb der Falz, beim Scrollen sichtbar).
  - Seitlich: Namen rücken nur waagerecht nach innen (24 px Rand).
- Mobile/Tablet hochkant: Namen-Unterkante mindestens 24 px über dem sichtbaren Hero-Ende (Smartphones unverändert).

## Getestet
27 Fenstergrößen von 375 × 667 bis 2560 × 1300: kein Name abgeschnitten; Position im Foto überall wie freigegeben; Smartphones identisch zu 1.0.20.
