"""
Datenverarbeitungs-Modul für Verbrauchsdaten-Analyse

Dieses Modul enthält Funktionen zur Verarbeitung von Zählerständen und Verbrauchsdaten,
sowie zur Validierung der Eingabedaten.
"""

import pandas as pd
import numpy as np
from typing import Tuple, List


# === KONFIGURATION ===
MIN_DATENPUNKTE = 5
SPALTE_DATUM = 'Datum'
SPALTE_VERBRAUCH = 'Verbrauch'
SPALTE_ZAEHLERSTAND = 'Zaehlerstand'
# ====================


def berechne_verbrauch_aus_zaehlerstand(
    staende: List[float],
    datum: List,
    resets: List[bool]
) -> pd.DataFrame:
    """
    Berechnet Verbrauch aus Zählerständen.

    Der Verbrauch wird als Differenz zwischen aufeinanderfolgenden Zählerständen berechnet.
    Bei einem Reset (z.B. Zählerwechsel) wird der Verbrauch als der neue Zählerstand interpretiert.

    Args:
        staende: Liste der Zählerstände (chronologisch sortiert)
        datum: Liste der Datum-Werte (korrespondierend zu den Ständen)
        resets: Liste mit Boolean-Werten (True wenn Reset an dieser Position)

    Returns:
        DataFrame mit Spalten 'Datum' und 'Verbrauch'

    Logik:
        - Verbrauch = Stand_neu - Stand_alt
        - Bei Reset: Verbrauch = Stand_neu (da der Zähler bei 0 beginnt)
        - Erste Zeile hat keinen Verbrauch (kein vorheriger Wert) → wird übersprungen

    Beispiel:
        Datum       | Stand | Reset | Verbrauch
        ------------|-------|-------|----------
        2024-01-01  | 100   | False | -        (erste Zeile, kein Vorgänger)
        2024-02-01  | 150   | False | 50       (150 - 100)
        2024-03-01  | 200   | False | 50       (200 - 150)
        2024-04-01  | 30    | True  | 30       (Reset, neuer Zähler)
        2024-05-01  | 80    | False | 50       (80 - 30)
    """
    # Leere Liste für Verbrauchswerte
    verbrauch_liste = []
    datum_liste = []

    # Iteriere durch alle Zählerstände (ab dem zweiten Eintrag)
    for i in range(1, len(staende)):
        aktueller_stand = staende[i]
        vorheriger_stand = staende[i - 1]
        ist_reset = resets[i]

        # Wenn Reset markiert ist: Verbrauch = aktueller Stand
        # (Annahme: Zähler wurde gewechselt und startet bei 0)
        if ist_reset:
            verbrauch = aktueller_stand
        else:
            # Normaler Fall: Differenz zwischen aktuellem und vorherigem Stand
            verbrauch = aktueller_stand - vorheriger_stand

        # Füge Verbrauch zur Liste hinzu
        verbrauch_liste.append(verbrauch)
        datum_liste.append(datum[i])

    # Erstelle DataFrame aus den berechneten Werten
    df = pd.DataFrame({
        SPALTE_DATUM: datum_liste,
        SPALTE_VERBRAUCH: verbrauch_liste
    })

    return df


