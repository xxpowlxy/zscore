"""
Leave-One-Out Z-Score

Der zu testende Wert wird aus der Berechnung von Mittelwert/Std ausgeschlossen.
Dies verhindert den Masking-Effekt, bei dem extreme Ausreißer sich selbst "verstecken".

Anwendungsfall: Validierung des LETZTEN Zählerstands gegen die historischen Daten.
"""

import numpy as np
from typing import List, Dict

DEFAULT_THRESHOLD_LOO = 2.0  # standard-schwellenwert für LOO anomalie erkennung


def loo_zscore(
        verbrauch_liste: List[float],
        threshold: float = DEFAULT_THRESHOLD_LOO
) -> Dict:
    """
    Findet Ausreißer im Verbrauch mit Leave-One-Out Z-Score.

    Der LETZTE Wert wird gegen alle vorherigen Werte geprüft.

    Beispiel:
        verbrauch = [100, 105, 98, 102, 99, 250]

        Für den LETZTEN Wert (250):
        1. Mittelwert OHNE 250: (100+105+98+102+99)/5 = 100.8 kWh
        2. Standardabweichung OHNE 250: 2.86 kWh
        3. Z-Score für 250: (250 - 100.8) / 2.86 = 52.17
        4. Bei threshold=2.0: ANOMALIE! (52.17 > 2.0)

        Vorteil: Der extreme Wert 250 kann sich nicht selbst "verstecken",
                 da er nicht in die Berechnung von μ und σ einfließt.

    Args:
        verbrauch_liste: Monatliche Verbrauchswerte (chronologisch sortiert)
        threshold: Ab welchem |z-score| gilt der letzte Wert als Ausreißer

    Returns:
        {
            'mittelwert': float,           # Mittelwert OHNE letzten Wert
            'std': float,                  # Std OHNE letzten Wert
            'z_score': float,              # Z-Score des letzten Wertes
            'ist_anomalie': bool,          # True wenn letzter Wert Anomalie ist
            'letzter_wert': float,         # Der geprüfte Wert
            'letzter_index': int,          # Index des geprüften Wertes
            'methode': str,
            'threshold': float
        }
    """

    if len(verbrauch_liste) < 2:
        raise ValueError("Mindestens 2 Datenpunkte erforderlich für Leave-One-Out Analyse")

    verbrauch_array = np.array(verbrauch_liste)

    # Trenne letzten Wert von den restlichen
    letzter_wert = verbrauch_array[-1]
    letzter_index = len(verbrauch_liste) - 1
    historische_werte = verbrauch_array[:-1]  # Alle außer dem letzten

    # Berechne Statistik NUR aus historischen Werten
    mittelwert = np.mean(historische_werte)
    standardabweichung = np.std(historische_werte, ddof=1)

    # Berechne Z-Score für den letzten Wert
    if standardabweichung == 0:
        # Wenn alle historischen Werte gleich sind
        if letzter_wert == mittelwert:
            z_score = 0.0
            ist_anomalie = False
        else:
            # Letzter Wert unterscheidet sich von konstanten historischen Werten
            z_score = np.inf if letzter_wert > mittelwert else -np.inf
            ist_anomalie = True
    else:
        z_score = (letzter_wert - mittelwert) / standardabweichung
        ist_anomalie = abs(z_score) > threshold

    ergebnis = {
        'mittelwert': float(mittelwert),
        'std': float(standardabweichung),
        'z_score': float(z_score),
        'ist_anomalie': bool(ist_anomalie),
        'letzter_wert': float(letzter_wert),
        'letzter_index': letzter_index,
        'methode': 'Leave-One-Out Z-Score',
        'threshold': float(threshold)
    }

    return ergebnis


def konfidenzintervall_loo(mittelwert: float, std: float, threshold: float) -> tuple:
    """
    Konfidenzintervall für LOO = "Normalbereich" basierend auf historischen Daten

    Beispiel:
        mittelwert=100, std=10, threshold=2.0
        → untere_grenze = 100 - 2.0*10 = 80
        → obere_grenze = 100 + 2.0*10 = 120

    Args:
        mittelwert: Durchschnitt der historischen Werte (OHNE letzten Wert)
        std: Standardabweichung der historischen Werte
        threshold: Z-Score Schwellenwert

    Returns:
        Tuple (untere_grenze, obere_grenze)
        Der letzte Wert wird als Anomalie betrachtet, wenn er außerhalb liegt
    """
    untere_grenze = mittelwert - (threshold * std)
    obere_grenze = mittelwert + (threshold * std)

    return untere_grenze, obere_grenze
