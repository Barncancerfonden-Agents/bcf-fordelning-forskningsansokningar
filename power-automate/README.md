# Power Automate - Fördelningsflödet

Beskriver det faktiskt driftsatta Power Automate-flödet. Se `docs/ARCHITECTURE.md` för helhetsbilden — det här dokumentet går djupare på själva flödet.

## Grunduppgifter

- **Namn:** Fördelning forskningsansökningar (jävagent)
- **Miljö:** Sandbox Dev (medvetet val, inte standardmiljön "Default")
- **Trigger:** `Manually trigger a flow` (inget indatafält krävs)
- **Startas av:** en Button-webbdel på SharePoint-cockpiten (se `sharepoint/README.md`), inte via Power Automate-portalen eller en HTTP-URL

## Varför "Manually trigger a flow" och inte en HTTP-trigger

Ursprunglig plan var en `When an HTTP request is received`-trigger med en vanlig länk-knapp på SharePoint. Det byttes till `Manually trigger a flow` eftersom SharePoints moderna Button-webbdel har en inbyggd åtgärd "Kör Power Automate-flöde" som är byggd specifikt för den triggertypen — enklare för slutanvändaren (inget att bygga eller underhålla en offentlig URL för) och inget behov av att exponera en anropbar endpoint alls.

**Viktig fallgrop:** Button-webbdelen letar bara i standardmiljön (Default) om man bara anger flödets vanliga GUID (den som syns i webbadressen när flödet är öppet). Eftersom det här flödet ligger i Sandbox Dev måste man istället använda flödets **detaljerade identifierare**:

