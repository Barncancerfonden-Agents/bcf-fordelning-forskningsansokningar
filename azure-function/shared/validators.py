"""
Valideringsfunktioner för indata till fördelningssystemet.

Validerar att indata har korrekt struktur och innehåll innan fördelning körs.
"""

from typing import Any
from dataclasses import dataclass


@dataclass
class ValideringsResultat:
    """Resultat av validering."""
    ok: bool
    fel: list[str]
    varningar: list[str]


def validera_ansokningar(ansokningar: list[dict]) -> ValideringsResultat:
    """
    Validera lista med ansökningar.
    
    Kontrollerar:
    - Att ans_no finns och är unikt
    - Att forskningskategori är giltig
    
    Args:
        ansokningar: Lista med ansökningar som dictionaries
        
    Returns:
        ValideringsResultat med eventuella fel och varningar
    """
    fel = []
    varningar = []
    
    if not ansokningar:
        fel.append("Inga ansökningar angivna")
        return ValideringsResultat(ok=False, fel=fel, varningar=varningar)
    
    ans_no_set = set()
    giltiga_kategorier = {'grundforskning', 'translationell', 'klinisk', ''}
    
    for i, a in enumerate(ansokningar):
        # Kontrollera ans_no
        ans_no = a.get('ans_no', '').strip()
        if not ans_no:
            fel.append(f"Ansökan {i+1}: Saknar ans_no")
        elif ans_no in ans_no_set:
            fel.append(f"Ansökan {i+1}: Duplicerat ans_no '{ans_no}'")
        else:
            ans_no_set.add(ans_no)
        
        # Kontrollera forskningskategori
        fkat = a.get('forskningskategori', '').strip().lower()
        if fkat and fkat not in giltiga_kategorier:
            varningar.append(f"Ansökan {ans_no}: Okänd forskningskategori '{fkat}'")
        
        # Varna om nyckelord saknas
        nyckelord = a.get('nyckelord', [])
        if not nyckelord:
            varningar.append(f"Ansökan {ans_no}: Inga nyckelord angivna")
    
    return ValideringsResultat(
        ok=len(fel) == 0,
        fel=fel,
        varningar=varningar
    )


def validera_ledamoter(ledamoter: list[dict]) -> ValideringsResultat:
    """
    Validera lista med ledamöter.
    
    Kontrollerar:
    - Att initialer finns och är unika
    - Att grupp är giltig (Bio I, Bio II, Bio III)
    - Att det finns minst en ordförande per grupp
    
    Args:
        ledamoter: Lista med ledamöter som dictionaries
        
    Returns:
        ValideringsResultat med eventuella fel och varningar
    """
    fel = []
    varningar = []
    
    if not ledamoter:
        fel.append("Inga ledamöter angivna")
        return ValideringsResultat(ok=False, fel=fel, varningar=varningar)
    
    initialer_set = set()
    giltiga_grupper = {'bio i', 'bio ii', 'bio iii'}
    ordforande_per_grupp = {g: False for g in giltiga_grupper}
    
    for i, l in enumerate(ledamoter):
        # Kontrollera initialer
        initialer = l.get('initialer', '').strip()
        if not initialer:
            fel.append(f"Ledamot {i+1}: Saknar initialer")
        elif initialer in initialer_set:
            fel.append(f"Ledamot {i+1}: Duplicerade initialer '{initialer}'")
        else:
            initialer_set.add(initialer)
        
        # Kontrollera grupp
        grupp = l.get('grupp', '').strip().lower()
        if not grupp:
            fel.append(f"Ledamot {initialer}: Saknar grupp")
        elif grupp not in giltiga_grupper:
            fel.append(f"Ledamot {initialer}: Ogiltig grupp '{grupp}'")
        
        # Kolla ordförande
        roll = l.get('roll', '').strip().lower()
        if roll == 'ordförande' and grupp in ordforande_per_grupp:
            ordforande_per_grupp[grupp] = True
        
        # Varna om kompetens saknas
        fkat = l.get('forskningskategori', '').strip()
        nyckelord = l.get('nyckelord', [])
        if not fkat and not nyckelord:
            varningar.append(f"Ledamot {initialer}: Saknar kompetensinfo (forskningskategori och nyckelord)")
    
    # Kontrollera att alla grupper har ordförande
    for grupp, har_ordf in ordforande_per_grupp.items():
        if not har_ordf:
            varningar.append(f"Grupp '{grupp}' saknar ordförande")
    
    return ValideringsResultat(
        ok=len(fel) == 0,
        fel=fel,
        varningar=varningar
    )


def validera_javsrelationer(javsrelationer: list[dict], 
                            giltiga_initialer: set[str],
                            giltiga_ans_no: set[str]) -> ValideringsResultat:
    """
    Validera lista med jävsrelationer.
    
    Kontrollerar:
    - Att initialer existerar bland ledamöter
    - Att ans_no existerar bland ansökningar
    
    Args:
        javsrelationer: Lista med jävsrelationer som dictionaries
        giltiga_initialer: Set med giltiga ledamotsinitialer
        giltiga_ans_no: Set med giltiga ansökningsnummer
        
    Returns:
        ValideringsResultat med eventuella fel och varningar
    """
    fel = []
    varningar = []
    
    for i, j in enumerate(javsrelationer):
        initialer = j.get('initialer', '').strip()
        ans_no = j.get('ans_no', '').strip()
        
        if not initialer:
            varningar.append(f"Jävsrelation {i+1}: Saknar initialer")
            continue
        if not ans_no:
            varningar.append(f"Jävsrelation {i+1}: Saknar ans_no")
            continue
        
        if initialer not in giltiga_initialer:
            varningar.append(f"Jävsrelation {i+1}: Okänd ledamot '{initialer}'")
        
        if ans_no not in giltiga_ans_no:
            varningar.append(f"Jävsrelation {i+1}: Okänt ansökningsnummer '{ans_no}'")
    
    return ValideringsResultat(
        ok=len(fel) == 0,
        fel=fel,
        varningar=varningar
    )


def validera_all_indata(ansokningar: list[dict], 
                        ledamoter: list[dict],
                        javsrelationer: list[dict]) -> ValideringsResultat:
    """
    Validera all indata samtidigt.
    
    Args:
        ansokningar: Lista med ansökningar
        ledamoter: Lista med ledamöter
        javsrelationer: Lista med jävsrelationer
        
    Returns:
        Kombinerat ValideringsResultat
    """
    alla_fel = []
    alla_varningar = []
    
    # Validera ansökningar
    res_ans = validera_ansokningar(ansokningar)
    alla_fel.extend(res_ans.fel)
    alla_varningar.extend(res_ans.varningar)
    
    # Validera ledamöter
    res_led = validera_ledamoter(ledamoter)
    alla_fel.extend(res_led.fel)
    alla_varningar.extend(res_led.varningar)
    
    # Extrahera giltiga värden för jävsvalidering
    giltiga_initialer = {l.get('initialer', '').strip() for l in ledamoter}
    giltiga_ans_no = {a.get('ans_no', '').strip() for a in ansokningar}
    
    # Validera jävsrelationer
    res_jav = validera_javsrelationer(javsrelationer, giltiga_initialer, giltiga_ans_no)
    alla_fel.extend(res_jav.fel)
    alla_varningar.extend(res_jav.varningar)
    
    return ValideringsResultat(
        ok=len(alla_fel) == 0,
        fel=alla_fel,
        varningar=alla_varningar
    )
