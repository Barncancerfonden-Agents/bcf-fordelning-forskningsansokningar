# Användarguide - Fördelning av forskningsansökningar

Den här guiden beskriver hur forskningsavdelningen kör fördelningen av forskningsansökningar. Ingen teknisk bakgrund krävs.

## Vad gör systemet?

Systemet läser tre Excel-filer (ansökningar, ledamöter, jävsrelationer) och fördelar automatiskt varje ansökan till:

- En **prioriteringsgrupp** (Bio I, Bio II eller Bio III)
- En **föredragande ledamot** som ska granska ansökan

Fördelningen tar hänsyn till jäv (viktigast — en jävig person tilldelas aldrig), balanserar arbetsbelastningen mellan grupper och ledamöter, och matchar kompetens där det går.

## Steg 1: Förbered de tre Excel-filerna

Filerna måste heta exakt **Ansökningar.xlsx**, **Ledamöter.xlsx** och **Jäv.xlsx**, och varje flik måste vara formaterad som en riktig Excel-**tabell** (Infoga → Tabell), inte bara rådata.

### Ansökningar.xlsx

| Kolumn | Krävs | Beskrivning |
|--------|-------|-------------|
| Ans no | Ja | Unikt ansökningsnummer, t.ex. KP2024-0001 |
| Sökande | Ja | Sökandens namn |
| F.kat | Ja | Forskningskategori |
| Område | Ja | Forskningsområde |
| Diagnos | Ja | Cancerdiagnos ansökan gäller |
| Nyckelord | Ja | Kommaseparerade nyckelord, t.ex. "immunterapi, t-celler" |

*Övriga kolumner (t.ex. Projekttitel, Kat, Diagn. und.nivå) får finnas kvar men används inte av fördelningen idag.*

### Ledamöter.xlsx

| Kolumn | Krävs | Beskrivning |
|--------|-------|-------------|
| Namn | Ja | Ledamotens fullständiga namn |
| Initialer | Ja | Unika initialer, t.ex. GB — måste matcha exakt de initialer som används i Jäv.xlsx |
| Grupp | Ja | Bio I, Bio II eller Bio III |
| Ordförande | Ja | Skriv exakt texten "Ordförande" på de rader som är ordförande, lämna tomt för övriga |
| Forskningskategori | Ja | Ledamotens kompetensområde |
| Nyckelord | Ja | Kommaseparerade kompetensord |

**Varje grupp (Bio I/II/III) måste ha exakt en ordförande.** Ordförande tilldelas aldrig ansökningar som föredragande.

### Jäv.xlsx

| Kolumn | Krävs | Beskrivning |
|--------|-------|-------------|
| Ans no | Ja | Ansökningsnummer |
| Jäv | Ja | Initialer på alla jäviga ledamöter för just den ansökan, kommaseparerade, t.ex. "GB, KN, LP" |

En rad per ansökan (inte en rad per jävig person) — lista alla jäviga initialer i samma cell.

## Steg 2: Ladda upp filerna