def validiere_eingabedaten(daten: pd.DataFrame) -> Tuple[bool, str]:
    """
    Prüft ob Eingabedaten valide sind.

    Args:
        daten: DataFrame mit mindestens den Spalten 'Datum' und 'Verbrauch'

    Returns:
        Tuple (is_valid, error_message)
        - is_valid: True wenn alle Checks bestanden, sonst False
        - error_message: Leerer String wenn valide, sonst Beschreibung des Fehlers

    Checks:
        1. Keine NaN-Werte in den wichtigen Spalten
        2. Datum in korrektem Format (wird von Streamlit sichergestellt)
        3. Mindestens MIN_DATENPUNKTE (5) Datenpunkte vorhanden
        4. Verbrauchswerte sind numerisch
    """
    # Check 1: DataFrame ist nicht leer
    if daten is None or len(daten) == 0:
        return False, "Keine Daten vorhanden. Bitte füllen Sie die Tabelle aus."

    # Check 2: Mindestanzahl an Datenpunkten
    if len(daten) < MIN_DATENPUNKTE:
        return False, f"Zu wenige Datenpunkte. Mindestens {MIN_DATENPUNKTE} Einträge erforderlich, {len(daten)} vorhanden."

    # Check 3: Keine NaN-Werte in Datum-Spalte
    if daten[SPALTE_DATUM].isna().any():
        anzahl_nan = daten[SPALTE_DATUM].isna().sum()
        return False, f"Fehlende Datumsangaben: {anzahl_nan} Zeile(n) ohne Datum."

    # Check 4: Keine NaN-Werte in Verbrauch-Spalte
    if daten[SPALTE_VERBRAUCH].isna().any():
        anzahl_nan = daten[SPALTE_VERBRAUCH].isna().sum()
        return False, f"Fehlende Verbrauchswerte: {anzahl_nan} Zeile(n) ohne Wert."

    # Check 5: Verbrauchswerte sind numerisch
    try:
        pd.to_numeric(daten[SPALTE_VERBRAUCH])
    except (ValueError, TypeError):
        return False, "Verbrauchswerte müssen numerisch sein."

    # Check 6: Datum aufsteigend sortiert (chronologisch)
    # Konvertiere zu datetime falls noch nicht geschehen
    try:
        datum_sortiert = pd.to_datetime(daten[SPALTE_DATUM])
        if not datum_sortiert.is_monotonic_increasing:
            return False, "Datumsangaben müssen chronologisch aufsteigend sein."
    except Exception:
        return False, "Ungültiges Datumsformat."

    # Alle Checks bestanden
    return True, ""


def lade_csv_daten(file, sep=';') -> Tuple[pd.DataFrame, str]:
    """
    Lädt CSV-Datei mit Fehlerbehandlung.

    Args:
        file: File-Objekt von Streamlit File Uploader
        sep: Trennzeichen (Standard: Semikolon)

    Returns:
        Tuple (DataFrame, error_message)
        - DataFrame: Geladene Daten oder None bei Fehler
        - error_message: Fehlermeldung oder leerer String

    Hinweise:
        - NaN-Werte werden automatisch ignoriert
        - Erwartet Spalten: 'Datum' und 'Verbrauch' (oder 'Zaehlerstand')
    """
    try:
        # Lade CSV-Datei
        df = pd.read_csv(file, sep=sep)

        # Entferne Zeilen mit NaN in allen Spalten (komplett leere Zeilen)
        df = df.dropna(how='all')

        # Prüfe ob notwendige Spalten vorhanden sind
        erforderliche_spalten = [SPALTE_DATUM]

        # Entweder 'Verbrauch' oder 'Zaehlerstand' muss vorhanden sein
        if SPALTE_VERBRAUCH not in df.columns and SPALTE_ZAEHLERSTAND not in df.columns:
            return None, f"CSV muss entweder Spalte '{SPALTE_VERBRAUCH}' oder '{SPALTE_ZAEHLERSTAND}' enthalten."

        if SPALTE_DATUM not in df.columns:
            return None, f"CSV muss Spalte '{SPALTE_DATUM}' enthalten."

        # Konvertiere Datum zu datetime
        df[SPALTE_DATUM] = pd.to_datetime(df[SPALTE_DATUM], errors='coerce')

        # Entferne Zeilen mit ungültigem Datum
        df = df.dropna(subset=[SPALTE_DATUM])

        # Sortiere nach Datum
        df = df.sort_values(by=SPALTE_DATUM)

        return df, ""

    except Exception as e:
        # Fehlerbehandlung mit aussagekräftiger Meldung
        fehler_text = f"Fehler beim Laden der CSV-Datei: {str(e)}"
        return None, fehler_text


def konvertiere_zu_dataframe(datum_liste: List, wert_liste: List, spaltenname: str) -> pd.DataFrame:
    """
    Hilfsfunktion: Konvertiert Listen zu DataFrame.

    Args:
        datum_liste: Liste mit Datumswerten
        wert_liste: Liste mit numerischen Werten
        spaltenname: Name für die Werte-Spalte (z.B. 'Verbrauch' oder 'Zaehlerstand')

    Returns:
        DataFrame mit Spalten 'Datum' und spaltenname
    """
    df = pd.DataFrame({
        SPALTE_DATUM: datum_liste,
        spaltenname: wert_liste
    })

    # Sortiere nach Datum
    df = df.sort_values(by=SPALTE_DATUM)
    df = df.reset_index(drop=True)

    return df
