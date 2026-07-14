"""
Enhetstester för fördelningsalgoritmen.

Kör med: python -m pytest test/test_fordelning.py -v
"""

import pytest
import sys
import os

# Lägg till azure-function i path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'azure-function'))

from shared.fordelning import (
    Ansokan, Ledamot, Fordelningsmotor, Fordelning
)
from shared.validators import (
    validera_ansokningar, validera_ledamoter, validera_all_indata
)


# ============================================================================
# Test fixtures
# ============================================================================

@pytest.fixture
def grunddata_ansokningar():
    """Skapa testansökningar."""
    return [
        Ansokan(
            ans_no="KP2024-0001",
            huvudsokande="Anna Andersson",
            forskningskategori="Grundforskning",
            omrade="Cancerbiologi",
            diagnos="Leukemi",
            nyckelord=["immunterapi", "t-celler"]
        ),
        Ansokan(
            ans_no="KP2024-0002",
            huvudsokande="Bertil Bertilsson",
            forskningskategori="Klinisk",
            omrade="Behandling",
            diagnos="Hjärntumör",
            nyckelord=["strålbehandling", "kirurgi"]
        ),
        Ansokan(
            ans_no="KP2024-0003",
            huvudsokande="Cecilia Cecilsson",
            forskningskategori="Translationell",
            omrade="Diagnostik",
            diagnos="Neuroblastom",
            nyckelord=["biomarkörer", "diagnostik"]
        ),
    ]


@pytest.fixture
def grunddata_ledamoter():
    """Skapa testledamöter."""
    return [
        # Bio I
        Ledamot("Gisela Barbany", "GB", "Bio I", "Ordförande", "Grundforskning", ["genetik", "leukemi"]),
        Ledamot("Lars Palmqvist", "LP", "Bio I", "Ledamot", "Grundforskning", ["immunterapi", "t-celler"]),
        Ledamot("Stina Söderlund", "SS", "Bio I", "Ledamot", "Grundforskning", ["cellbiologi"]),
        
        # Bio II
        Ledamot("Karin Mellgren", "KM", "Bio II", "Ordförande", "Klinisk", ["pediatrik", "behandling"]),
        Ledamot("Kristina Nilsson", "KN", "Bio II", "Ledamot", "Klinisk", ["strålbehandling", "kirurgi"]),
        Ledamot("Per Davidsson", "PD", "Bio II", "Ledamot", "Translationell", ["läkemedelsutveckling"]),
        
        # Bio III
        Ledamot("Richard Rosenquist", "RR", "Bio III", "Ordförande", "Translationell", ["genomik"]),
        Ledamot("Theresa Vincent", "TV", "Bio III", "Ledamot", "Translationell", ["biomarkörer", "diagnostik"]),
        Ledamot("Johan Malmström", "JM", "Bio III", "Ledamot", "Grundforskning", ["proteomik"]),
    ]


@pytest.fixture
def grunddata_jav():
    """Skapa testjävsrelationer."""
    return {
        "LP": {"KP2024-0001"},  # LP jävig mot ansökan 1
        "KN": {"KP2024-0002"},  # KN jävig mot ansökan 2
    }


# ============================================================================
# Tester för Fördelningsmotor
# ============================================================================

