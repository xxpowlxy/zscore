"""
Streamlit Frontend zur Anomalie-Erkennung
"""

import streamlit as st
import pandas as pd
import numpy as np

# models import
from typing import List, Dict
from models.classic_zscore import classic_zscore, konfidenzintervall

# utils von CLAUDE geschrieben
from utils.data_processing import (
    berechne_verbrauch_aus_zaehlerstand,
    validiere_eingabedaten,
    lade_csv_daten,
    konvertiere_zu_dataframe
)
from utils.visualization import (
    plot_anomalie_erkennung,
    erstelle_statistik_tabelle,
    erstelle_zusammenfassung,
    plot_z_score_verteilung,
    erstelle_fehlerreport
)


# config
DEFAULT_THRESHOLD_CLASSIC = 1.5
MIN_DATENPUNKTE = 5
MAX_DATENPUNKTE = 20
DEFAULT_HISTORIE = 12

# typen
GERAETE_TYPEN = ['EHKV', 'WMZ', 'KWZ', 'WWZ', 'STR']

# methoden-namen-mapping
METHODE_CLASSIC = "Klassischer Z-Score"

def setup_page():
    """ Konfigurieren der Streamlit-Start Seite mit Titel und Layout """
    st.set_page_config(
        page_title="Anomalie-Erkennung",
        page_icon="🕵🏻‍♀️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.header("Test Cases zur Anomalie-Erkennung in Verbrauchsdaten")
    st.markdown("""
    Dieses Projekt dient der Evaluierung verschiedener mathematischer Modelle zur Erkennung von Anomalien in Verbrauchsdaten.
    """)
    st.divider()

def sidebar_controls():
    """
    Erstellt die Sidebar mit allen Konfigurationsmöglichkeiten.
    """
    with st.sidebar:                                        # with ist ein context manager
        st.header("Einstellungen")                       # sonst müsste ich st.sidebar.header() schreiben

        # auswahl der methode / mathe modell
        st.subheader("mathematisches Modell")
        methode = st.radio(
        "Wählen Sie eine Modell:",
        [METHODE_CLASSIC],                                  # TODO: "leave one out zscore" implemintieren
        )

        st.divider()

        st.subheader("Schwellenwert / Z-score")

        if methode == METHODE_CLASSIC:
            default_threshold = DEFAULT_THRESHOLD_CLASSIC
            threshold_range = (1.0, 4.0)                    # min und max für den slider
        # else:

        threshold = st.slider(
            "Z-Score",
            min_value=threshold_range[0],                   # 0 Index -> 1.5
            max_value = threshold_range[1],                 # 1 Index -> 4.0
            value=default_threshold,
            step=0.1,                                       # steps für den slider
        )

        st.divider()

        st.subheader("Datenumfang")
        anzahl_historie= st.number_input(
            "Anzahl Datenpunkte",
            min_value=MIN_DATENPUNKTE,
            max_value=MAX_DATENPUNKTE,
            value=DEFAULT_HISTORIE,
            step=1,
            help=f"Mindestnes: {MIN_DATENPUNKTE} / Maximal: {MAX_DATENPUNKTE}"
        )

        return{
            'methode':methode,
            'threshold':threshold,
            'anzahl_historie':int(anzahl_historie)          # type hint ?
        }
    
def input_meta() -> dict:
    """
    Erstellt Eingabefenster für Metadaten

    Returns:
        Dictionary {
        'anlagen_nr': anlagen_nr,
        'geraete_nr': geraete_nr,
        'geraete_typ': geraete_typ
    }
    """
    st.subheader("Daten Eingabe")

    col1, col2, col3 = st.columns(3)                        # erstellt drei spalten nebeneinander und gibt ihnen namen (col1, col2, col3)

    with col1:
        anlagen_nr = st.text_input(                         # erwartet string input
            "Anlagen-Nr:",
            placeholder="100-999999-069"
        )

    with col2:
        geraete_nr = st.text_input(                         # erwartet string input
            "Geräte-Nr:",
            placeholder="28890929"
        )

    with col3:
        geraete_typ = st.selectbox(                         # erwartet vordefiniertes value aus GERAETE_TYPEN tuple
            "Typ:",
            options=GERAETE_TYPEN
        )
    
    return {
        'anlagen_nr': anlagen_nr,
        'geraete_nr': geraete_nr,
        'geraete_typ': geraete_typ
    }

def verbrauch_modus() -> str:
    """
    Switch zwischen kumulierende Zählerstände und (reset) Verbrauch
    
    Returns:
        String: "zaehlerstand" oder "verbrauch"
    """
    st.subheader("Zähler Fortschritt")
 
    col1, col2 = st.columns([1,3])                          # 2 col für layout
    
    with col1:                                              # 1.col switch
        ist_kumulierend = st.toggle(
            "Kumulierend",
            value=True
        )

    with col2:                                              # 2.col für info
        if ist_kumulierend:
            st.info("Kumulierenden Zählerstand eintragen (fortlaufender Zähler)")
        else:
            st.info("Verbrauch pro Monat eintragen (rückstellender Zähler)")

    return "kumulierend" if ist_kumulierend else "reset"          # kumulierender zählerst. neu - zählerst. alt = verbrauch

def input_data(anzahl_historie: int, modus: str) -> tuple:                                                
    """
    Erstellt eine dynamische Tabelle zur Dateneingabe.

    Args:
        anzahl_zeilen: Anzahl der Zeilen in der Tabelle
        modus: "zaehlerstand" oder "verbrauch"

    Returns:
        Tuple (datum_liste, wert_liste, reset_liste)
    """
    st.subheader("Daten Eingabe")

    if 'tabellen_daten' not in st.session_state:            # cookies
        st.session_state.tabellen_daten = []
    
    if modus == "kumulierend":                              # TODO: if i[2] < i[0] -> ERROR: zählerstand fällt unplusibel
        st.markdown("Wenn im angegebenen Zeitraum ein Gerätetausch stattgefunden hat, " \
        "aktivieren Sie bitte das Feld 'Tausch'. <br>"\
        "Andernfalls kann der Tausch als Anomalie erkannt werden und verfälscht die Auswertung.", unsafe_allow_html=True )  # html tags on
    else:
        st.markdown("Bei rückstellenden Zählern, die den monatlichen Verbrauch zählen, bitte den tatsächlichen Monatsverbrauch eintragen.")

    # container für tabelle
    datum_liste = []
    wert_liste = []
    tausch_liste = []

    # header
    if modus == "kumulierend":
        cols = st.columns([2, 2, 1])                        # relativen breiten 2:2:1
        cols[0].markdown("**Datum**")
        cols[1].markdown("**Zählerstand**")
        cols[2].markdown("**Tausch**")
    else:
        cols = st.columns([2, 2])                           # relativen breiten 2:2
        cols[0].markdown("**Datum**")
        cols[1].markdown("**Verbrauch**")

    # zeilen
    for i in range (anzahl_historie):
        if modus == "kumulierend":
            cols = st.columns([2, 2, 1])                    # relativen breiten 2:2:1
            
            # datum
            datum_wert = cols[0].date_input(
                f"Datum {i+1}",
                value=None,
                key=f"datum_{i}",
                label_visibility="collapsed"
            )

            # zählerstand
            wert = cols[1].number_input(
                f"Zählerstand {i+1}",
                min_value=0.0,
                value=0.0,                                  # keine negativen zählerstände
                step=1.0,
                format="%.2f",
                key=f"wert_{i}",
                label_visibility="collapsed"
            )

            # geräte tausch
            tausch = cols[2].checkbox(
                f"Reset {i+1}",
                value=False,
                key=f"reset_{i}",
                label_visibility="collapsed"
            )

            tausch_liste.append(tausch)

        else: # reset modus
            cols = st.columns([2, 2])                       # relativen breiten 2:2

            # datum
            datum_wert = cols[0].date_input(
                f"Datum {i+1}",
                value=None,
                key=f"datum_{i}",
                label_visibility="collapsed"
            )

            # verbrauch
            wert = cols[1].number_input(
                f"Verbrauch {i+1}",
                min_value=0.0,
                value=0.0,                                  # keine negativen verbräuche
                step=1.0,
                format="%.2f",
                key=f"wert_{i}",
                label_visibility="collapsed"
            )

        if datum_wert is not None:
            datum_liste.append(datum_wert)
            wert_liste.append(wert)
            
    return datum_liste, wert_liste, tausch_liste

def valid_meta(metadaten: dict) -> tuple:
    """
    Validiert die eingegebenen Metadaten.

    Args:
        metadaten: Dictionary mit Metadaten

    Returns:
        Tuple (is_valid, error_message)
    """
    if not metadaten['anlagen_nr']:
        return False, "Bitte geben Sie eine Anlagen-Nr ein."

    if not metadaten['geraete_nr']:
        return False, "Bitte geben Sie eine Geräte-Nr ein."

    return True, ""

def analyse(                                                
        daten: pd.DataFrame,                                # type hint pandas dataframe
        methode: str, 
        threshold: float
)-> dict: 
    """
    Führt die gewählte Analyse-Methode durch.

    Args:
        daten: DataFrame mit Verbrauchsdaten
        methode: Name der Methode
        threshold: Schwellenwert

    Returns:
        Dictionary mit Analyse-Ergebnissen
    """

    # extrahiere verbrauchswerte 
    verbrauch_liste = daten['Verbrauch'].tolist()

    if methode == METHODE_CLASSIC:
        ergebniss = classic_zscore(verbrauch_liste, threshold)
    # TODO: "leave one out zscore" implemintieren

    return ergebniss

def zeige_ergebnisse(
        daten: pd.DataFrame,
        ergebniss: dict,
        methode: str,
        metadaten: dict,
        einstellungen: dict,
        modus: str
):
    """
    Zeigt die Analyse-Ergebnisse an.

    Die Utils in dieser Funktion sind alle von CLAUDE CODE geschrieben.

    Args:
        daten: DataFrame mit Verbrauchsdaten
        ergebnisse: Dictionary mit Analyse-Ergebnissen
        methode: Name der verwendeten Methode
        metadaten: Metadaten für die Anzeige
        einstellungen: Dictionary mit Einstellungen
        modus: "kumulierend" oder "reset"
    """
    st.success("Analyse erfolgreich durchgeführt!")

    zusammenfassung = erstelle_zusammenfassung(ergebniss, len(daten))
    st.markdown(zusammenfassung)

    # Download-Button für Fehlerreport
    fehlerreport = erstelle_fehlerreport(daten, ergebniss, einstellungen, metadaten, modus)

    st.download_button(
        label="Report herunterladen (Markdown)",
        data=fehlerreport,
        file_name=f"anomalie_report_{metadaten['geraete_nr']}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown",
        help="Lädt einen vollständigen Report mit allen Daten und Ergebnissen herunter"
    )

    # erstelle tabs
    tab1, tab2, tab3 = st.tabs([
        "Diagramm",
        "Statistik",
        "Verbrauch"
    ])
    
    with tab1:
        st.subheader("")                                                    # Diagramm

        if methode == METHODE_CLASSIC:
            methode_key = "classic"
        # TODO: "leave one out zscore" implemintieren

        try:
            fig = plot_anomalie_erkennung(daten, ergebniss, methode_key)
            st.pyplot(fig)
        except Exception as e:
            st.error(f"Fehler beim Erstellen des Plots: {e}")

    with tab2:
        st.subheader("")                                                    # Statistik

        statistik_tabelle = erstelle_statistik_tabelle(daten, ergebniss)    # erstelle tabelle

        st.dataframe(                                                       # zeige tabelle
            statistik_tabelle,
            use_container_width=True
            # hide_index=True
        )

    with tab3:
        st.subheader("")                                                    # Verbrauch

        st.dataframe(
            daten,
            use_container_width=True,
            hide_index=True
        )


def main():
    setup_page()                                 # layout page
    einstellungen = sidebar_controls()           # einstellungen
    metadaten = input_meta()                     # metadaten eingabe
    modus = verbrauch_modus()

    # return von input_data() in main() funktion übernehmen
    datum_liste, wert_liste, tausch_liste = input_data(
    einstellungen['anzahl_historie'],
    modus
)

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        reset_button = st.button(
            "Zurücksetzen",
            use_container_width=True,
            help="Alle Eingabefelder zurücksetzen"
        )

    with col2:
        analyse_button = st.button(
            "Analyse starten",
            type="primary",
            use_container_width=True
        )

    # col3 bleibt leer für symmetrisches Layout

    # Reset-Funktionalität
    if reset_button:
        # Lösche alle Session State Keys die mit den Eingabefeldern zusammenhängen
        keys_to_delete = [key for key in st.session_state.keys()
                         if key.startswith(('datum_', 'wert_', 'reset_', 'tabellen_daten'))]
        for key in keys_to_delete:
            del st.session_state[key]
        st.rerun()  # Seite neu laden

    if analyse_button:
        meta_valid, meta_error = valid_meta(metadaten)
        if not meta_valid:
            st.error(f"{meta_error}")
            return
        
        # prüfe datenumfang
        if len(datum_liste) < MIN_DATENPUNKTE:
            st.error(f"Zu wenige Datenpunkte. Mindestens {MIN_DATENPUNKTE} Einträge erforderlich.")
            return

        # df je nach modus kumu. / reset
        if modus == "kumulierend":
        # berechne verbrauch aus kumu. zählerstand
            daten = berechne_verbrauch_aus_zaehlerstand(
                wert_liste,
                datum_liste,
                tausch_liste
                )
        else:
            daten = konvertiere_zu_dataframe(
                wert_liste,
                datum_liste,
                'Verbrauch'
            )
    
        # TODO: daten validieren

        with st.spinner("Analysiere Daten..."):      # spinner lade sym
            ergebniss = analyse(
                daten,
                einstellungen['methode'],
                einstellungen['threshold']
            )
    
        zeige_ergebnisse(daten, ergebniss, einstellungen['methode'], metadaten, einstellungen, modus)
        # robuster mit try except schleife ?
    
if __name__ == "__main__":
    main()