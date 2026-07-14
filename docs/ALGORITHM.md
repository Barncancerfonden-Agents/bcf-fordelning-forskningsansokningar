# Fördelningsalgoritm

Detta dokument beskriver den algoritm som används för att fördela forskningsansökningar till prioriteringsgrupper och ledamöter.

## Grundprinciper

Algoritmen följer en strikt prioritetsordning:

1. **Jäv först** - Ordförande i tilldelad grupp får ALDRIG vara jävig
2. **Minimera jäv** - Välj grupp med färst jäviga ledamöter
3. **Gruppbalans** - Fördela ungefär lika många ansökningar per grupp
4. **Ledamotsbalans** - Fördela ungefär lika många ansökningar per ledamot
5. **Kompetensmatching** - Matcha forskningskategori och nyckelord
6. **Flagga osäkra** - Markera ansökningar som kräver manuell granskning

## Algoritm i detalj

### Steg 1: Förberedelse

```
FÖR varje ansökan:
    Skapa lista med kandidatgrupper (Bio I, Bio II, Bio III)
```

### Steg 2: Filtrera på ordförandejäv

```
FÖR varje kandidatgrupp:
    OM ordförande i gruppen är jävig mot ansökan:
        Markera gruppen som "ordförande jävig"
```

### Steg 3: Ranka grupper

Grupperna rankas efter följande kriterier (i prioritetsordning):

| Prioritet | Kriterium | Bättre värde |
|-----------|-----------|--------------|
| 1 | Ordförande jävig | Nej |
| 2 | Antal jäviga ledamöter | Färre |
| 3 | Antal tilldelade ansökningar | Färre |

```
SORTERA kandidatgrupper EFTER:
    1. ordförande_jävig (False < True)
    2. antal_jäviga (stigande)
    3. antal_tilldelade (stigande)

VÄLJ första gruppen i sorterad lista
```

### Steg 4: Välj ledamot

Inom vald grupp, välj ledamot enligt:

```
FÖR varje ledamot i gruppen:
    OM ledamot är ordförande: HOPPA ÖVER
    OM ledamot är jävig mot ansökan: HOPPA ÖVER
    
    Beräkna kompetens_score (0.0 - 1.0)
    Notera antal_tilldelade_ansökningar

SORTERA kandidater EFTER:
    1. kompetens_score (fallande - högre är bättre)
    2. antal_tilldelade (stigande - färre är bättre)

VÄLJ första ledamoten i sorterad lista
```

### Steg 5: Beräkna kompetens-score

```
score = 0.0

# Forskningskategori-match (60% vikt)
OM ledamotens forskningskategori matchar ansökans:
    score += 0.6

# Nyckelords-match (40% vikt)
överlapp = (ledamotens nyckelord) ∩ (ansökans nyckelord)
OM överlapp finns:
    match_ratio = antal_överlapp / antal_ansökans_nyckelord
    score += 0.4 * match_ratio

# Bonus för partiell matchning
FÖR varje par (ansökans_nyckelord, ledamotens_nyckelord):
    OM ena innehåller den andra:
        score += 0.05

RETURNERA min(score, 1.0)
```

### Steg 6: Skapa motivering

Motiveringen byggs upp av:

1. Beskrivning av ansökan (diagnos/område/nyckelord)
2. Ledamotens relevanta kompetens
3. Var jäv förekom (i andra grupper)
4. Information om jäv i vald grupp
5. Balanseringsaspekt
6. Osäkerhetsmarkering (om relevant)

### Steg 7: Markera osäkra

En ansökan markeras som "osäker" om:
- Alla tre ordförande är jäviga mot ansökan

```
OM alla grupper har ordförande_jävig = True:
    Markera ansökan som "OSÄKER PLACERING"
```

## Pseudokod - Komplett

```python
def fördela(ansökningar, ledamöter, jävsrelationer):
    resultat = []
    
    # Räknare för balansering
    per_grupp = {grupp: 0 for grupp in GRUPPER}
    per_ledamot = {l.initialer: 0 for l in ledamöter}
    
    # Sortera för konsekvent resultat
    ansökningar = sortera(ansökningar, nyckel=ans_no)
    
    for ansökan in ansökningar:
        # Steg 1-3: Välj grupp
        grupp, osäker = välj_grupp(
            ansökan, 
            ledamöter, 
            jävsrelationer, 
            per_grupp
        )
        
        # Steg 4-5: Välj ledamot
        ledamot = välj_ledamot(
            ansökan, 
            grupp, 
            ledamöter, 
            jävsrelationer, 
            per_ledamot
        )
        
        # Steg 6: Skapa motivering
        motivering = skapa_motivering(
            ansökan, 
            ledamot, 
            grupp, 
            jävsrelationer
        )
        
        # Uppdatera räknare
        per_grupp[grupp] += 1
        per_ledamot[ledamot.initialer] += 1
        
        # Spara resultat
        resultat.append(Fördelning(
            ans_no=ansökan.ans_no,
            grupp=grupp,
            ledamot=ledamot,
            motivering=motivering,
            osäker=osäker
        ))
    
    return resultat
```

## Komplexitet

| Operation | Tidskomplexitet |
|-----------|-----------------|
| Välj grupp | O(G) där G = antal grupper (3) |
| Välj ledamot | O(L) där L = ledamöter per grupp (~10) |
| Total fördelning | O(A × G × L) där A = antal ansökningar |

Med typiska värden (150 ansökningar, 3 grupper, 10 ledamöter/grupp):
- Antal operationer: ~4500
- Körtid: < 1 sekund

## Begränsningar

### Algoritmen hanterar INTE

- Flera föredragande per ansökan (endast en tilldelas)
- Viktat jäv (alla jävsrelationer behandlas lika)
- Tidsbaserade preferenser (t.ex. ledamot på semester)
- Manuella önskemål från ledamöter

### Kända edge cases

1. **Alla ordförande jäviga**: Ansökan markeras som osäker, placeras i grupp med minst totalt jäv

2. **Alla ledamöter jäviga i en grupp**: Väljer annan grupp om möjligt, annars tar första icke-ordförande

3. **Ingen kompetens-match alls**: Ledamot väljs baserat på arbetsbörda (den med minst)

## Testfall

Se `test/test_fordelning.py` för enhetstester som verifierar:

- Grundläggande fördelning fungerar
- Ordförande tilldelas aldrig
- Jävsrelationer respekteras
- Gruppbalans uppnås
- Ledamotsbalans uppnås
- Osäkra markeringar skapas korrekt
