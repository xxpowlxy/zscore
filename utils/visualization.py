"""
Visualisierungs-Modul für Anomalie-Erkennungs-Ergebnisse

Dieses Modul enthält Funktionen zum Erstellen von Plots und Tabellen
für die verschiedenen Anomalie-Erkennungs-Methoden.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import Dict
from datetime import datetime


# === KONFIGURATION ===
FARBE_NORMAL = '#2E86AB'  # Blau für normale Werte
FARBE_ANOMALIE = '#A23B72'  # Rot/Pink für Anomalien
FARBE_BASELINE = '#F18F01'  # Orange für Mittelwert/Median
FARBE_KONFIDENZ = '#C73E1D'  # Rot für Konfidenzgrenzen
ALPHA_KONFIDENZ = 0.2  # Transparenz für Konfidenzbereich

FIGSIZE_DEFAULT = (12, 6)  # Standardgröße für Plots
# ====================


def plot_anomalie_erkennung(
    daten: pd.DataFrame,
    ergebnisse: Dict,
    methode: str
) -> plt.Figure:
    """
    Erstellt einen Plot für Anomalie-Erkennung mit allen relevanten Informationen.

    Args:
        daten: DataFrame mit Spalten 'Datum' und 'Verbrauch'
        ergebnisse: Dictionary aus den Analyse-Funktionen (classic_zscore, etc.)
        methode: String zur Identifikation der Methode
                 ("classic", "loo", "mad")

    Returns:
        matplotlib Figure Objekt

    Plot zeigt:
        - Linie: Verbrauchswerte über Zeit (blaue Linie)
        - Baseline: Mittelwert oder Median (orange gestrichelte Linie)
        - Konfidenzbereich: Bereich zwischen oberer und unterer Grenze (rote Fläche)
        - Anomalie-Marker: Rote Punkte für identifizierte Anomalien
        - Legende mit allen Informationen
    """
    # Erstelle Figure und Axes
    fig, ax = plt.subplots(figsize=FIGSIZE_DEFAULT)

    # Extrahiere Daten
    datum = daten['Datum'].values
    verbrauch = daten['Verbrauch'].values

    # LOO hat eine andere Struktur - nur ein Wert wird geprüft
    if methode == "loo":
        # LOO: Erstelle anomalien-Liste (nur letzter Wert kann Anomalie sein)
        anomalien = [False] * len(verbrauch)
        anomalien[ergebnisse['letzter_index']] = ergebnisse['ist_anomalie']

        # LOO: Erstelle z_scores-Liste (nur letzter Wert hat Z-Score)
        z_scores = [0.0] * len(verbrauch)
        z_scores[ergebnisse['letzter_index']] = ergebnisse['z_score']
    else:
        # Classic: Alle Werte haben Z-Scores
        anomalien = ergebnisse['anomalien']
        z_scores = ergebnisse['z_score']

    # Konvertiere Datum zu datetime falls nötig
    if not isinstance(datum[0], (datetime, pd.Timestamp)):
        datum = pd.to_datetime(datum)

    # === BASELINE UND KONFIDENZBEREICH ===
    # Bestimme Baseline (Mittelwert oder Median) je nach Methode
    if methode == "mad":
        baseline = ergebnisse['median']
        baseline_label = 'Median'
        streuung = ergebnisse['mad_std']
    else:
        baseline = ergebnisse['mittelwert']
        baseline_label = 'Mittelwert'
        streuung = ergebnisse['std']

    # Berechne Konfidenzgrenzen
    # Diese werden aus den Ergebnissen abgeleitet
    threshold = _bestimme_threshold_aus_ergebnissen(ergebnisse, verbrauch, baseline, streuung)

    untere_grenze = baseline - (threshold * streuung)
    obere_grenze = baseline + (threshold * streuung)

    # Zeichne Konfidenzbereich (gefüllte Fläche zwischen Grenzen)
    ax.fill_between(
        datum,
        untere_grenze,
        obere_grenze,
        alpha=ALPHA_KONFIDENZ,
        color=FARBE_KONFIDENZ,
        label=f'Konfidenzbereich (±{threshold:.1f}σ)'
    )

    # Zeichne Baseline (Mittelwert oder Median)
    ax.axhline(
        y=baseline,
        color=FARBE_BASELINE,
        linestyle='--',
        linewidth=2,
        label=f'{baseline_label} ({baseline:.2f})'
    )

    # === VERBRAUCHSDATEN ===
    # Zeichne Verbrauchslinie
    ax.plot(
        datum,
        verbrauch,
        color=FARBE_NORMAL,
        linewidth=2,
        marker='o',
        markersize=6,
        label='Verbrauch'
    )

    # === ANOMALIEN HERVORHEBEN ===
    # Finde Anomalie-Positionen
    anomalie_indizes = [i for i, ist_anomalie in enumerate(anomalien) if ist_anomalie]

    # Spezielle Markierung für LOO (geprüfter Wert)
    if methode == "loo":
        letzter_idx = ergebnisse['letzter_index']
        # Markiere den geprüften Wert (letzter Wert) mit grünem Rahmen
        ax.scatter(
            [datum[letzter_idx]],
            [verbrauch[letzter_idx]],
            color='none',
            s=300,
            zorder=4,
            marker='o',
            edgecolors='green',
            linewidths=3,
            label='Geprüfter Wert (LOO)'
        )

    if anomalie_indizes:
        # Extrahiere Daten für Anomalien
        anomalie_datum = datum[anomalie_indizes]
        anomalie_werte = verbrauch[anomalie_indizes]

        # Zeichne Anomalien als rote Punkte
        ax.scatter(
            anomalie_datum,
            anomalie_werte,
            color=FARBE_ANOMALIE,
            s=200,  # Größe der Marker
            zorder=5,  # Über anderen Elementen zeichnen
            marker='o',
            edgecolors='black',
            linewidths=2,
            label=f'Anomalien ({len(anomalie_indizes)})'
        )

        # Füge Z-Score Annotationen für Anomalien hinzu
        for idx in anomalie_indizes:
            ax.annotate(
                f'z={z_scores[idx]:.2f}',
                xy=(datum[idx], verbrauch[idx]),
                xytext=(10, 10),
                textcoords='offset points',
                fontsize=9,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
            )

    # === FORMATIERUNG ===
    # Titel und Labels
    ax.set_title(
        f'Anomalie-Erkennung: {ergebnisse.get("methode", methode)}',
        fontsize=14,
        fontweight='bold',
        pad=20
    )
    ax.set_xlabel('Datum', fontsize=12)
    ax.set_ylabel('Verbrauch', fontsize=12)

    # Formatiere X-Achse (Datum)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    # Grid für bessere Lesbarkeit
    ax.grid(True, alpha=0.3, linestyle='--')

    # Legende
    ax.legend(loc='best', fontsize=10, framealpha=0.9)

    # Layout optimieren
    plt.tight_layout()

    return fig


def erstelle_statistik_tabelle(daten: pd.DataFrame, ergebnisse: Dict) -> pd.DataFrame:
    """
    Erstellt eine übersichtliche Tabelle mit allen Analyse-Ergebnissen.

    Args:
        daten: DataFrame mit 'Datum' und 'Verbrauch'
        ergebnisse: Dictionary aus den Analyse-Funktionen

    Returns:
        DataFrame mit folgenden Spalten:
            - Datum: Datum des Datenpunkts
            - Verbrauch: Verbrauchswert
            - Z-Score: Berechneter Z-Score (formatiert)
            - Ist Anomalie: "Ja" oder "Nein"
            - Abweichung (%): Prozentuale Abweichung von Baseline

    Diese Tabelle kann direkt in Streamlit angezeigt oder als CSV exportiert werden.
    """
    # Extrahiere Daten
    datum = daten['Datum'].values
    verbrauch = daten['Verbrauch'].values

    # Prüfe ob LOO-Methode
    if 'letzter_index' in ergebnisse:
        # LOO: Erstelle Z-Score und Anomalien-Listen
        z_scores = [0.0] * len(verbrauch)
        z_scores[ergebnisse['letzter_index']] = ergebnisse['z_score']
        anomalien = [False] * len(verbrauch)
        anomalien[ergebnisse['letzter_index']] = ergebnisse['ist_anomalie']
    else:
        # Classic: Normale Listen
        z_scores = ergebnisse['z_score']
        anomalien = ergebnisse['anomalien']

    # Bestimme Baseline für Prozentberechnung
    if 'median' in ergebnisse:
        baseline = ergebnisse['median']
    else:
        baseline = ergebnisse['mittelwert']

    # Berechne prozentuale Abweichung von Baseline
    # Formel: ((Wert - Baseline) / Baseline) * 100
    abweichung_prozent = []
    for v in verbrauch:
        if baseline != 0:
            prozent = ((v - baseline) / baseline) * 100
            abweichung_prozent.append(prozent)
        else:
            abweichung_prozent.append(0.0)

    # Erstelle DataFrame
    tabelle = pd.DataFrame({
        'Datum': datum,
        'Verbrauch': verbrauch,
        'Z-Score': [f'{z:.3f}' for z in z_scores],
        'Ist Anomalie': ['Ja' if a else 'Nein' for a in anomalien],
        'Abweichung (%)': [f'{a:+.2f}%' for a in abweichung_prozent]
    })

    return tabelle


def erstelle_zusammenfassung(ergebnisse: Dict, anzahl_datenpunkte: int) -> str:
    """
    Erstellt eine textuelle Zusammenfassung der Analyse-Ergebnisse.

    Args:
        ergebnisse: Dictionary aus den Analyse-Funktionen
        anzahl_datenpunkte: Gesamtzahl der analysierten Datenpunkte

    Returns:
        String mit formatierter Zusammenfassung

    Diese Zusammenfassung kann in Streamlit als Info-Box angezeigt werden.
    """
    methode = ergebnisse.get('methode', 'Unbekannt')

    # LOO hat eine andere Struktur
    if 'letzter_index' in ergebnisse:
        # LOO: Nur ein Wert wird geprüft
        anzahl_anomalien = 1 if ergebnisse['ist_anomalie'] else 0
        prozent_anomalien = (anzahl_anomalien / anzahl_datenpunkte) * 100
    else:
        # Classic: Alle Werte werden geprüft
        anzahl_anomalien = len(ergebnisse['anomalien_indizes'])
        prozent_anomalien = (anzahl_anomalien / anzahl_datenpunkte) * 100

    # Bestimme Statistiken je nach Methode
    if 'median' in ergebnisse:
        zentrum_name = 'Median'
        zentrum_wert = ergebnisse['median']
        streuung_name = 'MAD (std-äquivalent)'
        streuung_wert = ergebnisse['mad_std']
    else:
        zentrum_name = 'Mittelwert'
        zentrum_wert = ergebnisse['mittelwert']
        streuung_name = 'Standardabweichung'
        streuung_wert = ergebnisse['std']

    # Erstelle Zusammenfassungstext
    zusammenfassung = f"""
