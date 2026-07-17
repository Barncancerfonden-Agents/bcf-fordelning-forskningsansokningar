# SharePoint - Fördelningscockpit

Beskriver den faktiskt driftsatta SharePoint-delen av lösningen.

## Plats

- **Site:** [Forskning, utveckling & stöd](https://bcfintranet.sharepoint.com/sites/Forskning_utveckling_stod)
- **Dokumentbibliotek:** Forskning och utbildning
- **Mapp:** `FORSKNING/PK-agenten Föredragande/Fördelning ansökningar/`

## Mappstruktur

```
Fördelning ansökningar/
├── Input/
│   ├── Ansökningar.xlsx   (Excel-tabell, se docs/USER_GUIDE.md för kolumner)
│   ├── Ledamöter.xlsx     (Excel-tabell)
│   └── Jäv.xlsx           (Excel-tabell)
└── Output/
    ├── Mall_Fordelning.xlsx        (mall med tom resultattabell, rör ej)
    └── Fordelning_YYYY-MM-DD.xlsx  (en fil per körning, skapas automatiskt av flödet)
```

- [Input-mappen](https://bcfintranet.sharepoint.com/sites/Forskning_utveckling_stod/Forskning%20och%20utbildning/Forms/AllItems.aspx?id=%2Fsites%2FForskning%5Futveckling%5Fstod%2FForskning%20och%20utbildning%2FFORSKNING%2FPK%2Dagenten%20F%C3%B6redragande%2FF%C3%B6rdelning%20ans%C3%B6kningar%2FInput&viewid=3ee8afc5%2Deb0d%2D4566%2D9f82%2Df60d7ffe63f0)
- [Output-mappen](https://bcfintranet.sharepoint.com/sites/Forskning_utveckling_stod/Forskning%20och%20utbildning/Forms/AllItems.aspx?id=%2Fsites%2FForskning%5Futveckling%5Fstod%2FForskning%20och%20utbildning%2FFORSKNING%2FPK%2Dagenten%20F%C3%B6redragande%2FF%C3%B6rdelning%20ans%C3%B6kningar%2FOutput&viewid=3ee8afc5%2Deb0d%2D4566%2D9f82%2Df60d7ffe63f0)

Indatafilerna måste vara formaterade som riktiga Excel-tabeller (Infoga → Tabell) — Power Automate-flödet läser dem via `List rows present in a table`, vilket kräver en namngiven tabell, inte bara rådata i ett kalkylblad.

## Cockpit-sidan

**URL:** [Fördelning av forskningsansökningar](https://bcfintranet.sharepoint.com/sites/Forskning_utveckling_stod/SitePages/F%C3%B6rdelning-av-forskningsans%C3%B6kningar.aspx)

Sidan innehåller en instruktionstext och en **Button-webbdel** ("Starta fördelning") kopplad direkt till Power Automate-flödet via knappens inbyggda åtgärd **"Kör Power Automate-flöde"**.

### Så är knappen konfigurerad

Moderna SharePoint-knappar har (till skillnad från vad som tidigare antogs i den här dokumentationen) ingen generell "Power Automate"-webbdel att lägga till separat — istället har den vanliga **Button**-webbdelen ett åtgärdsval **"Kör Power Automate flöde"** direkt i sina inställningar:

1. Lägg till en **Button**-webbdel på sidan
2. Knapptext: t.ex. "Starta fördelning"
3. Åtgärd: **Kör Power Automate flöde**
4. Flödes-ID: den **detaljerade identifieraren**, inte den korta GUID:en från flödets URL

**Varför den detaljerade identifieraren krävs:** flödet ligger i Power Automate-miljön "Sandbox Dev", inte standardmiljön. Knappfunktionen letar bara i standardmiljön om man bara anger den korta GUID:en (t.ex. `59b46383-2080-f111-ab0f-70a8a581669b`) — resultatet blir felmeddelandet "Det gick inte att hitta flödet" trots korrekt ID och rätt användare. Lösningen: i Power Automate, öppna flödet → **Export** → **Get flow identifier**, och klistra in hela den strängen (format `v1/{miljö-id}-{flödes-id}...`) i knappens Flödes-ID-fält istället. Den bakar in miljöinformationen och fungerar oavsett vilken miljö flödet ligger i.

Se `power-automate/README.md` för mer bakgrund om triggerval.

### Instruktionstext på sidan

```
Klicka på knappen nedan efter att du laddat upp de tre filerna som
behövs för att göra fördelningen. När du har klickat på knappen tar
det ca 5-10 minuter innan fördelningen är klar. Du får då ett
meddelande på Teams.
```

## Behörigheter

| Roll | Behörighet |
|------|------------|
| Forskningsavdelningen | Redigera (Contribute) på Input/Output-mapparna, samt köråtkomst till Power Automate-flödet (Share → Run only i Power Automate — annars ger knappen ett missvisande "hittade inte flödet"-fel istället för ett behörighetsfel) |
| IT-support / utvecklare | Fullständig kontroll, ägare av flödet |
| Övriga | Ingen åtkomst |

## Underhåll

- **Uppdatera indatafiler:** skriv över filerna i Input-mappen med samma filnamn inför varje körning. Gamla resultatfiler i Output skrivs aldrig över (varje körning får ett eget, datumstämplat filnamn) — arkivera/städa manuellt vid behov.
- **Rör inte `Mall_Fordelning.xlsx`** i Output-mappen — den kopieras av flödet vid varje körning och måste ha exakt samma tabellstruktur som flödet förväntar sig (se `power-automate/README.md`).
