"""
Fördelningsalgoritm för Barncancerfondens forskningsansökningar.

Denna modul innehåller all logik för att fördela forskningsansökningar
till prioriteringsgrupper och ledamöter baserat på jävsrelationer,
kompetensmatching och balansering.

Författare: Tech Sisters AB
Version: 1.0.0
"""

import pandas as pd
from dataclasses import dataclass
from typing import Optional
from collections import Counter


@dataclass
class Ansokan:
    """Representerar en forskningsansökan."""
    ans_no: str
    huvudsokande: str
    forskningskategori: str
    omrade: str
    diagnos: str
    nyckelord: list[str]


@dataclass
class Ledamot:
    """Representerar en ledamot i en prioriteringsgrupp."""
    namn: str
    initialer: str
    grupp: str
    roll: str
    forskningskategori: str
    nyckelord: list[str]
    
    @property
    def ar_ordforande(self) -> bool:
        return self.roll.lower() == 'ordförande'


@dataclass
class Fordelning:
    """Representerar en tilldelad fördelning."""
    ans_no: str
    huvudsokande: str
    grupp: str
    ledamot_namn: str
    ledamot_initialer: str
    motivering: str
    osakert: bool = False


class Fordelningsmotor:
    """
    Motor för att fördela forskningsansökningar till prioriteringsgrupper och ledamöter.
    
    Prioritetsordning:
    1. Ordförande i tilldelad grupp får ALDRIG vara jävig
    2. Minimera antal jäviga i gruppen
    3. Balansera mellan grupper (~50 var)
    4. Balansera mellan ledamöter (5-7 var)
    5. Matcha på forskningskategori och nyckelord
    """
    
    GRUPPER = ['Bio I', 'Bio II', 'Bio III']
    
    def __init__(self, ansokningar: list[Ansokan], ledamoter: list[Ledamot], 
                 javsrelationer: dict[str, set[str]]):
        """
        Initialisera motorn.
        
        Args:
            ansokningar: Lista med alla ansökningar
            ledamoter: Lista med alla ledamöter
            javsrelationer: Dict där nyckel är initialer och värde är set av ans_no
        """
        self.ansokningar = ansokningar
        self.ledamoter = ledamoter
        self.javsrelationer = javsrelationer
        
        # Skapa uppslagsstrukturer
        self.ledamoter_per_grupp = self._gruppera_ledamoter()
        self.ordforande_per_grupp = self._hitta_ordforande()
        
        # Räknare för balansering
        self.ansokningar_per_grupp = Counter()
        self.ansokningar_per_ledamot = Counter()
        
    def _gruppera_ledamoter(self) -> dict[str, list[Ledamot]]:
        """Gruppera ledamöter per prioriteringsgrupp."""
        grupper = {g: [] for g in self.GRUPPER}
        for ledamot in self.ledamoter:
            if ledamot.grupp in grupper:
                grupper[ledamot.grupp].append(ledamot)
        return grupper
    
    def _hitta_ordforande(self) -> dict[str, Optional[Ledamot]]:
        """Hitta ordförande för varje grupp."""
        ordforande = {}
        for grupp, ledamoter in self.ledamoter_per_grupp.items():
            ordforande[grupp] = next(
                (l for l in ledamoter if l.ar_ordforande), 
                None
            )
        return ordforande
    
    def _ar_javig(self, initialer: str, ans_no: str) -> bool:
        """Kontrollera om en ledamot är jävig mot en ansökan."""
        return ans_no in self.javsrelationer.get(initialer, set())
    
    def _antal_javiga_i_grupp(self, grupp: str, ans_no: str) -> int:
        """Räkna antal jäviga ledamöter i en grupp för en ansökan."""
        return sum(
            1 for l in self.ledamoter_per_grupp[grupp]
            if self._ar_javig(l.initialer, ans_no)
        )
    
    def _ordforande_ar_javig(self, grupp: str, ans_no: str) -> bool:
        """Kontrollera om ordförande är jävig i en grupp."""
        ordf = self.ordforande_per_grupp.get(grupp)
        if ordf is None:
            return False
        return self._ar_javig(ordf.initialer, ans_no)
    
    def _berakna_kompetens_score(self, ansokan: Ansokan, ledamot: Ledamot) -> float:
        """
        Beräkna kompetens-score mellan ansökan och ledamot.
        
        Returns:
            Score mellan 0.0 och 1.0 där högre är bättre match
        """
        score = 0.0
        
        # Forskningskategori-match (primär, väger 60%)
        if ledamot.forskningskategori and ansokan.forskningskategori:
            if ledamot.forskningskategori.lower() in ansokan.forskningskategori.lower() or \
               ansokan.forskningskategori.lower() in ledamot.forskningskategori.lower():
                score += 0.6
        
        # Nyckelords-match (sekundär, väger 40%)
        if ledamot.nyckelord and ansokan.nyckelord:
            ansokan_nyckelord = set(n.lower().strip() for n in ansokan.nyckelord)
            ledamot_nyckelord = set(n.lower().strip() for n in ledamot.nyckelord)
            
            # Hitta överlapp
            overlap = ansokan_nyckelord & ledamot_nyckelord
            if overlap:
                # Partiell match baserat på hur många som överlappar
                match_ratio = len(overlap) / max(len(ansokan_nyckelord), 1)
                score += 0.4 * min(match_ratio, 1.0)
            
            # Bonus för delvis matchande ord (t.ex. "leukemi" i "akut leukemi")
            for an in ansokan_nyckelord:
                for ln in ledamot_nyckelord:
                    if an in ln or ln in an:
                        score += 0.05
        
        return min(score, 1.0)
    
    def _valj_grupp(self, ansokan: Ansokan) -> tuple[str, bool, list[str]]:
        """
        Välj bästa grupp för en ansökan.
        
        Returns:
            Tuple med (grupp, osakert, lista med jäviga i gruppen)
        """
        kandidater = []
        
        for grupp in self.GRUPPER:
            ordf_javig = self._ordforande_ar_javig(grupp, ansokan.ans_no)
            antal_javiga = self._antal_javiga_i_grupp(grupp, ansokan.ans_no)
            antal_i_grupp = self.ansokningar_per_grupp[grupp]
            
            # Hitta jäviga initialer
            javiga_i_grupp = [
                l.initialer for l in self.ledamoter_per_grupp[grupp]
                if self._ar_javig(l.initialer, ansokan.ans_no)
            ]
            
            kandidater.append({
                'grupp': grupp,
                'ordf_javig': ordf_javig,
                'antal_javiga': antal_javiga,
                'antal_i_grupp': antal_i_grupp,
                'javiga_initialer': javiga_i_grupp
            })
        
        # Sortera: 
        # 1. Ordförande EJ jävig först
        # 2. Färre jäviga
        # 3. Färre ansökningar (balans)
        kandidater.sort(key=lambda k: (
            k['ordf_javig'],      # False < True
            k['antal_javiga'],    # Färre jäviga bättre
            k['antal_i_grupp']    # Färre ansökningar bättre
        ))
        
        basta = kandidater[0]
        
        # Markera som osäker om ordförande är jävig i ALLA grupper
        alla_ordf_javiga = all(k['ordf_javig'] for k in kandidater)
        
        return basta['grupp'], alla_ordf_javiga, basta['javiga_initialer']
    
    def _valj_ledamot(self, ansokan: Ansokan, grupp: str) -> Ledamot:
        """
        Välj bästa ledamot för en ansökan inom en grupp.
        
        Returns:
            Vald ledamot
        """
        kandidater = []
        
        for ledamot in self.ledamoter_per_grupp[grupp]:
            # Hoppa över ordförande och jäviga
            if ledamot.ar_ordforande:
                continue
            if self._ar_javig(ledamot.initialer, ansokan.ans_no):
                continue
            
            kompetens_score = self._berakna_kompetens_score(ansokan, ledamot)
            antal_tilldelade = self.ansokningar_per_ledamot[ledamot.initialer]
            
            kandidater.append({
                'ledamot': ledamot,
                'kompetens_score': kompetens_score,
                'antal_tilldelade': antal_tilldelade
            })
        
        if not kandidater:
            # Fallback: ta första icke-jäviga (även ordförande om nödvändigt)
            for ledamot in self.ledamoter_per_grupp[grupp]:
                if not self._ar_javig(ledamot.initialer, ansokan.ans_no):
                    return ledamot
            # Sista utväg: ta första i gruppen
            return self.ledamoter_per_grupp[grupp][0]
        
        # Sortera:
        # 1. Högre kompetens-score
        # 2. Färre tilldelade ansökningar (balans)
        kandidater.sort(key=lambda k: (
            -k['kompetens_score'],    # Högre score bättre (negativ för stigande sort)
            k['antal_tilldelade']    # Färre tilldelade bättre
        ))
        
        return kandidater[0]['ledamot']
    
    def _skapa_motivering(self, ansokan: Ansokan, ledamot: Ledamot, 
                          grupp: str, javiga_i_gruppen: list[str],
                          osakert: bool) -> str:
        """Skapa en detaljerad motivering för fördelningen."""
        delar = []
        
        # Beskrivning av ansökan
        if ansokan.diagnos and str(ansokan.diagnos).lower() != 'nan':
            delar.append(f"Ansökan inom {ansokan.diagnos}")
        elif ansokan.omrade and str(ansokan.omrade).lower() != 'nan':
            delar.append(f"Ansökan inom {ansokan.omrade}")
        elif ansokan.nyckelord:
            delar.append(f"Ansökan matchar {', '.join(ansokan.nyckelord[:2])}")
        else:
            delar.append(f"Ansökan i kategori {ansokan.forskningskategori}")
        
        # Ledamotens kompetens
        if ledamot.nyckelord:
            kompetens_str = ', '.join(ledamot.nyckelord[:3])
            delar.append(f"{ledamot.initialer} har kompetens inom {kompetens_str}")
        elif ledamot.forskningskategori:
            delar.append(f"{ledamot.initialer} har kompetens inom {ledamot.forskningskategori}")
        
        # Jävsinfo
        if javiga_i_gruppen:
            andra_grupper_jav = []
            for g in self.GRUPPER:
                if g != grupp:
                    jav_i_g = [
                        l.initialer for l in self.ledamoter_per_grupp[g]
                        if self._ar_javig(l.initialer, ansokan.ans_no)
                    ]
                    if jav_i_g:
                        andra_grupper_jav.append(f"{g} ({', '.join(jav_i_g)})")
            
            if andra_grupper_jav:
                delar.append(f"Jäv fanns i {', '.join(andra_grupper_jav)}")
            
            if javiga_i_gruppen:
                delar.append(f"I vald grupp är {', '.join(javiga_i_gruppen)} jäviga, men ej {ledamot.initialer}")
        else:
            delar.append(f"Ingen jäv identifierad mot {ledamot.initialer}")
        
        # Balanseringsinfo
        delar.append(f"Val av {grupp} bidrar till balanserad fördelning")
        
        # Osäkerhetsmarkering
        if osakert:
            delar.insert(0, "OSÄKER PLACERING: Alla ordförande är jäviga.")
        
        return "; ".join(delar) + "."
    
    def fordela(self) -> list[Fordelning]:
        """
        Utför fördelningen av alla ansökningar.
        
        Returns:
            Lista med alla fördelningar
        """
        fordelningar = []
        
        # Sortera ansökningar för konsekvent resultat
        sorterade = sorted(self.ansokningar, key=lambda a: a.ans_no)
        
        for ansokan in sorterade:
            # Steg 1-3: Välj grupp
            grupp, osakert, javiga_i_gruppen = self._valj_grupp(ansokan)
            
            # Steg 4-5: Välj ledamot
            ledamot = self._valj_ledamot(ansokan, grupp)
            
            # Steg 6: Skapa motivering
            motivering = self._skapa_motivering(
                ansokan, ledamot, grupp, javiga_i_gruppen, osakert
            )
            
            # Skapa fördelning
            fordelning = Fordelning(
                ans_no=ansokan.ans_no,
                huvudsokande=ansokan.huvudsokande,
                grupp=grupp,
                ledamot_namn=ledamot.namn,
                ledamot_initialer=ledamot.initialer,
                motivering=motivering,
                osakert=osakert
            )
            fordelningar.append(fordelning)
            
            # Uppdatera räknare
            self.ansokningar_per_grupp[grupp] += 1
            self.ansokningar_per_ledamot[ledamot.initialer] += 1
        
        return fordelningar


