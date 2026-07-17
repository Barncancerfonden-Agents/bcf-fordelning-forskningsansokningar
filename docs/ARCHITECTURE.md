# Arkitektur (teknisk dokumentation)

Detta dokument beskriver den faktiska, driftsatta lösningen — inte en plan. Skrivet för utvecklare, IT-drift eller en framtida leverantör som ska underhålla eller vidareutveckla systemet.

## Översikt

Lösningen består av tre komponenter:

1. **SharePoint** — lagrar indata- och resultatfiler, är startpunkten via en knapp på en sida
2. **Power Automate** — läser Excel-filer, anropar Azure Function, skriver resultat, notifierar i Teams
3. **Azure Function** — kör själva fördelningsalgoritmen (ren beräkning, ingen lagring)

```
┌──────────────────────────────────────────────────────────────────────┐
│  FORSKNINGSAVDELNINGEN                                                │
│  1. Laddar upp tre Excel-filer till Input-mappen                      │
│  2. Klickar knappen "Starta fördelning" på SharePoint-sidan            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│  SHAREPOINT                                                           │
│  Site: Forskning, utveckling & stöd                                   │
│  Bibliotek: Forskning och utbildning                                  │
│  Mapp: FORSKNING/PK-agenten Föredragande/Fördelning ansökningar/      │
│    ├─ Input/   (Ansökningar.xlsx, Ledamöter.xlsx, Jäv.xlsx)           │
│    └─ Output/  (Mall_Fordelning.xlsx + genererade resultatfiler)      │
│  Sida: Fördelning-av-forskningsansökningar.aspx (knapp)               │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼  (Button-webbdel, "Kör Power Automate-flöde")
┌──────────────────────────────────────────────────────────────────────┐
│  POWER AUTOMATE  (miljö: Sandbox Dev)                                 │
│  Flöde: "Fördelning forskningsansökningar (jävagent)"                 │
│  Trigger: Manually trigger a flow                                     │
│                                                                        │
│  Läs_Ansökningar ─┐                                                   │
│  Läs_Ledamöter   ─┼─▶ Mappa_* (Select) ─▶ Bygg Request (Compose)      │
│  Läs_Jäv         ─┘                            │                      │
│                                                 ▼                      │
│                                     Anropa Fordelning (HTTP → Azure)   │
│                                                 │                      │
│                                    Condition: success == true?         │
│                                 ┌───────────────┴───────────────┐      │
│                               True                            False    │
│  Bygg_Filnamn → Läs_Mall → Skapa_Resultatfil →              Terminate  │
│  Apply_to_each → Add_a_row_into_a_table                    (Failed)   │
│                                                 │                      │
│                                     Post message i Teams               │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼  HTTPS POST /api/fordela (function key)
┌──────────────────────────────────────────────────────────────────────┐
│  AZURE FUNCTION  bcf-fordelning-dev.azurewebsites.net                 │
│  (Resursgrupp rg-bcf-fordelning-dev, Sweden Central)                  │
│                                                                        │
│  FordelaAnsokningar/__init__.py  — HTTP-endpoint, JSON in/ut          │
│  shared/fordelning.py            — Fördelningsmotor (all logik)       │
│  shared/validators.py            — Valfri indatavalidering             │
│                                                                        │
│  Ingen data lagras. Allt processas i minnet och returneras direkt.    │
└──────────────────────────────────────────────────────────────────────┘
```

## Komponentbeskrivning

### Azure Function

**Teknologi:** Python 3.11, Azure Functions v4, Linux Consumption-plan.

**Resurser (endast dev-miljö finns, ingen prod ännu):**

| Resurs | Namn | Typ |
|--------|------|-----|
| Resursgrupp | `rg-bcf-fordelning-dev` | Sweden Central |
| Storage account | `stbcffordelningdev` | Standard_LRS |
| Function App | `bcf-fordelning-dev` | Linux, Consumption (Y1) |
| Application Insights | `bcf-fordelning-dev-ai` | Kopplad via `APPLICATIONINSIGHTS_CONNECTION_STRING` |

**Endpoint:** `POST https://bcf-fordelning-dev.azurewebsites.net/api/fordela`
Autentisering: function key i header `x-functions-key` (hämtas i Azure Portal under Function App → Functions → FordelaAnsokningar → Function Keys → `default`). Använd aldrig master-nyckeln här — den ger adminåtkomst till hela Function App.

