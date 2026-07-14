"""
Azure Function: FordelaAnsokningar

HTTP-endpoint för att fördela forskningsansökningar till prioriteringsgrupper
och ledamöter för Barncancerfonden.

Anropas via POST med JSON-body innehållande ansökningar, ledamöter och jävsrelationer.
Returnerar komplett fördelning med motiveringar.
"""

import logging
import json
import azure.functions as func
from ..shared.fordelning import (
    Ansokan, Ledamot, Fordelningsmotor, Fordelning
)


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP-trigger för fördelning av forskningsansökningar.
    
    Förväntat request-format:
    {
        "ansokningar": [
            {
                "ans_no": "KP2024-0001",
                "huvudsokande": "Namn Efternamn",
                "forskningskategori": "Grundforskning",
                "omrade": "Cancerbiologi",
                "diagnos": "Leukemi",
                "nyckelord": ["immunterapi", "t-celler"]
            },
            ...
        ],
        "ledamoter": [
            {
                "namn": "Anna Andersson",
                "initialer": "AA",
                "grupp": "Bio I",
                "roll": "Ledamot",
                "forskningskategori": "Grundforskning",
                "nyckelord": ["genetik", "epigenetik"]
            },
            ...
        ],
        "javsrelationer": [
            {"initialer": "AA", "ans_no": "KP2024-0001"},
            ...
        ]
    }
    
    Response-format:
    {
        "success": true,
        "fordelningar": [
            {
                "ans_no": "KP2024-0001",
                "huvudsokande": "Namn Efternamn",
                "grupp": "Bio I",
                "ledamot_namn": "Anna Andersson",
                "ledamot_initialer": "AA",
                "motivering": "...",
                "osakert": false
            },
            ...
        ],
        "statistik": {
            "antal_ansokningar": 147,
            "antal_fordelade": 147,
            "antal_osakra": 2,
            "per_grupp": {"Bio I": 49, "Bio II": 49, "Bio III": 49},
            "per_ledamot": {"AA": 6, "BB": 5, ...}
        }
    }
    """
    logging.info('FordelaAnsokningar function triggered.')
    
    try:
        # Parsa request body
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "error": "Ogiltig JSON i request body"
            }),
            mimetype="application/json",
            status_code=400
        )
    
    # Validera att alla required fält finns
    required_fields = ['ansokningar', 'ledamoter', 'javsrelationer']
    missing = [f for f in required_fields if f not in req_body]
    if missing:
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "error": f"Saknade fält: {', '.join(missing)}"
            }),
            mimetype="application/json",
            status_code=400
        )
    
    try:
        # Konvertera JSON till dataklasser
        ansokningar = []
        for a in req_body['ansokningar']:
            ansokningar.append(Ansokan(
                ans_no=str(a.get('ans_no', '')).strip(),
                huvudsokande=str(a.get('huvudsokande', '')).strip(),
                forskningskategori=str(a.get('forskningskategori', '')).strip(),
                omrade=str(a.get('omrade', '')).strip(),
                diagnos=str(a.get('diagnos', '')).strip(),
                nyckelord=a.get('nyckelord', [])
            ))
        
        ledamoter = []
        for l in req_body['ledamoter']:
            ledamoter.append(Ledamot(
                namn=str(l.get('namn', '')).strip(),
                initialer=str(l.get('initialer', '')).strip(),
                grupp=str(l.get('grupp', '')).strip(),
                roll=str(l.get('roll', 'Ledamot')).strip(),
                forskningskategori=str(l.get('forskningskategori', '')).strip(),
                nyckelord=l.get('nyckelord', [])
            ))
        
        # Bygg jävsrelationer dict
        javsrelationer = {}
        for j in req_body['javsrelationer']:
            initialer = str(j.get('initialer', '')).strip()
            ans_no = str(j.get('ans_no', '')).strip()
            if initialer and ans_no:
                if initialer not in javsrelationer:
                    javsrelationer[initialer] = set()
                javsrelationer[initialer].add(ans_no)
        
        logging.info(f"Mottog {len(ansokningar)} ansökningar, {len(ledamoter)} ledamöter, "
                     f"{sum(len(v) for v in javsrelationer.values())} jävsrelationer")
        
        # Kör fördelning
        motor = Fordelningsmotor(ansokningar, ledamoter, javsrelationer)
        fordelningar = motor.fordela()
        
        # Bygg response
        fordelningar_json = []
        for f in fordelningar:
            fordelningar_json.append({
                "ans_no": f.ans_no,
                "huvudsokande": f.huvudsokande,
                "grupp": f.grupp,
                "ledamot_namn": f.ledamot_namn,
                "ledamot_initialer": f.ledamot_initialer,
                "motivering": f.motivering,
                "osakert": f.osakert
            })
        
        statistik = {
            "antal_ansokningar": len(ansokningar),
            "antal_ledamoter": len(ledamoter),
            "antal_javsrelationer": sum(len(v) for v in javsrelationer.values()),
            "antal_fordelade": len(fordelningar),
            "antal_osakra": sum(1 for f in fordelningar if f.osakert),
            "per_grupp": dict(motor.ansokningar_per_grupp),
            "per_ledamot": dict(motor.ansokningar_per_ledamot)
        }
        
        logging.info(f"Fördelning klar: {statistik}")
        
        return func.HttpResponse(
            json.dumps({
                "success": True,
                "fordelningar": fordelningar_json,
                "statistik": statistik
            }, ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logging.error(f"Fel vid fördelning: {str(e)}", exc_info=True)
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "error": f"Internt fel: {str(e)}"
            }),
            mimetype="application/json",
            status_code=500
        )