1. Öppna [Input-mappen](https://bcfintranet.sharepoint.com/sites/Forskning_utveckling_stod/Forskning%20och%20utbildning/Forms/AllItems.aspx?id=%2Fsites%2FForskning%5Futveckling%5Fstod%2FForskning%20och%20utbildning%2FFORSKNING%2FPK%2Dagenten%20F%C3%B6redragande%2FF%C3%B6rdelning%20ans%C3%B6kningar%2FInput&viewid=3ee8afc5%2Deb0d%2D4566%2D9f82%2Df60d7ffe63f0)
2. Ladda upp de tre filerna — skriv över eventuella tidigare versioner med samma filnamn

## Steg 3: Starta fördelningen

1. Gå till [sidan "Fördelning av forskningsansökningar"](https://bcfintranet.sharepoint.com/sites/Forskning_utveckling_stod/SitePages/F%C3%B6rdelning-av-forskningsans%C3%B6kningar.aspx)
2. Klicka på knappen **Starta fördelning**
3. Vänta — det tar cirka **5-10 minuter**
4. Du får ett **meddelande i Teams** när fördelningen är klar (eller om något gick fel)

## Steg 4: Hämta resultatet

Resultatet läggs i [Output-mappen](https://bcfintranet.sharepoint.com/sites/Forskning_utveckling_stod/Forskning%20och%20utbildning/Forms/AllItems.aspx?id=%2Fsites%2FForskning%5Futveckling%5Fstod%2FForskning%20och%20utbildning%2FFORSKNING%2FPK%2Dagenten%20F%C3%B6redragande%2FF%C3%B6rdelning%20ans%C3%B6kningar%2FOutput&viewid=3ee8afc5%2Deb0d%2D4566%2D9f82%2Df60d7ffe63f0) som en ny fil, namngiven efter dagens datum (t.ex. `Fordelning_2026-07-17.xlsx`). Varje körning skapar en ny fil — gamla resultat skrivs aldrig över.

Filen innehåller en tabell med följande kolumner:

| Kolumn | Beskrivning |
|--------|-------------|
| Ans no | Ansökningsnummer |
| Huvudsökande | Sökandens namn |
| Grupp | Tilldelad prioriteringsgrupp |
| Föredragande | Ledamotens namn |
| Initialer | Ledamotens initialer |
| Motivering | Förklaring till varför just den här grupp/ledamot valdes |
| Osäker | SANT om fördelningen behöver granskas manuellt, annars FALSKT |

## Steg 5: Granska osäkra rader

Sortera/filtrera på kolumnen **Osäker**. En rad markeras SANT bara i mycket ovanliga fall:

- Alla tre ordförande är jäviga mot ansökan, **eller**
- Ingen jävfri ledamot alls kunde hittas, i någon grupp, för den ansökan (extremt sällsynt — kräver att nästan alla ledamöter är jäviga samtidigt)

Läs motiveringstexten för dessa rader och gör en manuell bedömning. Resultatfilen är en vanlig Excel-fil — det går bra att ändra grupp eller föredragande direkt i den om ni behöver justera något, oavsett om raden är markerad osäker eller inte.

## Vanliga frågor

**Varför hamnade ansökan X hos ledamot Y?**
Läs motiveringen i resultatfilen — den förklarar kompetensmatchning, jäv och balansering för just den raden.

**Kan jag köra fördelningen flera gånger?**
Ja. Varje körning skapar en ny resultatfil (med dagens datum) i Output-mappen — tidigare resultat påverkas inte. Vanligt arbetssätt: kör en första gång, granska, justera indatafilerna (t.ex. lägg till en jävsrelation som saknades) och kör igen.

**Vad gör jag om två körningar samma dag krockar (samma filnamn)?**
Filen skrivs över om du kör flera gånger samma dag. Ladda ner/döp om den föregående filen manuellt innan du kör igen om du vill spara båda.

## Felsökning

**Inget Teams-meddelande kommer, eller ett felmeddelande kommer**
Kontrollera att alla tre filerna finns i Input-mappen, att de heter exakt rätt, och att kolumnrubrikerna stämmer (stor/liten bokstav och mellanslag spelar roll). Kontakta teknisk support (se nedan) om filerna ser korrekta ut men det ändå felar.

**En ledamot fick inga ansökningar alls**
Troliga orsaker: ledamoten är ordförande (tilldelas aldrig), eller är jävig mot väldigt många ansökningar.

**Fördelningen verkar ojämn**
Systemet strävar efter jämn arbetsbelastning per ledamot, men jäv går alltid först — om en ledamot har väldigt många jävsrelationer kan den ledamoten få färre ansökningar än andra.

## Kontakt

- **Tekniska problem** (fel i knappen, Azure, Power Automate): Tech Sisters AB
- **Frågor om fördelningsregler eller resultat:** internt inom forskningsavdelningen
