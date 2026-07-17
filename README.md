# BCF Fördelning av Forskningsansökningar

Automatiserad fördelning av forskningsansökningar till prioriteringsgrupper och granskande ledamöter för Barncancerfonden.

## Översikt

Barncancerfondens forskningsavdelning tar emot cirka 150 forskningsansökningar två gånger per år. Dessa ska fördelas till tre prioriteringsgrupper (Bio I, Bio II, Bio III) och tilldelas en föredragande ledamot som granskar ansökan.

Fördelningen måste ta hänsyn till:
- **Jävsrelationer** mellan ledamöter och sökande
- **Kompetensmatching** baserat på forskningskategori och nyckelord
- **Balansering** av arbetsbelastning mellan grupper och ledamöter

Denna lösning automatiserar hela processen genom en Azure Function som anropas via Power Automate, triggat med en knapp på en SharePoint-sida.

**Status:** Driftsatt och i skarp användning mot dev-miljön i Azure. Ingen produktionsmiljö finns ännu (se `docs/ARCHITECTURE.md`).

## Arkitektur

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Excel-filer    │────▶│  Power Automate  │────▶│  Azure Function │
│  i SharePoint   │     │  (orkestrerare)  │     │  (logik)        │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
        ▲                                                  │
        │                                                  ▼
┌─────────────────┐                                ┌─────────────────┐
│  Knapp på       │                                │  Ny resultat-   │
│  SharePoint-sida│                                │  Excel per      │
│  triggar flödet │                                │  körning        │
└─────────────────┘                                └─────────────────┘
```

Fullständig teknisk beskrivning: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Snabbstart

### Förutsättningar

- Python 3.9+
- Azure Functions Core Tools
- Azure CLI (för deploy)
- Tillgång till Barncancerfondens Azure-subscription

### Lokal utveckling

```bash
# Klona repot
git clone https://github.com/Barncancerfonden-Agents/bcf-fordelning-forskningsansokningar.git
cd bcf-fordelning-forskningsansokningar

# Skapa virtuell miljö
python -m venv .venv
source .venv/bin/activate  # På Windows: .venv\Scripts\activate

# Installera beroenden
pip install -r azure-function/requirements.txt

# Kör lokalt
cd azure-function
func start
```

### Testa med exempeldata

```bash
# Kör enhetstester
python -m pytest test/

# Kör fördelningen fristående mot exempelfilerna (utan Azure Function/HTTP)
python azure-function/shared/fordelning.py \
    test/testdata/ansokningar_test.csv \
    test/testdata/ledamoter_test.csv \
    test/testdata/jav_test.csv \
    fordelning_resultat.xlsx
