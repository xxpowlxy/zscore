## 🕵🏻‍♀️ PoC: Modell-Evaluierung zur Verbrauchsvalidierung

Dieses Repository dient als Proof of Concept (PoC), um verschiedene statistische Modelle zur Anomalie-Erkennung in Verbrauchsdaten zu evaluieren und vergleichen.

Der Fokus liegt auf der Optimierung von Z-Score-Varianten (Standard, Kreuzvalidiert, Robust/MAD-basiert) und der Ermittlung ihrer idealen Parametereinstellungen für unseren Anwendungsfall.

Die Streamlit-Web-App dient dabei als visuelles Test-Interface, um eine fundierte Entscheidung für das optimale Modell treffen zu können.

Das Ziel ist die Auswahl des bestgeeigneten Algorithmus für die spätere Implementierung als Microservice in der Produktionsumgebung.

## 🔐 Authentifizierung

Die App ist durch ein einfaches Login-System geschützt. Die Credentials werden aus der `.env` Datei geladen:

```env
APP_USERNAME=dein_username
APP_PASSWORD=dein_passwort
```

**Wichtig:** Die `.env` Datei ist in `.gitignore` und wird nicht committet!

## 📊 Verfügbare Modelle

- **Klassischer Z-Score**: Alle Werte werden für Mittelwert/Std verwendet
- **Leave-One-Out Z-Score**: Der letzte Wert wird gegen historische Daten geprüft (verhindert Masking-Effekt) 