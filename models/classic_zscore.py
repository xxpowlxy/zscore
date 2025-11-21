"""
Klassischer Z-Score

Alle Werte inkl. des zu testenden Wertes werden für Mittelwert/Std berechnet
Problem: Ein extremer Ausreißer verschiebt den Mittelwert und kann sich dadurch selbst "verstecken" (Masking-Effekt)
"""

import numpy as np
from typing import List, Dict                   # für type hints
DEFAULT_THRESHOLD_CLASSIC = 1.5                 # standard-schwellenwert für anomalie erkennung

def classic_zscore (
        verbrauch_liste: List[float],
        threshold: float = DEFAULT_THRESHOLD_CLASSIC
) -> Dict:
    """
    Findet Ausreißer im Verbrauch mit klassischem Z-Score.
    
    Beispiel:
        verbrauch = [100, 105, 98, 102, 250, 99]
        
        1. Mittelwert: 125.67 kWh
        2. Standardabweichung: 60.96 kWh
        3. Z-Score für 250 kWh: (250 - 125.67) / 60.96 = 2.04
        4. Bei threshold=2.5: KEINE Anomalie (2.04 < 2.5)
        
        Hinweis: Extreme Werte können sich durch Verschiebung des Mittelwerts selbst "verstecken".
    
    Args:
        verbrauch_liste: Monatliche Verbrauchswerte, KEINE kumulierende Zählerstände!
        threshold: Ab welchem |z-score| gilt ein Wert als Ausreißer
    
    Returns:{
        'mittelwert': float(mittelwert),
        'std': float(standardabweichung),
        'z_score': z_score,
        'anomalien': anomalien,
        'anomalien_indizes': anomalie_indizes,
        'methode': 'Klassicher Z-Score'
    }
    """

    verbrauch_array = np.array(verbrauch_liste)                     # liste -> numpy array
    mittelwert = np.mean(verbrauch_array)                           # Σ / n
    standardabweichung = np.std(verbrauch_array, ddof=1)            # ddof=1 -> s = √( Σ(x - μ)² / (n - 1) )

    # problem wenn standardabweichung 0 ist -> (wert / mittelwert) / standardabweichung (0) -> ERROR division durch null
    if standardabweichung == 0:
        z_score = [0.0] * len(verbrauch_liste)                      # liste mit 0.0 werten
        anomalien = [False] * len(verbrauch_liste)                  # liste mit false werten
        anomalie_indizes = []                                       # leere liste -> keine anomalien
    else:
        z_score = (verbrauch_array - mittelwert) / standardabweichung
        anomalien_array = np.abs(z_score) > threshold               # abs() = absolute value -> negative werte werden zu betrag

        z_score = z_score.tolist()
        anomalien = anomalien_array.tolist()

        anomalie_indizes = []
        for i, ist_anomalie in enumerate(anomalien):                # enumerate() gibt index i und value zurück
            if ist_anomalie:              
                anomalie_indizes.append(i)  

        """
        for i, ist_anomalie in enumerate(anomalien):
            │   │                          │
            │   │                          └─ Die Liste, die wir durchlaufen
            │   └─ Das ist der WERT an Position i
            └─ Das ist der INDEX
        """

        ergebnis = {
            'mittelwert': float(mittelwert),
            'std': float(standardabweichung),
            'z_score': z_score,
            'anomalien': anomalien,
            'anomalien_indizes': anomalie_indizes,
            'methode': 'Klassicher Z-Score'
        }

        return ergebnis
    
def konfidenzintervall(mittelwert: float, std: float, threshold: float) -> tuple:
    """
    Konfidenzintervall = "Normalbereich"

    Beispiel:
        mittelwert=100, std=10, threshold=2.5
        → untere_grenze = 100 - 2.5*10 = 75
        → obere_grenze = 100 + 2.5*10 = 125

    Args:
        mittelwert: Durchschnittswert
        std: Standardabweichung
        threshold: Z-Score Schwellenwert

    Returns:
        Tuple (untere_grenze, obere_grenze)
        Werte außerhalb dieses Intervalls werden als Anomalien betrachtet
    """
    untere_grenze = mittelwert - (threshold * std)
    obere_grenze = mittelwert + (threshold * std)

    return untere_grenze, obere_grenze