def las_ansokningar(filepath: str, separator: str = ';') -> list[Ansokan]:
    """Läs ansökningar från CSV/Excel-fil."""
    df = pd.read_csv(filepath, sep=separator, encoding='utf-8')
    
    ansokningar = []
    for _, row in df.iterrows():
        nyckelord_raw = str(row.get('Nyckelord', ''))
        nyckelord = [n.strip() for n in nyckelord_raw.split(',') if n.strip()]
        
        ansokan = Ansokan(
            ans_no=str(row.get('Ans no', row.get('Ansökningsnummer', ''))).strip(),
            huvudsokande=str(row.get('Huvudsökande', row.get('Sökande', ''))).strip(),
            forskningskategori=str(row.get('F.kat', row.get('Forskningskategori', ''))).strip(),
            omrade=str(row.get('Område', '')).strip(),
            diagnos=str(row.get('Diagnos', '')).strip(),
            nyckelord=nyckelord
        )
        ansokningar.append(ansokan)
    
    return ansokningar


def las_ledamoter(filepath: str, separator: str = ';') -> list[Ledamot]:
    """Läs ledamöter från CSV/Excel-fil."""
    df = pd.read_csv(filepath, sep=separator, encoding='utf-8')
    
    ledamoter = []
    for _, row in df.iterrows():
        nyckelord_raw = str(row.get('Nyckelord', ''))
        nyckelord = [n.strip() for n in nyckelord_raw.split(',') if n.strip()]
        
        # Hantera olika kolumnnamn för grupp
        grupp = str(row.get('Prioriteringsgrupp', row.get('Grupp', ''))).strip()
        
        # Hantera namn - kan vara separata kolumner eller en
        fornamn = str(row.get('Förnamn', '')).strip()
        efternamn = str(row.get('Efternamn', '')).strip()
        if fornamn and efternamn:
            namn = f"{fornamn} {efternamn}"
        else:
            namn = str(row.get('Namn', f"{fornamn} {efternamn}")).strip()
        
        ledamot = Ledamot(
            namn=namn,
            initialer=str(row.get('Initialer', '')).strip(),
            grupp=grupp,
            roll=str(row.get('Roll', 'Ledamot')).strip(),
            forskningskategori=str(row.get('Forskningskategori', '')).strip(),
            nyckelord=nyckelord
        )
        ledamoter.append(ledamot)
    
    return ledamoter


