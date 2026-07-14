# Användarguide - Fördelning av forskningsansökningar

Denna guide beskriver hur forskningsavdelningen använder systemet för att fördela forskningsansökningar till prioriteringsgrupper och ledamöter.

## Översikt

Systemet tar tre Excel-filer som indata och producerar en fördelningslista där varje ansökan har tilldelats:
- En **prioriteringsgrupp** (Bio I, Bio II eller Bio III)
- En **föredragande ledamot** som ska granska ansökan

Fördelningen tar hänsyn till jävsrelationer, ledamöternas kompetenser och ser till att arbetsbelastningen blir jämnt fördelad.

## Steg-för-steg

### 1. Förbered indatafiler

Exportera tre filer från ert interna system:

#### Ansökningar.xlsx

| Kolumn | Beskrivning | Exempel |
|--------|-------------|---------|
| Ans no | Unikt ansökningsnummer | KP2024-0001 |
| Huvudsökande | Forskarens namn | Anna Andersson |
| F.kat | Forskningskategori | Grundforskning |
| Område | Forskningsområde | Cancerbiologi |
| Diagnos | Cancerdiagnos | Leukemi |
| Nyckelord | Kommaseparerade nyckelord | immunterapi, t-celler, car-t |

#### Ledamöter.xlsx

| Kolumn | Beskrivning | Exempel |
|--------|-------------|---------|
| Förnamn | Ledamotens förnamn | Gisela |
| Efternamn | Ledamotens efternamn | Barbany |
| Initialer | Unika initialer | GB |
| Prioriteringsgrupp | Bio I, Bio II eller Bio III | Bio I |
| Roll | Ordförande eller Ledamot | Ordförande |
| Forskningskategori | Kompetensområde | Grundforskning |
| Nyckelord | Kompetenser | genetik, leukemi, diagnostik |

#### Jäv.xlsx

| Kolumn | Beskrivning | Exempel |
|--------|-------------|---------|
| Ledamot | Ledamotens initialer | GB |
| Ans no | Ansökningsnummer | KP2024-0001 |

### 2. Ladda upp filer

1. Gå till SharePoint-sidan för fördelning
2. Navigera till mappen **Indata**
3. Ladda upp de tre filerna (ersätt eventuellt befintliga)

### 3. Kör fördelning

1. Gå till cockpit-sidan
2. Kontrollera att rätt filer visas under "Indatafiler"
3. Klicka på knappen **Kör fördelning**
4. Vänta medan systemet arbetar (ca 10-30 sekunder)
5. En bekräftelse visas när fördelningen är klar

### 4. Granska resultat

Resultatfilen skapas automatiskt i mappen **Resultat** och innehåller tre flikar:

#### Flik 1: Fördelning

Huvudresultatet med alla ansökningar:

| Kolumn | Beskrivning |
|--------|-------------|
| Ans no | Ansökningsnummer |
| Huvudsökande | Forskarens namn |
| Grupp | Tilldelad prioriteringsgrupp |
| Föredragande | Ledamotens namn |
| Initialer | Ledamotens initialer |
| Motivering | Förklaring till fördelningen |
| Osäker | "JA" om fördelningen behöver granskas manuellt |

#### Flik 2: Statistik

Sammanställning som visar:
- Antal ansökningar per grupp
- Antal ansökningar per ledamot

#### Flik 3: Ledamöter per grupp

Översikt över alla ledamöter och deras kompetenser.

### 5. Hantera osäkra fördelningar

Vissa ansökningar kan markeras som "Osäker placering". Detta händer när:
- Alla tre ordförande är jäviga mot ansökan
- Det inte finns någon icke-jävig ledamot med relevant kompetens

Dessa ansökningar kräver manuellt beslut:
1. Filtrera Excel-filen på kolumnen "Osäker" = "JA"
2. Granska motiveringen för varje osäker ansökan
3. Gör manuell justering vid behov

## Vanliga frågor

### Varför hamnade ansökan X i grupp Y?

Läs motiveringen i resultatfilen. Den förklarar:
- Vilken kompetens-match som fanns
- Var jäv förekom
- Varför just denna grupp valdes

### Kan jag ändra en fördelning manuellt?

Ja, resultatfilen är en vanlig Excel-fil. Du kan ändra grupp eller föredragande manuellt efter behov.

### Vad händer om jag kör fördelningen igen?

En ny resultatfil skapas. Den gamla filen finns kvar i SharePoint-historiken.

### Hur ofta kan jag köra fördelningen?

Så ofta du vill. Det är vanligt att:
1. Köra en första fördelning
2. Granska resultatet
3. Justera indatafilerna vid behov (t.ex. lägga till jävsrelationer)
4. Köra igen tills resultatet är tillfredsställande

## Felsökning

### "Fördelningen misslyckades"

Kontrollera att:
- Alla tre filer finns i Indata-mappen
- Filerna har korrekt format (se ovan)
- Kolumnnamnen stämmer exakt

### "Inga ansökningar fördelade"

Kontrollera att:
- Ansökningsfilen innehåller data
- Kolumnen "Ans no" finns och innehåller värden

### "Ledamot X fick ingen ansökan"

Detta kan bero på:
- Ledamoten är ordförande (ordförande tilldelas aldrig ansökningar)
- Ledamoten är jävig mot alla ansökningar
- Ledamotens kompetens matchar inte någon ansökan

## Kontakt

Vid tekniska problem, kontakta:
- **Tech Sisters AB** - [kontakt@techsisters.se]

Vid frågor om fördelningsregler, kontakta:
- **Forskningsavdelningen** - [internt]
