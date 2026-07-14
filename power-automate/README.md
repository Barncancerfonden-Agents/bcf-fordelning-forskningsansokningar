# Power Automate - Fördelningsflöde

Detta dokument beskriver Power Automate-flödet som orkestrerar fördelningen.

## Översikt

Flödet triggas från SharePoint och:
1. Läser indatafiler (Excel) från SharePoint
2. Konverterar till JSON
3. Anropar Azure Function
4. Skriver resultat till Excel
5. Sparar i SharePoint
6. Notifierar via Teams

## Flödesstruktur

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  TRIGGER: HTTP Request (från SharePoint-knapp)                   │
│                                                                  │
└──────────────────────────────────────┬───────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  SCOPE: Läs indatafiler                                          │
│                                                                  │
│  ├─ Get file content: Ansökningar.xlsx                           │
│  ├─ Get file content: Ledamöter.xlsx                             │
│  └─ Get file content: Jäv.xlsx                                   │
│                                                                  │
└──────────────────────────────────────┬───────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  SCOPE: Konvertera till JSON                                     │
│                                                                  │
│  ├─ List rows present in table: Ansökningar                      │
│  ├─ List rows present in table: Ledamöter                        │
│  ├─ List rows present in table: Jäv                              │
│  └─ Compose: Bygg request body                                   │
│                                                                  │
└──────────────────────────────────────┬───────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  HTTP: Anropa Azure Function                                     │
│                                                                  │
│  Method: POST                                                    │
│  URI: https://bcf-fordelning.azurewebsites.net/api/fordela      │
│  Headers: x-functions-key: [function key]                        │
│  Body: [JSON från föregående steg]                               │
│                                                                  │
└──────────────────────────────────────┬───────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  CONDITION: Lyckad fördelning?                                   │
│                                                                  │
│  IF body('HTTP')?['success'] == true                             │
│                                                                  │
└───────────────┬──────────────────────────────────┬───────────────┘
                │                                  │
           JA   ▼                             NEJ  ▼
┌───────────────────────────┐      ┌───────────────────────────────┐
│                           │      │                               │
│  SCOPE: Skapa resultat    │      │  Post message to Teams        │
│                           │      │  "Fördelning misslyckades"    │
│  ├─ Create Excel file     │      │                               │
│  ├─ Add rows to table     │      │  Terminate: Failed            │
│  └─ Create file (SP)      │      │                               │
│                           │      └───────────────────────────────┘
└───────────────┬───────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  Post message to Teams: "Fördelning klar"                        │
│  (inkludera länk till resultatfil)                               │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Bygginstruktioner

### 1. Skapa nytt flöde

1. Gå till Power Automate
2. Skapa → Instant cloud flow
3. Namnge: "BCF - Kör fördelning"
4. Välj trigger: "When an HTTP request is received"

### 2. Konfigurera trigger

```json
{
  "type": "object",
  "properties": {
    "körning_id": {
      "type": "string"
    }
  }
}
```

Spara HTTP POST URL för användning i SharePoint.

### 3. Lägg till SharePoint-kopplingar

**Get file content using path** (3 stycken):
- Site Address: `https://bcfintranet.sharepoint.com/sites/Forskningsavdelning`
- File Path: `/Fördelning/Indata/Ansökningar.xlsx`

Upprepa för Ledamöter.xlsx och Jäv.xlsx.

### 4. Konvertera Excel till JSON

**List rows present in a table** (3 stycken):
- Location: Samma site
- Document Library: Samma bibliotek
- File: Dynamisk från "Get file content"
- Table name: "Tabell1" (eller faktiskt tabellnamn)

### 5. Bygg request body

**Compose**:
```json
{
  "ansokningar": @{body('List_rows_Ansökningar')?['value']},
  "ledamoter": @{body('List_rows_Ledamöter')?['value']},
  "javsrelationer": @{body('List_rows_Jäv')?['value']}
}
```

### 6. Anropa Azure Function

**HTTP**:
- Method: POST
- URI: `https://bcf-fordelning.azurewebsites.net/api/fordela`
- Headers:
  - Content-Type: application/json
  - x-functions-key: [din function key]
- Body: `@{outputs('Compose')}`

### 7. Hantera resultat

**Condition**: `@equals(body('HTTP')?['success'], true)`

**Om ja:**
- Skapa Excel-fil med resultat
- Spara till SharePoint
- Skicka Teams-meddelande med länk

**Om nej:**
- Skicka felmeddelande till Teams
- Terminate med status Failed

## Testning

1. Verifiera att indatafiler finns i rätt mapp
2. Kör flödet manuellt från Power Automate
3. Kontrollera att resultatfil skapas
4. Granska Teams-notifiering

## Felsökning

### "File not found"
- Kontrollera sökvägar till indatafiler
- Verifiera att filerna är namngivna exakt rätt

### "Table not found"
- Öppna Excel-filerna och verifiera tabellnamn
- Formatera om data som tabell om nödvändigt

### "HTTP 401 Unauthorized"
- Kontrollera function key i HTTP-action
- Verifiera att function key är giltig

### "HTTP 500 Internal Server Error"
- Granska Azure Function logs
- Verifiera att JSON-strukturen är korrekt