def las_javsrelationer(filepath: str, separator: str = ';') -> dict[str, set[str]]:
    """
    Läs jävsrelationer från CSV/Excel-fil.
    
    Returns:
        Dict där nyckel är ledamotens initialer och värde är set av ans_no
    """
    df = pd.read_csv(filepath, sep=separator, encoding='utf-8')
    
    jav = {}
    for _, row in df.iterrows():
        # Hitta rätt kolumnnamn
        initialer = str(row.get('Ledamot', row.get('Initialer', ''))).strip()
        ans_no = str(row.get('Ans no', row.get('Ansökningsnummer', row.get('Ansökan', '')))).strip()
        
        if initialer and ans_no:
            if initialer not in jav:
                jav[initialer] = set()
            jav[initialer].add(ans_no)
    
    return jav


def exportera_till_excel(fordelningar: list[Fordelning], 
                         ledamoter: list[Ledamot],
                         output_path: str):
    """Exportera fördelningar till Excel med flera flikar."""
    
    # Flik 1: Fördelning
    fordelning_data = []
    for f in fordelningar:
        fordelning_data.append({
            'Ans no': f.ans_no,
            'Huvudsökande': f.huvudsokande,
            'Grupp': f.grupp,
            'Föredragande': f.ledamot_namn,
            'Initialer': f.ledamot_initialer,
            'Motivering': f.motivering,
            'Osäker': 'JA' if f.osakert else ''
        })
    df_fordelning = pd.DataFrame(fordelning_data)
    
    # Flik 2: Statistik
    grupp_stats = df_fordelning.groupby('Grupp').size().reset_index(name='Antal ansökningar')
    ledamot_stats = df_fordelning.groupby(['Grupp', 'Föredragande', 'Initialer']).size().reset_index(name='Antal')
    
    # Flik 3: Ledamöter per grupp
    ledamot_data = []
    for l in ledamoter:
        ledamot_data.append({
            'Grupp': l.grupp,
            'Namn': l.namn,
            'Initialer': l.initialer,
            'Roll': l.roll,
            'Forskningskategori': l.forskningskategori,
            'Nyckelord': ', '.join(l.nyckelord) if l.nyckelord else ''
        })
    df_ledamoter = pd.DataFrame(ledamot_data)
    
    # Skriv till Excel
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df_fordelning.to_excel(writer, sheet_name='Fördelning', index=False)
        grupp_stats.to_excel(writer, sheet_name='Statistik - Grupper', index=False)
        ledamot_stats.to_excel(writer, sheet_name='Statistik - Ledamöter', index=False)
        df_ledamoter.to_excel(writer, sheet_name='Ledamöter per grupp', index=False)