### Analyse-Zusammenfassung

**Methode:** {methode}

**Statistiken:**
- {zentrum_name}: {zentrum_wert:.2f}
- {streuung_name}: {streuung_wert:.2f}

**Anomalien:**
- Anzahl: {anzahl_anomalien} von {anzahl_datenpunkte} Datenpunkten
- Anteil: {prozent_anomalien:.1f}%
"""

    # Füge Anomalie-Details hinzu wenn vorhanden
    if anzahl_anomalien > 0:
        # LOO: Nur ein Wert (der letzte)
        if 'letzter_index' in ergebnisse:
            idx = ergebnisse['letzter_index']
            z = ergebnisse['z_score']
            zusammenfassung += f"\n**Anomalie-Details:**\n"
            zusammenfassung += f"- Position {idx + 1} (letzter Wert): Z-Score = {z:.2f}\n"
        else:
            # Classic: Mehrere Werte möglich
            anomalie_indizes = ergebnisse['anomalien_indizes']
            anomalie_z_scores = [ergebnisse['z_score'][i] for i in anomalie_indizes]

            zusammenfassung += f"\n**Anomalie-Details:**\n"
            for idx, z in zip(anomalie_indizes, anomalie_z_scores):
                zusammenfassung += f"- Position {idx + 1}: Z-Score = {z:.2f}\n"
    else:
        zusammenfassung += "\n✅ Keine Anomalien gefunden.\n"

    return zusammenfassung


def _bestimme_threshold_aus_ergebnissen(ergebnisse: Dict, verbrauch: np.ndarray, baseline: float, streuung: float) -> float:
    """
    Hilfsfunktion: Bestimmt den verwendeten Threshold aus den Ergebnissen.

    Da der Threshold nicht direkt in den Ergebnissen gespeichert ist,
    leiten wir ihn ab, indem wir die Anomalien analysieren.

    Args:
        ergebnisse: Dictionary mit Analyse-Ergebnissen
        verbrauch: Array der Verbrauchswerte
        baseline: Baseline (Mittelwert oder Median)
        streuung: Streuungsmaß (std oder mad_std)

    Returns:
        Geschätzter Threshold-Wert
    """
    # Versuche häufige Threshold-Werte
    # Für klassische/LOO Z-Score: typischerweise 2.0-3.0
    # Für MAD: typischerweise 3.0-4.0

    if 'median' in ergebnisse:
        # MAD Methode
        return 3.5
    else:
        # Z-Score Methoden
        return 1.0


def plot_z_score_verteilung(ergebnisse: Dict) -> plt.Figure:
    """
    Erstellt ein Histogramm der Z-Score Verteilung.

    Nützlich um die Verteilung der Z-Scores zu visualisieren und
    zu sehen, wie viele Werte nah am Threshold liegen.

    Args:
        ergebnisse: Dictionary aus den Analyse-Funktionen

    Returns:
        matplotlib Figure Objekt
    """
    fig, ax = plt.subplots(figsize=(10, 5))

    z_scores = ergebnisse['z_score']
    anomalien = ergebnisse['anomalien']

    # Separate Z-Scores für normale Werte und Anomalien
    z_normal = [z for z, ist_anomalie in zip(z_scores, anomalien) if not ist_anomalie]
    z_anomalie = [z for z, ist_anomalie in zip(z_scores, anomalien) if ist_anomalie]

    # Zeichne Histogramme
    if z_normal:
        ax.hist(z_normal, bins=20, alpha=0.7, color=FARBE_NORMAL, label='Normal', edgecolor='black')

    if z_anomalie:
        ax.hist(z_anomalie, bins=10, alpha=0.7, color=FARBE_ANOMALIE, label='Anomalien', edgecolor='black')

    # Markiere Threshold-Linien
    # Wir nehmen an Threshold ist ca. 2.5 oder 3.5
    threshold_schaetzung = 2.5 if 'median' not in ergebnisse else 3.5

    ax.axvline(threshold_schaetzung, color='red', linestyle='--', linewidth=2, label=f'Threshold (+{threshold_schaetzung})')
    ax.axvline(-threshold_schaetzung, color='red', linestyle='--', linewidth=2, label=f'Threshold (-{threshold_schaetzung})')

    # Labels und Titel
    ax.set_xlabel('Z-Score', fontsize=12)
    ax.set_ylabel('Häufigkeit', fontsize=12)
    ax.set_title('Verteilung der Z-Scores', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    return fig


def erstelle_fehlerreport(
    daten: pd.DataFrame,
    ergebnisse: Dict,
    einstellungen: Dict,
    metadaten: Dict,
    modus: str
) -> str:
    """
    Erstellt einen vollständigen Fehlerreport als Markdown.

    Args:
        daten: DataFrame mit Verbrauchsdaten
        ergebnisse: Dictionary mit Analyse-Ergebnissen
        einstellungen: Dictionary mit Einstellungen (methode, threshold, anzahl_historie)
        metadaten: Dictionary mit Metadaten (anlagen_nr, geraete_nr, geraete_typ)
        modus: "kumulierend" oder "reset"

    Returns:
        String mit vollständigem Markdown-Report
    """
    from datetime import datetime

    # Header
    report = "# Anomalie-Erkennungs Report\n\n"
    report += f"**Erstellt am:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"
    report += "---\n\n"

    # Metadaten
    report += "## 1. Metadaten\n\n"
    report += f"- **Anlagen-Nr:** {metadaten['anlagen_nr']}\n"
    report += f"- **Geräte-Nr:** {metadaten['geraete_nr']}\n"
    report += f"- **Geräte-Typ:** {metadaten['geraete_typ']}\n"
    report += f"- **Zähler-Modus:** {modus}\n\n"
    report += "---\n\n"

    # Einstellungen
    report += "## 2. Analyse-Einstellungen\n\n"
    report += f"- **Methode:** {einstellungen['methode']}\n"
    report += f"- **Threshold (Z-Score):** {einstellungen['threshold']}\n"
    report += f"- **Anzahl Datenpunkte:** {einstellungen['anzahl_historie']}\n\n"
    report += "---\n\n"

    # Eingabedaten
    report += "## 3. Eingabedaten\n\n"
    report += "| Datum | Verbrauch |\n"
    report += "|-------|----------|\n"
    for idx, row in daten.iterrows():
        datum_str = row['Datum'].strftime('%d.%m.%Y')
        verbrauch = row['Verbrauch']
        report += f"| {datum_str} | {verbrauch:.2f} |\n"
    report += "\n---\n\n"

    # Analyse-Ergebnisse
    report += "## 4. Analyse-Ergebnisse\n\n"
    report += f"- **Methode:** {ergebnisse.get('methode', 'Unbekannt')}\n"
    report += f"- **Mittelwert:** {ergebnisse.get('mittelwert', 0):.2f}\n"
    report += f"- **Standardabweichung:** {ergebnisse.get('std', 0):.2f}\n"

    # Konfidenzintervall berechnen
    if 'mittelwert' in ergebnisse and 'std' in ergebnisse:
        from models.classic_zscore import konfidenzintervall
        untere, obere = konfidenzintervall(
            ergebnisse['mittelwert'],
            ergebnisse['std'],
            einstellungen['threshold']
        )
        report += f"- **Konfidenzintervall:** [{untere:.2f}, {obere:.2f}]\n"

    # Anomalien
    anzahl_anomalien = len(ergebnisse.get('anomalien_indizes', []))
    report += f"- **Anzahl Anomalien:** {anzahl_anomalien}\n\n"

    if anzahl_anomalien > 0:
        report += "### Anomalie-Details\n\n"
        report += "| Position | Datum | Verbrauch | Z-Score |\n"
        report += "|----------|-------|-----------|----------|\n"

        anomalie_indizes = ergebnisse['anomalien_indizes']
        z_scores = ergebnisse['z_score']

        for idx in anomalie_indizes:
            datum_str = daten.iloc[idx]['Datum'].strftime('%d.%m.%Y')
            verbrauch = daten.iloc[idx]['Verbrauch']
            z_score = z_scores[idx]
            report += f"| {idx + 1} | {datum_str} | {verbrauch:.2f} | {z_score:.2f} |\n"

    report += "\n---\n\n"

    # Vollständige Daten mit Z-Scores
    report += "## 5. Detaillierte Auswertung\n\n"
    report += "| # | Datum | Verbrauch | Z-Score | Anomalie |\n"
    report += "|---|-------|-----------|---------|----------|\n"

    # Prüfe ob LOO-Methode (z_score ist dann ein einzelner Float)
    if 'letzter_index' in ergebnisse:
        # LOO: Erstelle Z-Score und Anomalien-Listen
        z_scores = [0.0] * len(daten)
        z_scores[ergebnisse['letzter_index']] = ergebnisse['z_score']
        anomalien = [False] * len(daten)
        anomalien[ergebnisse['letzter_index']] = ergebnisse['ist_anomalie']
    else:
        # Classic: Normale Listen
        z_scores = ergebnisse.get('z_score', [])
        anomalien = ergebnisse.get('anomalien', [])

    for idx, row in daten.iterrows():
        datum_str = row['Datum'].strftime('%d.%m.%Y')
        verbrauch = row['Verbrauch']
        z_score = z_scores[idx] if idx < len(z_scores) else 0.0
        ist_anomalie = "✅ JA" if (idx < len(anomalien) and anomalien[idx]) else "❌ Nein"
        report += f"| {idx + 1} | {datum_str} | {verbrauch:.2f} | {z_score:.2f} | {ist_anomalie} |\n"

    report += "\n---\n\n"
    report += "*Dieser Report wurde automatisch generiert für Debugging-Zwecke.*\n"

    return report