**Request-format:**
```json
{
  "ansokningar": [
    {"ans_no": "KP2024-0001", "huvudsokande": "...", "forskningskategori": "...",
     "omrade": "...", "diagnos": "...", "nyckelord": ["...", "..."]}
  ],
  "ledamoter": [
    {"namn": "...", "initialer": "AA", "grupp": "Bio I", "roll": "Ordförande|Ledamot",
     "forskningskategori": "...", "nyckelord": ["...", "..."]}
  ],
  "javsrelationer": [
    {"ans_no": "KP2024-0001", "initialer_lista": ["AA", "BB"]}
  ]
}
```
Notera: `javsrelationer` är en post **per ansökan** med en lista av jäviga initialer, inte en post per (ledamot, ansökan)-par — det matchar hur den verkliga Jäv-tabellen i SharePoint ser ut (en rad per ansökan, flera initialer i samma cell).

**Response-format:**
```json
{
  "success": true,
  "fordelningar": [
    {"ans_no": "...", "huvudsokande": "...", "grupp": "...", "ledamot_namn": "...",
     "ledamot_initialer": "...", "motivering": "...", "osakert": false}
  ],
  "statistik": {
    "antal_ansokningar": 147, "antal_ledamoter": 28, "antal_javsrelationer": 210,
    "antal_fordelade": 147, "antal_osakra": 0,
    "per_grupp": {"Bio I": 49, "Bio II": 49, "Bio III": 49},
    "per_ledamot": {"AA": 6, "BB": 5}
  }
}
```
Svaret har alltid `Content-Type: application/json; charset=utf-8` — viktigt för att å/ä/ö ska komma fram korrekt genom Power Automate och vidare till Excel.

**Filer:**
- `FordelaAnsokningar/__init__.py` — HTTP-endpoint, validerar och parsar JSON, anropar motorn, bygger svaret
- `shared/fordelning.py` — Fördelningsmotorn (`Fordelningsmotor`), all algoritmlogik
- `shared/validators.py` — Valideringsfunktioner (används inte av HTTP-endpointen idag, finns tillgängliga för framtida bruk)
- `shared/models.py` — Dataklasser, dubblett av klasserna i `fordelning.py` för tydlighetens skull

**Körtid:** Några sekunder för ~150 ansökningar.

### Power Automate

**Miljö:** Sandbox Dev (medvetet val — inte standardmiljön "Default"). Flödesägare: kontot som skapade flödet.

**Flödesnamn:** "Fördelning forskningsansökningar (jävagent)"

**Trigger:** `Manually trigger a flow` — triggas via en Button-webbdel på SharePoint-sidan (se nedan), inte via en rå HTTP-endpoint. Ingen indata krävs i triggern.

**Flödessteg (i ordning):**

1. `Läs_Ansökningar`, `Läs_Ledamöter`, `Läs_Jäv` — `List rows present in a table` (Excel Online Business), en per Excel-fil i Input-mappen. Filen väljs via filbläddraren i designern (statisk, känd sökväg) — inte via dynamiskt innehåll, eftersom `List rows present in a table` behöver en filreferens den kan fråga om tabellmetadata, inte rått filinnehåll.
2. `Mappa_Ansökningar`, `Mappa_Ledamöter`, `Mappa_Jäv` — `Select`-åtgärder som mappar om Excelns riktiga kolumnrubriker till de fältnamn Azure Function förväntar sig (se tabellen i nästa avsnitt).
3. `Bygg Request` — `Compose`, bygger JSON-body:n till Azure Function av de tre `Select`-outputen.
4. `Anropa Fordelning` — `HTTP`-åtgärd (grön HTTP-connector, inte "HTTP with Microsoft Entra ID"), POST mot `/api/fordela` med function key i headern.
5. `Condition` — `@equals(body('Anropa_Fordelning')?['success'], true)`.
   - **False:** `Post message in a chat or channel` (Teams-felmeddelande) → `Terminate` (Failed).
   - **True:** fortsätt till resultathantering.
