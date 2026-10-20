# OS001 4.4.11 – Transferprotokoll (Stand 2026-10-20)

Quelle: /os-lab-player (Page 6ad76b50b42f445c4b38fac3), Staging-Stand 2026-10-20 14:47:31 UTC,
Page-Head/-Footer identisch mit /os-lab (4.4.10).

Release-Vorbereitung (prep_release.py, sonst zeichengleich):
1. alter Player `.os029-mp[data-os-mp-old]` entfernt (31 894 Zeichen, inkl. eigener Player-CSS)
2. Lab-Schalter-Skript (`data-ssmp-lab`, `?mp=old`) entfernt
3. zwei Lab-CSS-Regeln fuer `?mp=old` (+ Kommentar) entfernt

Build: `lab2cms.py --mode cdn`, Roundtrip identisch, 12 Embeds (max. 9 222 Zeichen).
Bekannt, bewusst unveraendert: Head/Footer enthalten weiter den Code des alten Players
(greift ohne `.os029-mp` nicht); Player-Bundle enthaelt den Testschalter `ssmpconsent`,
aktiv nur mit `data-ssmp-lab` am <html> (wird nirgends mehr gesetzt).

CMS (Articles, Item 6ad5d992b5ed151fe2616ef4, nur DE, bleibt Draft):
rich-text, off-script, kategorie-2, off-script-paket, off-script-sri-css/-js,
hero-image, hero-image-mobile, hero-image-alt-text.
