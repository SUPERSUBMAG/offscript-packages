# os002 1.0.22

Basis: 1.0.21 (unverändert übernommen), nur Hero-Namen im Mobile-Layout angepasst.

## Problem
Im Mobile-Layout (Breite unter 768 px oder Seitenverhältnis bis 4/5) wurden die Namen in flachen Fenstern seit 1.0.21 nach oben verschoben, damit sie nicht abgeschnitten werden. Dadurch lagen sie im Gesicht bzw. am Kragen statt auf der Jacke (z. B. 506 × 535: 53 % statt 75 % der Bildhöhe; 600 × 600: 50 %; 800 × 1000: 67 %).

## Vorgabe
Namen nie höher als im freigegebenen Layout (Sperrzone darüber), auch im Mobile-Layout.

## Lösung (nur CSS, head)
- Mobile-Layout: Namen immer an der freigegebenen Bildposition (Unterkante 86,4 % der Bildhöhe), keine Verschiebung nach oben.
- Reicht die Fensterhöhe nicht, wird der Hero so weit verlängert, dass Tillman mit 24 px Abstand vollständig im Hero liegt (unterhalb der Falz, beim Scrollen sichtbar).
- Desktop unverändert gegenüber 1.0.21.

## Getestet
17 Fenstergrößen im Mobile-Layout (360 × 740 bis 1024 × 1366, inkl. 506 × 535, 600 × 600, 667 × 375): Namen überall bei 75 % / 65 % der Bildhöhe, nie abgeschnitten; Smartphones hochkant identisch zu 1.0.21.