```

**Observera:** driftsättning till Azure sker inte via `func azure functionapp publish` i den här lösningen (Azure Functions Core Tools har inte gått att installera i miljön den byggdes i) — se `docs/ARCHITECTURE.md` för den manuella `az functionapp deployment source config-zip`-processen som faktiskt används.

## Projektstruktur

```
bcf-fordelning-forskningsansokningar/
│
├── README.md                    # Denna fil
├── docs/
│   ├── ARCHITECTURE.md          # Teknisk arkitektur
│   ├── USER_GUIDE.md            # Guide för forskningsavdelningen
│   └── ALGORITHM.md             # Beskrivning av fördelningslogiken
│
├── azure-function/
│   ├── FordelaAnsokningar/
│   │   ├── __init__.py          # Azure Function endpoint
│   │   └── function.json        # Function-konfiguration
│   ├── shared/
│   │   ├── fordelning.py        # Fördelningsalgoritmen
│   │   ├── models.py            # Dataklasser
│   │   └── validators.py        # Validering av indata
│   ├── requirements.txt
│   ├── host.json
│   └── local.settings.json.template
│
├── power-automate/
│   └── README.md                # Beskrivning av Power Automate-flödet
│
├── sharepoint/
│   └── README.md                # Beskrivning av SharePoint-cockpit
│
├── test/
│   ├── test_fordelning.py       # Enhetstester
│   └── testdata/                # Exempelfiler
│
└── .gitignore
```

## Dokumentation

| Dokument | Beskrivning |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Teknisk arkitektur och flöden |
| [USER_GUIDE.md](docs/USER_GUIDE.md) | Användarguide för forskningsavdelningen |
| [ALGORITHM.md](docs/ALGORITHM.md) | Detaljerad beskrivning av fördelningsalgoritmen |

## Fördelningsregler (sammanfattning)

Prioritetsordning — varje regel avgör bara när regeln ovanför den inte räcker för att skilja kandidater åt:

1. **Jäv först**: en jävig person tilldelas i praktiken aldrig. Om alla ledamöter i den naturliga gruppen är jäviga letar motorn i andra grupper. Bara om ingen jävfri ledamot finns någonstans tilldelas en jävig person, och då flaggas ansökan alltid som osäker.
2. **Minimera jäv**: välj grupp med minst antal jäviga ledamöter (och där ordförande inte är jävig)
3. **Gruppbalans**: fördela ~50 ansökningar per grupp
4. **Ledamotsbalans**: väger tyngre än kompetensmatchning — avgör vem som tilldelas bland jävfria kandidater
5. **Kompetensmatching**: forskningskategori och nyckelord, används bara för att skilja mellan annars lika belastade ledamöter
6. **Flagga osäkra**: ansökningar där alla ordförande är jäviga, eller där jäv inte gick att undvika alls

Fullständig algoritmbeskrivning: [docs/ALGORITHM.md](docs/ALGORITHM.md).

## Indatafiler

Tre Excel-filer krävs, formaterade som Excel-tabeller (Infoga → Tabell), med exakt dessa filnamn: **Ansökningar.xlsx**, **Ledamöter.xlsx**, **Jäv.xlsx**.

### Ansökningar.xlsx
| Kolumn | Beskrivning |
|--------|-------------|
| Ans no | Unikt ansökningsnummer |
| Sökande | Namn på forskare |
| F.kat | Forskningskategori |
| Område | Forskningsområde |
| Diagnos | Cancerdiagnos |
| Nyckelord | Kommaseparerade nyckelord |

### Ledamöter.xlsx
| Kolumn | Beskrivning |
|--------|-------------|
| Namn | Ledamotens fullständiga namn |
| Initialer | Unik identifierare (t.ex. "GB"), måste matcha Jäv.xlsx exakt |
| Grupp | Bio I, Bio II eller Bio III |
| Ordförande | Texten "Ordförande" på ordförande-rader, annars tomt |
| Forskningskategori | Kompetensområde |
| Nyckelord | Kommaseparerade kompetenser |

### Jäv.xlsx
| Kolumn | Beskrivning |
|--------|-------------|
| Ans no | Ansökningsnummer |
| Jäv | Alla jäviga initialer för ansökan, kommaseparerade i samma cell (en rad per ansökan) |

Fullständig, användarvänlig beskrivning: [docs/USER_GUIDE.md](docs/USER_GUIDE.md).

## Utdata

En ny Excel-fil per körning (`Fordelning_YYYY-MM-DD.xlsx`), med en tabell: Ans no, Huvudsökande, Grupp, Föredragande, Initialer, Motivering, Osäker.

## Underhåll

- **Ny ledamot**: Lägg till i Ledamöter.xlsx
- **Ändrad jävsrelation**: Uppdatera Jäv.xlsx
- **Ändrad algoritm**: Modifiera `azure-function/shared/fordelning.py`, kör om `pytest test/`, deploya manuellt (se `docs/ARCHITECTURE.md` — ingen CI/CD finns, push till GitHub deployar inte automatiskt)

## Kontakt

- **Utvecklat av**: Tech Sisters AB
- **Kund**: Barncancerfonden
- **År**: 2025-2026

## Licens

Proprietär - Barncancerfonden