6. `Bygg_Filnamn` — `Compose`, bygger ett unikt datumstämplat filnamn: `Fordelning_@{formatDateTime(utcNow(), 'yyyy-MM-dd')}.xlsx`.
7. `Läs_Mall` — `Get file content` på mallfilen `Mall_Fordelning.xlsx` i Output-mappen (statisk, förvald via filbläddraren).
8. `Skapa_Resultatfil` — `Create file`, skriver en ny fil i Output-mappen med namnet från `Bygg_Filnamn` och innehållet från `Läs_Mall`. Detta ger en ny fil per körning istället för att skriva över föregående resultat.
9. `Apply_to_each` över `outputs('Anropa_Fordelning')?['body']?['fordelningar']` → `Add a row into a table` (Excel Online Business) mot den nyskapade filen. Filen refereras **dynamiskt** (`@outputs('Skapa_Resultatfil')?['body/Id']`, inte via filbläddraren, eftersom filen inte finns vid designtillfället) — Table-fältet är därför manuellt inskrivet tabellnamn (`FordelningTabell`) istället för valt ur dropdown. Row-fältet är en handskriven JSON-mappning (se Code view i flödet för exakt innehåll).
10. `Post message in a chat or channel` — Teams-notis vid lyckad körning.

**Kolumnmappning (Excel → Azure Function-fält):**

| Tabell | Excel-kolumn | Function-fält | Anmärkning |
|--------|-------------|----------------|------------|
| Ansökningar | Ans no | `ans_no` | |
| | Sökande | `huvudsokande` | |
| | F.kat | `forskningskategori` | Inte "Kat" — den kolumnen används inte |
| | Område | `omrade` | |
| | Diagnos | `diagnos` | |
| | Nyckelord | `nyckelord` | `split(..., ',')` — kommaseparerad cell → lista |
| Ledamöter | Namn | `namn` | Redan ett fält, ingen sammanslagning behövs |
| | Initialer | `initialer` | |
| | Grupp | `grupp` | |
| | Ordförande | `roll` | `if(equals(..., 'Ordförande'), 'Ordförande', 'Ledamot')` — kolumnen innehåller texten "Ordförande" på ordförande-rader, annars tom |
| | Forskningskategori | `forskningskategori` | |
| | Nyckelord | `nyckelord` | `split(..., ',')` |
| Jäv | Ans no | `ans_no` | |
| | Jäv | `initialer_lista` | `split(..., ',')` — en rad per ansökan, flera initialer i samma cell |

**Kritiskt att veta om Select-åtgärder i Power Automate:** värden måste läggas in via uttrycksredigeraren (fx-ikonen), inte skrivas direkt i textfältet — annars blir värdet bokstavlig text istället för ett evaluerat uttryck. Kontrollera i **Code view** att varje värde börjar med `@` (t.ex. `"ans_no": "@item()?['Ans no']"`), inte är omgivet av citattecken utan `@`-prefix.

### SharePoint

**Site:** `https://bcfintranet.sharepoint.com/sites/Forskning_utveckling_stod`
**Bibliotek:** Forskning och utbildning
**Mapp:** `FORSKNING/PK-agenten Föredragande/Fördelning ansökningar/`

```
Fördelning ansökningar/
├── Input/
│   ├── Ansökningar.xlsx   (formaterad som Excel-tabell)
│   ├── Ledamöter.xlsx     (formaterad som Excel-tabell)
│   └── Jäv.xlsx           (formaterad som Excel-tabell)
└── Output/
    ├── Mall_Fordelning.xlsx        (mall med tom tabell, kopieras varje körning)
    └── Fordelning_YYYY-MM-DD.xlsx  (en fil per körning, skapas automatiskt)
```

**Cockpit-sida:** `https://bcfintranet.sharepoint.com/sites/Forskning_utveckling_stod/SitePages/Fördelning-av-forskningsansökningar.aspx`

Innehåller en **Button-webbdel** med inbyggd åtgärd "Kör Power Automate-flöde". Konfigurerad med flödets **detaljerade identifierare** (inte den korta GUID:en från flödets URL) — hämtas i Power Automate via **Export → Get flow identifier** på det aktuella flödet. Den korta GUID:en fungerar inte eftersom knappfunktionen bara letar i standardmiljön (Default); den detaljerade identifieraren bakar in miljö-informationen och hittar flödet oavsett vilken miljö det ligger i.

