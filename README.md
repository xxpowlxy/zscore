# PoC: Statistische Anomalie-Erkennung für Verbrauchsdaten

Dieses Repository dient als Proof of Concept (PoC) zur Evaluierung statistischer Modelle, um Abrechnungsfehler in Messdaten automatisch zu identifizieren.

## Projektziel

Ziel des Projekts ist es, Messdienst-Mitarbeiter mithilfe einer interaktiven Oberfläche mit statistischen Erkennungsmethoden vertraut zu machen. Die Mitarbeiter können bekannte Problemfälle simulieren und ideale Schwellenwerte für die automatische Validierung festlegen und vorschlagen.

## Evaluierte Modelle & Methodik

- **Klassischer Z-Score:**
Mittelwert und Standardabweichung werden über den gesamten Datensatz gebildet.
Effizient für die abschließende Prüfung kompletter Datensätze vor der Abrechnung.

- **Leave-One-Out (LOO) Z-Score:**
Der neue Messwert wird gegen die historische Verteilung geprüft, ohne diese selbst zu beeinflussen. Das verhindert den Masking-Effekt — also dass ein Ausreißer das Modell so stark verzerrt, dass er sich selbst als unauffällig tarnt. Ideal für die Validierung bei der Datenerfassung.

- **MAD (Median Absolute Deviation):**
Robuster Algorithmus für die initiale Bereinigung von stark verrauschten Altdatenbeständen. Im aktuellen PoC noch nicht implementiert — als nächster Schritt geplant.

## Features der Streamlit-App

Die Web-App dient als interaktives Reporting- und Konfigurationstool:

- **Flexible Konfiguration:** Historische Betrachtungszeiträume (5–20 Datenpunkte) und Schwellenwerte (1.0–4.0) sind live anpassbar.
- **Domänen-Logik:** Berücksichtigung von Gerätetauschen (Reset der Zählerstände) und Unterscheidung zwischen kumulierenden und rückstellenden Zählertypen.
- **Reporting:** Export von Testergebnissen im Markdown-Format zur Dokumentation und Reproduktion von Grenzfällen.

## Design Decisions

### Separate Schwellenwerte pro Methode

Jede Erkennungsmethode hat ihren eigenen konfigurierbaren Schwellenwert pro Gerätetyp. 
Die Methoden arbeiten bewusst unabhängig voneinander und werden nicht auf eine gemeinsame Skala gebracht — ähnlich wie Celsius und Fahrenheit: Beide messen Temperatur korrekt, sind aber nicht direkt vergleichbar.

Da der Output in diesem PoC binär ist (Anomalie / keine Anomalie), hat diese Entscheidung keine praktischen Nachteile. 
Sollte zukünftig ein gemeinsamer Konfidenz-Score über alle Methoden hinweg berechnet werden, wäre eine Normalisierung der Skalen erforderlich.

### Automatischer Feedback-Loop (Roadmap)

Eine geplante Erweiterung ist die automatische Anpassung der Schwellenwerte: Bewertet das Qualitätsmanagement eine erkannte Anomalie als Fehlalarm, wird der Schwellenwert automatisch leicht erhöht. Über diesen Feedback-Loop würden sich die Grenzwerte schrittweise an die Realität anpassen.

Diese Funktion wird bewusst nicht in der Beta eingeführt, da sie die Auswertung und Vergleichbarkeit der Modellergebnisse in der Evaluierungsphase erschweren würde.

## Setup

Die App ist durch ein einfaches Login-System geschützt und ausschließlich für den internen Betrieb vorgesehen. Die Zugangsdaten werden über eine `.env`-Datei konfiguriert:

```env
APP_USERNAME=dein_username
APP_PASSWORD=dein_passwort
```