class TestFordelningsmotor:
    """Tester för huvudalgoritmen."""
    
    def test_grundlaggande_fordelning(self, grunddata_ansokningar, grunddata_ledamoter, grunddata_jav):
        """Verifiera att grundläggande fördelning fungerar."""
        motor = Fordelningsmotor(grunddata_ansokningar, grunddata_ledamoter, grunddata_jav)
        fordelningar = motor.fordela()
        
        assert len(fordelningar) == 3
        assert all(isinstance(f, Fordelning) for f in fordelningar)
    
    def test_alla_ansokningar_fordelas(self, grunddata_ansokningar, grunddata_ledamoter, grunddata_jav):
        """Verifiera att alla ansökningar får en fördelning."""
        motor = Fordelningsmotor(grunddata_ansokningar, grunddata_ledamoter, grunddata_jav)
        fordelningar = motor.fordela()
        
        fordelade_ans_no = {f.ans_no for f in fordelningar}
        alla_ans_no = {a.ans_no for a in grunddata_ansokningar}
        
        assert fordelade_ans_no == alla_ans_no
    
    def test_ordforande_tilldelas_aldrig(self, grunddata_ansokningar, grunddata_ledamoter, grunddata_jav):
        """Verifiera att ordförande aldrig tilldelas ansökningar."""
        motor = Fordelningsmotor(grunddata_ansokningar, grunddata_ledamoter, grunddata_jav)
        fordelningar = motor.fordela()
        
        ordforande_initialer = {"GB", "KM", "RR"}
        
        for f in fordelningar:
            assert f.ledamot_initialer not in ordforande_initialer, \
                f"Ordförande {f.ledamot_initialer} tilldelades ansökan {f.ans_no}"
    
    def test_javig_tilldelas_ej(self, grunddata_ansokningar, grunddata_ledamoter, grunddata_jav):
        """Verifiera att jäviga ledamöter inte tilldelas."""
        motor = Fordelningsmotor(grunddata_ansokningar, grunddata_ledamoter, grunddata_jav)
        fordelningar = motor.fordela()
        
        for f in fordelningar:
            initialer = f.ledamot_initialer
            if initialer in grunddata_jav:
                assert f.ans_no not in grunddata_jav[initialer], \
                    f"Jävig ledamot {initialer} tilldelades ansökan {f.ans_no}"
    
    def test_giltig_grupp_tilldelas(self, grunddata_ansokningar, grunddata_ledamoter, grunddata_jav):
        """Verifiera att endast giltiga grupper tilldelas."""
        motor = Fordelningsmotor(grunddata_ansokningar, grunddata_ledamoter, grunddata_jav)
        fordelningar = motor.fordela()
        
        giltiga_grupper = {"Bio I", "Bio II", "Bio III"}
        
        for f in fordelningar:
            assert f.grupp in giltiga_grupper, f"Ogiltig grupp: {f.grupp}"
    
    def test_motivering_skapas(self, grunddata_ansokningar, grunddata_ledamoter, grunddata_jav):
        """Verifiera att motivering skapas för alla fördelningar."""
        motor = Fordelningsmotor(grunddata_ansokningar, grunddata_ledamoter, grunddata_jav)
        fordelningar = motor.fordela()
        
        for f in fordelningar:
            assert f.motivering is not None
            assert len(f.motivering) > 10, f"För kort motivering för {f.ans_no}"


class TestOrdforandeJav:
    """Tester för hantering av ordförandejäv."""
    
    def test_ordforande_javig_valjer_annan_grupp(self):
        """Om ordförande är jävig ska en annan grupp väljas."""
        ansokningar = [
            Ansokan("KP2024-0001", "Test Testsson", "Grundforskning", "", "", [])
        ]
        
        ledamoter = [
            Ledamot("Ordf I", "OI", "Bio I", "Ordförande", "", []),
            Ledamot("Led I", "LI", "Bio I", "Ledamot", "", []),
            Ledamot("Ordf II", "OII", "Bio II", "Ordförande", "", []),
            Ledamot("Led II", "LII", "Bio II", "Ledamot", "", []),
            Ledamot("Ordf III", "OIII", "Bio III", "Ordförande", "", []),
            Ledamot("Led III", "LIII", "Bio III", "Ledamot", "", []),
        ]
        
        # Ordförande i Bio I är jävig
        jav = {"OI": {"KP2024-0001"}}
        
        motor = Fordelningsmotor(ansokningar, ledamoter, jav)
        fordelningar = motor.fordela()
        
        # Ska inte hamna i Bio I
        assert fordelningar[0].grupp != "Bio I"
    
    def test_alla_ordforande_javiga_markeras_osakert(self):
        """Om alla ordförande är jäviga ska ansökan markeras som osäker."""
        ansokningar = [
            Ansokan("KP2024-0001", "Test Testsson", "Grundforskning", "", "", [])
        ]
        
        ledamoter = [
            Ledamot("Ordf I", "OI", "Bio I", "Ordförande", "", []),
            Ledamot("Led I", "LI", "Bio I", "Ledamot", "", []),
            Ledamot("Ordf II", "OII", "Bio II", "Ordförande", "", []),
            Ledamot("Led II", "LII", "Bio II", "Ledamot", "", []),
            Ledamot("Ordf III", "OIII", "Bio III", "Ordförande", "", []),
            Ledamot("Led III", "LIII", "Bio III", "Ledamot", "", []),
        ]
        
        # Alla ordförande är jäviga
        jav = {
            "OI": {"KP2024-0001"},
            "OII": {"KP2024-0001"},
            "OIII": {"KP2024-0001"},
        }
        
        motor = Fordelningsmotor(ansokningar, ledamoter, jav)
        fordelningar = motor.fordela()
        
        assert fordelningar[0].osakert == True