## Säkerhet

- **Azure Function:** function-key-autentisering (`authLevel: function` i `function.json`). Nyckeln delas bara med Power Automate-flödet, aldrig checkas in i git.
- **Power Automate:** flödet måste delas (Share → Run only) med de användare/grupper som ska kunna trigga det via knappen — annars ger knappen ett missvisande "kunde inte hitta flödet"-fel istället för ett behörighetsfel.
- **SharePoint:** standard M365-behörigheter på siten/biblioteket.
- **Dataskydd:** Azure Function lagrar ingenting permanent — all data processas i minnet per request och returneras direkt. Excel-filerna (som kan innehålla personuppgifter om sökande och ledamöter) lagras enbart i SharePoint, inom BCF:s egen Microsoft 365-tenant.

## Driftsättning

**Det finns idag ingen CI/CD-koppling.** Push till GitHub deployar inte automatiskt till Azure — det är två helt separata, manuella steg. Att glömma det andra steget är ett vanligt misstag.

### Manuell deploy-process

```bash
# 1. Vendra Linux-kompatibla beroenden (pandas, numpy, openpyxl, azure-functions)
#    lokalt med pip --platform manylinux2014_x86_64 --python-version 3.11
#    till azure-function/.python_packages/lib/site-packages

# 2. Bygg zip med Pythons zipfile-modul (INTE PowerShells Compress-Archive —
#    den skriver bakåtstreck i sökvägarna istället för snedstreck, vilket
#    gör att Linux-värden inte hittar några mappar alls i paketet)

# 3. Ta bort ev. WEBSITE_RUN_FROM_PACKAGE-inställning, deploya, starta om:
az functionapp config appsettings delete --name bcf-fordelning-dev \
    --resource-group rg-bcf-fordelning-dev --setting-names WEBSITE_RUN_FROM_PACKAGE
az functionapp deployment source config-zip --resource-group rg-bcf-fordelning-dev \
    --name bcf-fordelning-dev --src deploy.zip
az functionapp restart --name bcf-fordelning-dev --resource-group rg-bcf-fordelning-dev
```

En riktig CI/CD-pipeline (GitHub Actions) är en naturlig framtida förbättring — se Kända begränsningar nedan.

### Miljöer

| Miljö | Status | URL |
|-------|--------|-----|
| Development | Driftsatt, verifierad | `bcf-fordelning-dev.azurewebsites.net` |
| Production | **Finns inte ännu** | — |

## Övervakning

Application Insights (`bcf-fordelning-dev-ai`) samlar in request-loggar, undantag och körtidsstatistik för Function App. Ingen alerting är konfigurerad ännu.

## Kostnadsuppskattning

| Komponent | Kostnad/månad |
|-----------|---------------|
| Azure Function (Consumption) | ~0 kr (gratis tier vid låg volym) |
| Application Insights | ~0 kr (låg volym) |
| **Totalt Azure** | **~0 kr** |

Power Automate och SharePoint ingår i befintliga M365-licenser.

## Kända begränsningar och teknisk skuld

- **Ingen prod-miljö.** Allt körs mot dev idag.
- **Ingen CI/CD.** Deploy till Azure är manuell, se ovan. Risk för att koden i git och koden i Azure divergerar om deploy-steget glöms bort.
- **Tom grupp kraschar.** Om en prioriteringsgrupp (Bio I/II/III) helt saknar ledamöter kraschar fördelningsmotorn med `IndexError` istället för att hantera fallet snyggt. Osannolikt i praktiken (alla tre grupper har alltid medlemmar), men inte skyddat mot.
- **Select-åtgärderna i Power Automate är ömtåliga att redigera.** Att skriva uttryck direkt i de små inmatningsfälten istället för via uttrycksredigeraren ger tyst fel (bokstavlig text istället för evaluerat värde) eller trasig JSON. Framtida ändringar av kolumnmappningen bör alltid göras via fx-ikonen, aldrig genom att klistra in text direkt.
- **Resultatfilen har en flik, inte tre.** Ursprunglig plan var tre flikar (Fördelning/Statistik/Ledamöter per grupp) men den driftsatta lösningen skriver bara huvudtabellen. `statistik`-objektet finns redan i Azure Function-svaret om ni vill bygga ut flödet med fler flikar senare.
