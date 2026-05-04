## 🕵🏻‍♀️ PoC: Modell-Evaluierung zur Verbrauchsvalidierung

Dieses Repository dient als Proof of Concept (PoC), um verschiedene statistische Modelle zur Anomalie-Erkennung in Verbrauchsdaten zu evaluieren und zu vergleichen.

Der Fokus liegt auf der Optimierung von Z-Score-Varianten und der Ermittlung ihrer idealen Parametereinstellungen für unseren Anwendungsfall.

Die Streamlit-Web-App dient dabei als visuelles Test-Interface für die Messdienst Abrechner, 
um bekannte Fälle zu testen und geeignete Parameter für das Modell festzulegen (treshhold).

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