def kör_fordelning(ansokningar_fil: str, ledamoter_fil: str, jav_fil: str,
                   output_fil: str, separator: str = ';') -> dict:
    """
    Huvudfunktion för att köra hela fördelningen.
    
    Args:
        ansokningar_fil: Sökväg till ansökningsfil
        ledamoter_fil: Sökväg till ledamotsfil
        jav_fil: Sökväg till jävsfil
        output_fil: Sökväg för resultat-Excel
        separator: CSV-separator
        
    Returns:
        Dict med statistik om körningen
    """
    # Läs data
    ansokningar = las_ansokningar(ansokningar_fil, separator)
    ledamoter = las_ledamoter(ledamoter_fil, separator)
    jav = las_javsrelationer(jav_fil, separator)
    
    # Kör fördelning
    motor = Fordelningsmotor(ansokningar, ledamoter, jav)
    fordelningar = motor.fordela()
    
    # Exportera
    exportera_till_excel(fordelningar, ledamoter, output_fil)
    
    # Returnera statistik
    osakra = sum(1 for f in fordelningar if f.osakert)
    return {
        'antal_ansokningar': len(ansokningar),
        'antal_ledamoter': len(ledamoter),
        'antal_javsrelationer': sum(len(v) for v in jav.values()),
        'antal_fordelade': len(fordelningar),
        'antal_osakra': osakra,
        'per_grupp': dict(motor.ansokningar_per_grupp),
        'per_ledamot': dict(motor.ansokningar_per_ledamot)
    }


if __name__ == '__main__':
    # Testkörning
    import sys
    
    if len(sys.argv) >= 4:
        resultat = kör_fordelning(
            ansokningar_fil=sys.argv[1],
            ledamoter_fil=sys.argv[2],
            jav_fil=sys.argv[3],
            output_fil=sys.argv[4] if len(sys.argv) > 4 else 'fordelning_resultat.xlsx'
        )
        print(f"Fördelning klar!")
        print(f"  Ansökningar: {resultat['antal_ansokningar']}")
        print(f"  Fördelade: {resultat['antal_fordelade']}")
        print(f"  Osäkra: {resultat['antal_osakra']}")
        print(f"  Per grupp: {resultat['per_grupp']}")
    else:
        print("Användning: python fordelning.py <ansökningar.csv> <ledamöter.csv> <jäv.csv> [output.xlsx]")
