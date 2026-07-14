# Arkitektur

## Översikt

Lösningen består av tre huvudkomponenter:

1. **Azure Function** - Kör fördelningsalgoritmen
2. **Power Automate** - Orkestrerar flödet och hanterar filer
3. **SharePoint** - Lagring och användargränssnitt

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                         FORSKNINGSAVDELNINGEN                               │
│                                                                             │
│   1. Exportera filer    2. Ladda upp         3. Klicka "Kör"               │
│      från internt          till SharePoint       på SharePoint-sidan       │
│      system                                                                 │
│                                                                             │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                            SHAREPOINT                                       │
│                                                                             │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│   │ Mapp:           │    │ Sida:           │    │ Lista:          │        │
│   │ Fördelning/     │    │ Cockpit.aspx    │    │ Historik        │        │
│   │ Indata/         │    │                 │    │                 │        │
│   │ ├─ Ansökningar  │    │ [Importera]     │    │ Körning 1       │        │
│   │ ├─ Ledamöter    │    │ [Kör fördelning]│    │ Körning 2       │        │
│   │ └─ Jäv          │    │ [Ladda ner]     │    │ ...             │        │
│   └─────────────────┘    └────────┬────────┘    └─────────────────┘        │
│                                   │                                         │
└───────────────────────────────────┼─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                         POWER AUTOMATE                                      │
│                                                                             │
│   Flöde: "Kör fördelning"                                                   │
│   ──────────────────────                                                    │
│                                                                             │
│   ┌─────────┐   ┌─────────────┐   ┌──────────────┐   ┌─────────────┐       │
│   │ Trigger │──▶│ Läs Excel-  │──▶│ Konvertera   │──▶│ Anropa      │       │
│   │ (HTTP)  │   │ filer från  │   │ till JSON    │   │ Azure       │       │
│   └─────────┘   │ SharePoint  │   │              │   │ Function    │       │
│                 └─────────────┘   └──────────────┘   └──────┬──────┘       │
│                                                              │              │
│   ┌─────────────┐   ┌─────────────┐   ┌──────────────┐      │              │
│   │ Skicka      │◀──│ Skapa       │◀──│ Ta emot     │◀─────┘              │
│   │ notifiering │   │ resultat-   │   │ JSON-svar   │                      │
│   │ till Teams  │   │ Excel       │   │             │                      │
│   └─────────────┘   └─────────────┘   └──────────────┘                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                         AZURE FUNCTION                                      │
│                                                                             │
│   Endpoint: POST /api/fordela                                               │
│   ────────────────────────────                                              │
│                                                                             │
│   Request:                              Response:                           │
│   {                                     {                                   │
│     "ansokningar": [...],                 "success": true,                  │
│     "ledamoter": [...],                   "fordelningar": [...],            │
│     "javsrelationer": [...]               "statistik": {...}                │
│   }                                     }                                   │
│                                                                             │
│   ┌──────────────────────────────────────────────────────────────────┐     │
│   │                                                                  │     │
│   │   Fördelningsmotor (fordelning.py)                               │     │
│   │   ─────────────────────────────────                              │     │
│   │                                                                  │     │
│   │   1. Parsa indata                                                │     │
│   │   2. För varje ansökan:                                          │     │
│   │      a. Hitta grupp där ordförande EJ jävig                      │     │
│   │      b. Minimera antal jäviga i gruppen                          │     │
│   │      c. Balansera mellan grupper                                 │     │
│   │      d. Välj ledamot med bäst kompetens-match                    │     │
│   │      e. Balansera mellan ledamöter                               │     │
│   │      f. Skapa motivering                                         │     │
│   │   3. Returnera resultat                                          │     │
│   │                                                                  │     │
│   └──────────────────────────────────────────────────────────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Komponentbeskrivning

### Azure Function

**Teknologi:** Python 3.9+, Azure Functions v4

**Filer:**
- `FordelaAnsokningar/__init__.py` - HTTP endpoint
- `shared/fordelning.py` - Fördelningsalgoritm
- `shared/validators.py` - Indatavalidering
- `shared/models.py` - Dataklasser

**Körtid:** 2-5 sekunder för 150 ansökningar

**Skalning:** Consumption plan (betala per körning)

### Power Automate

**Typ:** Instant flow med HTTP-trigger

**Steg:**
1. Triggas från SharePoint-knapp
2. Läser tre Excel-filer från SharePoint
3. Konverterar till JSON
4. Anropar Azure Function
5. Skriver resultat till Excel
6. Sparar i SharePoint
7. Skickar Teams-notifiering

### SharePoint

**Komponenter:**
- Dokumentbibliotek för indatafiler
- Modern sida med knappar (Power Automate-integration)
- Lista för körhistorik (valfritt)

## Säkerhet

### Autentisering

- Azure Function: Function key (delad med Power Automate)
- Power Automate: Kör med service account eller delegated user
- SharePoint: Standard M365-behörigheter

### Dataskydd

- Inga personuppgifter lagras permanent i Azure Function
- All data processas i minnet och returneras direkt
- Excel-filer lagras i SharePoint (BCF:s tenant)

## Driftsättning

### Miljöer

| Miljö | Användning | URL |
|-------|------------|-----|
| Development | Utveckling/test | `bcf-fordelning-dev.azurewebsites.net` |
| Production | Skarp drift | `bcf-fordelning.azurewebsites.net` |

### Deploy-process

1. Push till `main`-branchen
2. GitHub Actions bygger och testar
3. Manuell deploy till production (eller automatisk efter godkännande)

## Övervakning

### Application Insights

- Request-loggar
- Fel och exceptions
- Körtidsstatistik

### Alerting

- Email vid function-fel
- Teams-notifiering vid misslyckad körning

## Kostnadsuppskattning

| Komponent | Kostnad/månad |
|-----------|---------------|
| Azure Function (Consumption) | ~0 kr (gratis tier) |
| Application Insights | ~0 kr (låg volym) |
| **Totalt Azure** | **~0 kr** |

*Power Automate och SharePoint ingår i befintliga M365-licenser.*