1. Öppna flödet i [make.powerautomate.com](https://make.powerautomate.com)
2. **Export** → **Get flow identifier**
3. Kopiera hela strängen (format `v1/{miljö-id}-{flödes-id}...`)
4. Klistra in den — inte den korta GUID:en — i knappens `Flödes-ID`-fält

## Flödesstruktur

```
Manually trigger a flow
  │
  ├─ Läs_Ansökningar   (List rows present in a table, Input/Ansökningar.xlsx)
  ├─ Läs_Ledamöter     (List rows present in a table, Input/Ledamöter.xlsx)
  ├─ Läs_Jäv           (List rows present in a table, Input/Jäv.xlsx)
  │
  ├─ Mappa_Ansökningar (Select)
  ├─ Mappa_Ledamöter   (Select)
  ├─ Mappa_Jäv         (Select)
  │
  ├─ Bygg Request      (Compose - bygger JSON-body)
  ├─ Anropa Fordelning (HTTP POST till Azure Function)
  │
  └─ Condition: success == true?
       │
       ├─ True:
       │    ├─ Bygg_Filnamn       (Compose - Fordelning_<datum>.xlsx)
       │    ├─ Läs_Mall           (Get file content, Output/Mall_Fordelning.xlsx)
       │    ├─ Skapa_Resultatfil  (Create file i Output/, namn+innehåll från ovan)
       │    ├─ Apply_to_each      (över fordelningar-arrayen i svaret)
       │    │    └─ Add_a_row_into_a_table (skriver varje rad till den nya filen)
       │    └─ Post message i Teams (lyckad körning)
       │
       └─ False:
            ├─ Post message i Teams (felmeddelande)
            └─ Terminate (Failed)
```

## Steg 1: Läs Excel-filerna

Tre `List rows present in a table`-åtgärder (Excel Online Business), en per fil i Input-mappen.

**Viktigt:** filen väljs via **mapp-ikonen** (bläddra fram filen), inte via dynamiskt innehåll från en föregående `Get file content`. `List rows present in a table` behöver en filreferens den kan fråga om tabellmetadata — matar man in rått filinnehåll (bytes) kan Table-dropdownen inte fyllas i alls.

## Steg 2: Mappa om kolumnnamn

Excel-tabellernas riktiga kolumnrubriker matchar inte de fältnamn Azure Function förväntar sig. Tre `Select`-åtgärder gör om mappningen:

**Mappa_Ansökningar** (from: `value` från Läs_Ansökningar):

| Key | Value (expression) |
|---|---|
| ans_no | `item()?['Ans no']` |
| huvudsokande | `item()?['Sökande']` |
| forskningskategori | `item()?['F.kat']` |
| omrade | `item()?['Område']` |
| diagnos | `item()?['Diagnos']` |
| nyckelord | `split(item()?['Nyckelord'], ',')` |

**Mappa_Ledamöter** (from: `value` från Läs_Ledamöter):

| Key | Value (expression) |
|---|---|
| namn | `item()?['Namn']` |
| initialer | `item()?['Initialer']` |
| grupp | `item()?['Grupp']` |
| roll | `if(equals(item()?['Ordförande'], 'Ordförande'), 'Ordförande', 'Ledamot')` |
| forskningskategori | `item()?['Forskningskategori']` |
| nyckelord | `split(item()?['Nyckelord'], ',')` |

**Mappa_Jäv** (from: `value` från Läs_Jäv):

| Key | Value (expression) |
|---|---|
| ans_no | `item()?['Ans no']` |
| initialer_lista | `split(item()?['Jäv'], ',')` |

Jäv-tabellen har en rad per ansökan med flera initialer i en och samma cell (`initialer_lista`), inte en rad per (ledamot, ansökan)-par — matcha alltid mot vad Azure Function faktiskt förväntar sig, se `docs/ARCHITECTURE.md`.

**Kritiskt för att undvika trasiga Select-steg:** varje värde måste läggas in via **uttrycksredigeraren** (klicka i fältet → fx/blixt-ikonen → fliken Expression), inte skrivas eller klistras in direkt i den lilla rutan. Skriver man direkt blir värdet bokstavlig text (fungerar inte) snarare än ett evaluerat uttryck. Kontrollera i **Code view** att varje värde i `select`-objektet börjar med `@` (t.ex. `"ans_no": "@item()?['Ans no']"`) — annars är det fel.

## Steg 3: Bygg request och anropa Azure Function

**Bygg Request** (Compose):
```json
{
  "ansokningar": @{body('Mappa_Ansökningar')},
  "ledamoter": @{body('Mappa_Ledamöter')},
  "javsrelationer": @{body('Mappa_Jäv')}
}
```

**Anropa Fordelning** (vanlig grön **HTTP**-åtgärd, inte "HTTP with Microsoft Entra ID" — funktionen använder function-key-autentisering, inte Azure AD):

- Method: POST
- URI: `https://bcf-fordelning-dev.azurewebsites.net/api/fordela`
- Headers: `Content-Type: application/json`, `x-functions-key: <function key>` (hämta i Azure Portal, se `docs/ARCHITECTURE.md` — använd alltid den vanliga function-nyckeln, aldrig master-nyckeln)
- Body: `@{outputs('Bygg_Request')}`

## Steg 4: Hantera resultatet

**Condition:** `@equals(body('Anropa_Fordelning')?['success'], true)` — jämför specifikt `success`-fältet inuti svaret, inte hela svarsobjektet (ett vanligt misstag som alltid ger `false`).

**Vid fel (False-grenen):** Teams-notis med felmeddelandet från `body('Anropa_Fordelning')?['error']`, sedan `Terminate` med status Failed.

**Vid lyckad körning (True-grenen):**

1. `Bygg_Filnamn` (Compose): `Fordelning_@{formatDateTime(utcNow(), 'yyyy-MM-dd')}.xlsx` — ger en ny fil per körning istället för att skriva över föregående resultat.
2. `Läs_Mall` (Get file content): läser mallfilen `Output/Mall_Fordelning.xlsx` (tom tabell med rätt kolumner), vald via mapp-ikonen (statisk, känd fil).
3. `Skapa_Resultatfil` (Create file): skriver en ny fil i Output-mappen med namnet från steg 1 och innehållet från steg 2.
4. `Apply_to_each` över `outputs('Anropa_Fordelning')?['body']?['fordelningar']` → `Add a row into a table`:
   - **File:** refereras **dynamiskt** via blixt-ikonen → `Id` från `Skapa_Resultatfil` (inte mapp-ikonen — filen finns inte vid designtillfället eftersom namnet byggs vid körning)
   - **Table:** eftersom filen är dynamisk kan tabellnamnet inte väljas ur dropdown — skriv det manuellt via "Enter custom value" (t.ex. `FordelningTabell`)
   - **Row:** eftersom tabellschemat inte kan läsas av för en dynamisk fil visas inget separat fält per kolumn — skriv istället hela raden som JSON direkt i Row-fältet:
     ```
     {
       "Ans no": "@{item()?['ans_no']}",
       "Huvudsökande": "@{item()?['huvudsokande']}",
       "Grupp": "@{item()?['grupp']}",
       "Föredragande": "@{item()?['ledamot_namn']}",
       "Initialer": "@{item()?['ledamot_initialer']}",
       "Motivering": "@{item()?['motivering']}",
       "Osäker": @{item()?['osakert']}
     }
     ```
     Nycklarna måste matcha resultattabellens kolumnrubriker exakt. `Osäker` är boolean och ska **inte** ha citattecken runt uttrycket, till skillnad från textfälten.
5. Teams-notis med sammanfattning, t.ex. antal fördelade och antal osäkra (`body('Anropa_Fordelning')?['body']?['statistik']`).

## Testning

1. Ladda upp testfiler (`test/testdata/*.csv` konverterat till `.xlsx`, eller riktiga filer) till Input-mappen
2. Kör flödet manuellt (via Power Automate-portalen under utveckling, eller via SharePoint-knappen i skarp drift)
3. Kontrollera varje stegs körresultat i körhistoriken
4. Verifiera att en ny fil dyker upp i Output-mappen och att raderna stämmer, särskilt att inga jäviga personer tilldelats

## Felsökning

**"Invalid parameters" / "Enter a valid JSON" på ett Select-steg**
Något fält skrevs in direkt istället för via uttrycksredigeraren. Öppna Code view, leta efter värden som saknar `@`-prefix eller saknar omgivande citattecken, och gör om just det fältet via fx-ikonen.

**Table-dropdown fylls inte i vid List rows present in a table**
Filen kopplad via dynamiskt innehåll istället för mapp-ikonen. Byt till att bläddra fram filen manuellt.

**"File not found" på ett Get file content-steg**
Filreferensen är troligen dubbelkodad (kolla om `id`-parametern i Code view innehåller `%25` — det betyder att sökvägen URL-kodats två gånger). Rensa fältet och bläddra fram filen på nytt istället för att återanvända en kopierad referens.

**HTTP 500 från Anropa Fordelning**
Kolla `body('Anropa_Fordelning')?['error']` i körresultatet — Azure Function skickar alltid ett beskrivande felmeddelande. Vanligaste orsaken hittills: fel nycklar i en Select-mappning (t.ex. `initialer` istället för `initialer_lista`) gör att data som `javsrelationer` tystnar helt (`antal_javsrelationer: 0` i statistiken avslöjar det).

**"Kunde inte hitta flödet" när SharePoint-knappen klickas**
Antingen saknar användaren behörighet att köra flödet (Share → Run only i Power Automate), eller så används den korta flödes-GUID:en istället för den detaljerade identifieraren (`Export → Get flow identifier`) — se avsnittet ovan om varför det krävs när flödet ligger utanför standardmiljön.

**Osäker/success-fält visar fel värde trots att anropet lyckades**
Kontrollera att Condition jämför `body('Anropa_Fordelning')?['success']` specifikt, inte hela `body('Anropa_Fordelning')`.
