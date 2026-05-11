# 📊 PoC: Statistische Anomalie-Erkennung für Verbrauchsdaten
Dieses Repository dient als Proof of Concept (PoC) zur Evaluierung statistischer Modelle, um Abrechnungsfehler in Messdaten automatisiert zu identifizieren. 
Der Fokus liegt auf der Praxistauglichkeit verschiedener Z-Score-Varianten im operativen Betrieb.

## 🎯 Projektziel
Ziel des Projekts ist es, ein visuelles Test-Interface für Messdienst-Mitarbeiter bereitzustellen. 
Damit können bekannte Problemfälle simuliert und ideale Schwellenwerte (thresholds) für die automatisierte Validierung festgelegt werden.

## 🔍 Evaluierte Modelle & Methodik

- __Leave-One-Out (LOO) Z-Score:__

Funktion: Der neue Messwert wird gegen die historische Verteilung geprüft, ohne diese selbst zu beeinflussen.
Vorteil: Verhindert die "Kontamination" des Modells durch den Ausreißer selbst. Ideal für die "On-the-fly"-Validierung bei der Datenerfassung.

- __Klassischer Z-Score:__

Funktion: Mittelwert und Standardabweichung werden über den gesamten Datensatz gebildet.
Vorteil: Effizient für die abschließende Prüfung kompletter Datensätze vor der Abrechnung, sofern diese bereits grob bereinigt sind.

- __MAD (Median Absolute Deviation):__

Vorgesehen für die initiale Bereinigung von stark verrauschten Altdatenbeständen (robust gegen Ausreißer).

## 🛠️ Features der Streamlit-App
Die Web-App dient als interaktives Reporting-Tool:

__Flexible Konfiguration:__ Historische Betrachtungszeiträume (5-20 Datenpunkte) und Schwellenwerte (1.0 - 4.0) sind live anpassbar.
__Domänen-Logik:__ Berücksichtigung von Gerätetauschen (Reset der Zählerstände) und Unterscheidung zwischen kumulierenden und rückstellenden Zählertypen.
__Reporting:__ Export von Testergebnissen im Markdown-Format zur Dokumentation und Reproduktion von Grenzfällen

## 🔐 Authentifizierung

Die App ist durch ein einfaches Login-System geschützt, da es nur intern betrieben wird und keine kritischen Daten im Backend hat. 
Die Credentials werden aus der `.env` Datei geladen:

```env
APP_USERNAME=dein_username
APP_PASSWORD=dein_passwort
```

## 📊 Verfügbare Modelle

- **Klassischer Z-Score**: Alle Werte werden für Mittelwert/Std verwendet
- **Leave-One-Out Z-Score**: Der letzte Wert wird gegen historische Daten geprüft (verhindert Masking-Effekt)
- **MAD Z-Score**: _im PoC nicht implementiert_
