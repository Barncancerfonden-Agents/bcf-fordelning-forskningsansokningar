# BCF Fördelning av Forskningsansökningar

Automatiserad fördelning av forskningsansökningar till prioriteringsgrupper och granskande ledamöter för Barncancerfonden.

## Översikt

Barncancerfondens forskningsavdelning tar emot cirka 150 forskningsansökningar två gånger per år. Dessa ska fördelas till tre prioriteringsgrupper (Bio I, Bio II, Bio III) och tilldelas en föredragande ledamot som granskar ansökan.

Fördelningen måste ta hänsyn till:
- **Jävsrelationer** mellan ledamöter och sökande
- **Kompetensmatching** baserat på forskningskategori och nyckelord
- **Balansering** av arbetsbelastning mellan grupper och ledamöter

Denna lösning automatiserar hela processen genom en Azure Function som anropas via Power Automate.

## Arkitektur

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Excel-filer    │────▶│  Power Automate  │────▶│  Azure Function │
│  i SharePoint   │     │  (orkestrerare)  │     │  (logik)        │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
                                                ┌─────────────────┐
                                                │  Resultat-Excel │
                                                │  + Dataverse    │
                                                └─────────────────┘
```

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

# Testa med testfiler
python -m azure-function.shared.fordelning --test
```

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

1. **Jäv först**: Ordförande i tilldelad grupp får aldrig vara jävig mot ansökan
2. **Minimera jäv**: Välj grupp med minst antal jäviga ledamöter
3. **Gruppbalans**: Fördela ~50 ansökningar per grupp
4. **Ledamotsbalans**: Varje ledamot får 5-7 ansökningar
5. **Kompetensmatching**: Primärt forskningskategori, sekundärt nyckelord
6. **Flagga osäkra**: Ansökningar där alla ordförande är jäviga markeras

## Indatafiler

Tre Excel/CSV-filer krävs:

### Ansökningar
| Kolumn | Beskrivning |
|--------|-------------|
| Ans no | Unikt ansökningsnummer |
| Huvudsökande | Namn på forskare |
| F.kat | Forskningskategori (Grundforskning/Translationell/Klinisk) |
| Område | Forskningsområde |
| Diagnos | Cancerdiagnos |
| Nyckelord | Kommaseparerade nyckelord |

### Ledamöter
| Kolumn | Beskrivning |
|--------|-------------|
| Förnamn, Efternamn | Ledamotens namn |
| Initialer | Unik identifierare (t.ex. "GB") |
| Prioriteringsgrupp | Bio I, Bio II eller Bio III |
| Roll | Ordförande/Ledamot |
| Forskningskategori | Kompetensområde |
| Nyckelord | Kommaseparerade kompetenser |

### Jävsrelationer
| Kolumn | Beskrivning |
|--------|-------------|
| Ledamot (Initialer) | Vem som är jävig |
| Ans no | Mot vilken ansökan |

## Utdata

Excel-fil med tre flikar:

1. **Fördelning**: Alla ansökningar med grupp, ledamot och motivering
2. **Statistik**: Sammanställning per grupp och ledamot
3. **Ledamöter per grupp**: Översikt

## Underhåll

Lösningen är designad för att vara stabil och kräva minimalt underhåll. Vid ändringar:

- **Ny ledamot**: Lägg till i Ledamöter-filen
- **Ändrad jävsrelation**: Uppdatera Jäv-filen
- **Ändrad algoritm**: Modifiera `azure-function/shared/fordelning.py`

## Kontakt

- **Utvecklat av**: Tech Sisters AB
- **Kund**: Barncancerfonden
- **År**: 2025-2026

## Licens

Proprietär - Barncancerfonden
