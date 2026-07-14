# SharePoint - Fördelningscockpit

Detta dokument beskriver SharePoint-komponenten av fördelningslösningen.

## Översikt

SharePoint används för:
1. **Lagring** av indatafiler och resultat
2. **Användargränssnitt** för att trigga fördelningen
3. **Historik** över tidigare körningar

## Mappstruktur

```
Fördelning/
├── Indata/
│   ├── Ansökningar.xlsx
│   ├── Ledamöter.xlsx
│   └── Jäv.xlsx
│
├── Resultat/
│   ├── Fördelning_2024-01-VT.xlsx
│   ├── Fördelning_2024-02-HT.xlsx
│   └── ...
│
└── Arkiv/
    └── (gamla indatafiler)
```

## Cockpit-sida

### Skapa sidan

1. Gå till SharePoint-siten
2. Klicka **Ny** → **Sida**
3. Välj **Tom sida**
4. Namnge: "Fördelning av forskningsansökningar"

### Lägg till komponenter

#### Rubriksektion

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Fördelning av forskningsansökningar                       │
│   ═══════════════════════════════════                       │
│                                                             │
│   Fördela inkomna ansökningar till prioriteringsgrupper     │
│   och granskande ledamöter.                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Indatafiler (Dokumentbibliotek-webbdel)

1. Lägg till webbdel **Dokumentbibliotek**
2. Välj mappen "Indata"
3. Ställ in:
   - Visa: Kompakt lista
   - Antal objekt: 10

#### Knappar (Button-webbdel)

1. Lägg till webbdel **Button**
2. Konfigurera:
   - Text: "Kör fördelning"
   - Länk: [Power Automate HTTP trigger URL]
   - Öppna i: Samma fönster

*Alternativt: Använd Power Automate-knappwebbdelen om tillgänglig.*

#### Resultat (Dokumentbibliotek-webbdel)

1. Lägg till webbdel **Dokumentbibliotek**
2. Välj mappen "Resultat"
3. Ställ in:
   - Visa: Lista
   - Sortering: Ändrad (nyast först)
   - Antal objekt: 5

### Slutresultat

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   Fördelning av forskningsansökningar                                       │
│   ═══════════════════════════════════                                       │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   📁 Indatafiler                                                            │
│   ─────────────                                                             │
│   📄 Ansökningar.xlsx         Ändrad: 2024-01-15 09:30                      │
│   📄 Ledamöter.xlsx           Ändrad: 2024-01-14 14:22                      │
│   📄 Jäv.xlsx                 Ändrad: 2024-01-15 09:31                      │
│                                                                             │
│   ┌──────────────────────┐                                                  │
│   │   ▶ Kör fördelning   │                                                  │
│   └──────────────────────┘                                                  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   📁 Resultat                                                               │
│   ───────────                                                               │
│   📄 Fördelning_2024-01-15.xlsx    Ändrad: 2024-01-15 10:05                 │
│   📄 Fördelning_2024-01-14.xlsx    Ändrad: 2024-01-14 15:30                 │
│   📄 Fördelning_2024-01-10.xlsx    Ändrad: 2024-01-10 11:22                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Behörigheter

### Rekommenderad behörighetsstruktur

| Roll | Behörighet |
|------|------------|
| Forskningsavdelningen | Redigera (Contribute) |
| IT-support | Fullständig kontroll |
| Övriga | Ingen åtkomst |

### Konfigurera behörigheter

1. Gå till mappen "Fördelning"
2. Klicka **...** → **Hantera åtkomst**
3. Avbryt ärvda behörigheter
4. Lägg till gruppen "Forskningsavdelningen" med Redigera-behörighet

## Underhåll

### Rensa gamla resultat

Flytta resultatfiler äldre än 2 år till Arkiv-mappen.

### Uppdatera indatafiler

Se till att rätt filer ligger i Indata-mappen före varje körning.
Gamla indatafiler kan flyttas till Arkiv.

## Alternativ: Power Apps-gränssnitt

För ett mer avancerat gränssnitt kan en Power Apps Canvas App byggas:

- Filuppladdning med validering
- Progress-indikator under körning
- Inline-visning av resultat
- Historik med sökfunktion

*Detta är en framtida förbättring om behov finns.*