class TestBalansering:
    """Tester för balansering mellan grupper och ledamöter."""
    
    def test_gruppbalans(self):
        """Verifiera att ansökningar fördelas jämnt mellan grupper."""
        # Skapa 9 ansökningar (3 per grupp)
        ansokningar = [
            Ansokan(f"KP2024-{i:04d}", f"Sökande {i}", "Grundforskning", "", "", [])
            for i in range(1, 10)
        ]
        
        ledamoter = [
            Ledamot("Ordf I", "OI", "Bio I", "Ordförande", "", []),
            Ledamot("Led I", "LI", "Bio I", "Ledamot", "", []),
            Ledamot("Ordf II", "OII", "Bio II", "Ordförande", "", []),
            Ledamot("Led II", "LII", "Bio II", "Ledamot", "", []),
            Ledamot("Ordf III", "OIII", "Bio III", "Ordförande", "", []),
            Ledamot("Led III", "LIII", "Bio III", "Ledamot", "", []),
        ]
        
        motor = Fordelningsmotor(ansokningar, ledamoter, {})
        fordelningar = motor.fordela()
        
        per_grupp = {}
        for f in fordelningar:
            per_grupp[f.grupp] = per_grupp.get(f.grupp, 0) + 1
        
        # Varje grupp ska ha 3 ansökningar
        assert per_grupp.get("Bio I", 0) == 3
        assert per_grupp.get("Bio II", 0) == 3
        assert per_grupp.get("Bio III", 0) == 3


# ============================================================================
# Tester för validering
# ============================================================================

class TestValidering:
    """Tester för indatavalidering."""
    
    def test_validera_tomma_ansokningar(self):
        """Tom lista ska ge fel."""
        resultat = validera_ansokningar([])
        assert resultat.ok == False
        assert len(resultat.fel) > 0
    
    def test_validera_saknat_ans_no(self):
        """Saknat ans_no ska ge fel."""
        ansokningar = [{"huvudsokande": "Test"}]  # Saknar ans_no
        resultat = validera_ansokningar(ansokningar)
        assert resultat.ok == False
    
    def test_validera_duplicerat_ans_no(self):
        """Duplicerat ans_no ska ge fel."""
        ansokningar = [
            {"ans_no": "KP2024-0001"},
            {"ans_no": "KP2024-0001"},  # Duplikat
        ]
        resultat = validera_ansokningar(ansokningar)
        assert resultat.ok == False
    
    def test_validera_saknade_nyckelord_varnar(self):
        """Saknade nyckelord ska ge varning (inte fel)."""
        ansokningar = [{"ans_no": "KP2024-0001"}]  # Saknar nyckelord
        resultat = validera_ansokningar(ansokningar)
        assert resultat.ok == True  # OK men med varning
        assert len(resultat.varningar) > 0


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
