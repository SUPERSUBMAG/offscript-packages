# os002 1.0.20 (Hero im In-App-Browser stabil)

- Hero-Höhe und alle davon abhängigen Hero-Maße (Bildfläche, Logo-Breite Desktop, Navigationsabstand, Mobile-Versatz) nutzen jetzt wie OFF SCRIPT 001 die stabile Seitenhöhe `--ss-stable-vh` (Seitenscript, einmal beim Laden gesetzt) mit `100svh` als Rückfall, neue Variable `--os002-sv`.
- Grund: Im Instagram-In-App-Browser (und anderen In-App-Browsern) fährt die Leiste beim Scrollen ein und aus; der Webview ändert dabei seine Höhe, `svh` folgt mit, der Hero rechnete neu und sprang. Mit der stabilen Höhe bleiben Hero, Foto und Name fest.
- In Safari/Chrome mobil, auf Tablet und Desktop geometrisch identisch zu 1.0.18 (geprüft 390, 820, 1440, 1920 px). Basis ist 1.0.18; 1.0.19 (zentrierter Desktop-Hero) wurde verworfen und ist nicht enthalten.
- Loader 1.3, Status `staging-test`. Paket enthält ausschließlich Darstellungscode.
