"""
Datamodeller för fördelningssystemet.

Dessa klasser definierar strukturen för ansökningar, ledamöter och fördelningar.
De är också definierade i fordelning.py men exporteras härifrån för tydlighet.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Ansokan:
    """
    Representerar en forskningsansökan.
    
    Attributes:
        ans_no: Unikt ansökningsnummer (t.ex. "KP2024-0001")
        huvudsokande: Namn på den som söker anslag
        forskningskategori: Grundforskning, Translationell eller Klinisk
        omrade: Forskningsområde
        diagnos: Cancerdiagnos som forskningen rör
        nyckelord: Lista med nyckelord som beskriver forskningen
    """
    ans_no: str
    huvudsokande: str
    forskningskategori: str
    omrade: str
    diagnos: str
    nyckelord: list[str]


@dataclass
class Ledamot:
    """
    Representerar en ledamot i en prioriteringsgrupp.
    
    Attributes:
        namn: Ledamotens fullständiga namn
        initialer: Unika initialer (t.ex. "GB")
        grupp: Prioriteringsgrupp (Bio I, Bio II eller Bio III)
        roll: Ordförande eller Ledamot
        forskningskategori: Ledamotens kompetensområde
        nyckelord: Lista med nyckelord som beskriver kompetens
    """
    namn: str
    initialer: str
    grupp: str
    roll: str
    forskningskategori: str
    nyckelord: list[str]
    
    @property
    def ar_ordforande(self) -> bool:
        """Returnerar True om ledamoten är ordförande."""
        return self.roll.lower() == 'ordförande'


@dataclass
class Fordelning:
    """
    Representerar en tilldelad fördelning.
    
    Attributes:
        ans_no: Ansökningsnummer
        huvudsokande: Den sökandes namn
        grupp: Tilldelad prioriteringsgrupp
        ledamot_namn: Föredragandes namn
        ledamot_initialer: Föredragandes initialer
        motivering: Textbeskrivning av varför denna fördelning gjordes
        osakert: True om fördelningen är osäker (t.ex. alla ordförande jäviga)
    """
    ans_no: str
    huvudsokande: str
    grupp: str
    ledamot_namn: str
    ledamot_initialer: str
    motivering: str
    osakert: bool = False


@dataclass
class FordelningsResultat:
    """
    Sammanfattning av en fördelningskörning.
    
    Attributes:
        fordelningar: Lista med alla fördelningar
        antal_ansokningar: Totalt antal ansökningar
        antal_ledamoter: Totalt antal ledamöter
        antal_javsrelationer: Totalt antal jävsrelationer
        antal_osakra: Antal osäkra fördelningar
        per_grupp: Dict med antal per grupp
        per_ledamot: Dict med antal per ledamot
    """
    fordelningar: list[Fordelning]
    antal_ansokningar: int
    antal_ledamoter: int
    antal_javsrelationer: int
    antal_osakra: int
    per_grupp: dict[str, int]
    per_ledamot: dict[str, int]
