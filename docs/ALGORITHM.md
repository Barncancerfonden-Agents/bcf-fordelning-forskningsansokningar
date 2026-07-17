# Fördelningsalgoritm

Detta dokument beskriver den algoritm som används för att fördela forskningsansökningar till prioriteringsgrupper och ledamöter.

## Grundprinciper

Algoritmen följer en strikt prioritetsordning:

1. **Jäv först** - en jävig person tilldelas i praktiken aldrig som föredragande, ens om det innebär att ansökan flyttas till en annan grupp än den annars naturliga
2. **Minimera jäv** - Välj grupp med färst jäviga ledamöter, och där ordförande inte är jävig
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

Inom vald grupp, försök hitta en kandidat enligt:

```
FÖR varje ledamot i gruppen:
    OM ledamot är ordförande: HOPPA ÖVER
    OM ledamot är jävig mot ansökan: HOPPA ÖVER
    
    Beräkna kompetens_score (0.0 - 1.0)
    Notera antal_tilldelade_ansökningar

SORTERA kandidater EFTER:
    1. antal_tilldelade (stigande - färre är bättre, balans går FÖRE kompetens)
    2. kompetens_score (fallande - högre är bättre, avgör bara vid lika belastning)

VÄLJ första ledamoten i sorterad lista
```

**Viktigt:** balans prioriteras uttryckligen före kompetensmatchning, enligt punkt 4 vs. 5 i prioritetsordningen ovan. En tidig version av implementationen hade det omvänt (kompetens avgjorde, balans var bara en tie-breaker), vilket i praktiken lät en enskild ledamot med breda/generella nyckelord få en oproportionerlig andel av alla ansökningar — upptäckt i skarp drift när en ledamot fick 48 av 147 ansökningar. Ordningen ovan är den korrigerade, driftsatta versionen.

**Om ingen kandidat hittas i den valda gruppen** (alla icke-ordförande i gruppen är jäviga mot ansökan): motorn söker igenom **övriga grupper** efter en jävfri kandidat innan den någonsin tilldelar en jävig person. Det upptäcktes en bugg i skarp drift där en "sista utväg"-fallback ignorerade jäv helt och tilldelade första personen i listan oavsett jävstatus — detta är nu åtgärdat. Se `_valj_ledamot` i `fordelning.py` för den fullständiga logiken, och `_skapa_motivering` för hur motiveringstexten anpassas när ansökan flyttats till en annan grupp av det här skälet.

Bara om **verkligen ingen jävfri ledamot finns någonstans**, i någon grupp, tilldelas en jävig person som absolut sista utväg — och då flaggas ansökan alltid som osäker (se Steg 7).

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

En ansökan markeras som "osäker" i två fall:

1. **Alla tre ordförande är jäviga mot ansökan** (grupp-nivå — avgörs i `_valj_grupp`)
2. **Ingen jävfri, icke-ordförande ledamot kunde hittas i någon grupp** (ledamot-nivå — avgörs i `_valj_ledamot`, absolut sista utväg). Det här är fallet där jäv faktiskt inte gick att undvika, och tilldelningen kräver manuell granskning.

```
OM alla grupper har ordförande_jävig = True:
    Markera ansökan som "OSÄKER PLACERING: Alla ordförande är jäviga."

OM ingen jävfri ledamot finns i någon grupp:
    Markera ansökan som "OSÄKER PLACERING: Jäv kunde inte undvikas."
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
        vald_grupp, osäker, jäviga_i_gruppen = välj_grupp(
            ansökan, 
            ledamöter, 
            jävsrelationer, 
            per_grupp
        )
        
        # Steg 4-5: Välj ledamot. Kan hamna i en ANNAN grupp än vald_grupp
        # om vald_grupp saknar jävfria ledamöter - jäv får aldrig brytas
        # i onödan. tvingad_jav är True bara om ingen jävfri ledamot
        # kunde hittas någonstans alls.
        ledamot, grupp, tvingad_jav = välj_ledamot(
            ansökan, 
            vald_grupp, 
            ledamöter, 
            jävsrelationer, 
            per_ledamot
        )
        osäker = osäker OR tvingad_jav
        
        # Steg 6: Skapa motivering
        motivering = skapa_motivering(
            ansökan, 
            ledamot, 
            grupp, 
            jävsrelationer,
            vald_grupp,
            tvingad_jav
        )
        
        # Uppdatera räknare (på den FAKTISKA gruppen, inte nödvändigtvis vald_grupp)
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

2. **Alla ledamöter jäviga i en grupp**: Motorn söker upp en jävfri ledamot i en annan grupp istället för att bryta jäv. Om verkligen ingen jävfri ledamot finns någonstans tilldelas en jävig person som absolut sista utväg, och ansökan flaggas alltid som osäker i det fallet.

3. **Ingen kompetens-match alls**: Ledamot väljs baserat på arbetsbörda (den med minst)

4. **En hel grupp saknar ledamöter** (inte bara jäviga — bokstavligen inga medlemmar registrerade): motorn kraschar med `IndexError` istället för att hantera fallet. Känd, oåtgärdad begränsning — se `docs/ARCHITECTURE.md` under "Kända begränsningar". Inträffar inte i praktiken så länge alla tre grupper har minst en ledamot registrerad.

## Testfall

Se `test/test_fordelning.py` för enhetstester som verifierar:

- Grundläggande fördelning fungerar
- Ordförande tilldelas aldrig
- Jävsrelationer respekteras
- Gruppbalans uppnås
- Osäkra markeringar skapas korrekt vid ordförandejäv
- **`TestJavBrytsAldrigTyst`** — regressionstester för buggen där en jävig ledamot kunde tilldelas tyst: dels att motorn flyttar till en annan grupp när den ursprungliga är helt uttömd av jäv, dels att ansökan flaggas osäker när ingen jävfri ledamot finns någonstans alls
