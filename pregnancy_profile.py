"""Pregnancy profile and personalized nutrition requirements."""
from datetime import datetime, date
from typing import Dict, Optional

# Language setting - all bot responses will be in this language
LANGUAGE = "German"
LANGUAGE_INSTRUCTION = f"IMPORTANT: Always respond in {LANGUAGE}."


class PregnancyProfile:
    """Stores and calculates pregnancy-specific information."""
    
    def __init__(self):
        """Initialize with user's pregnancy data."""
        # Personal information
        self.age = 31
        self.weight_kg = 63
        self.height_cm = None  # Can be added if needed
        self.health_status = "gesund und in guter Form"
        
        # Pregnancy information
        # Week 5 on Jan 6, 2026 means pregnancy started around Dec 2, 2025
        # (conception ~2 weeks after last menstrual period)
        self.pregnancy_start_date = date(2025, 12, 2)  # Estimated start of pregnancy
        self.due_date = date(2026, 9, 7)  # ~40 weeks from start
        
        # Supplementation - Orthomol Natal provides daily:
        # (per daily dose: 1 tablet + 1 capsule + probiotics)
        self.supplements = {
            "name": "Orthomol Natal",
            "daily_nutrients": {
                "folate_mcg": 800,  # as Metafolin (active form)
                "iron_mg": 15,
                "calcium_mg": 150,
                "magnesium_mg": 75,
                "zinc_mg": 7.5,
                "iodine_mcg": 150,
                "selenium_mcg": 35,
                "vitamin_d_iu": 800,  # 20mcg
                "vitamin_c_mg": 110,
                "vitamin_e_mg": 13,
                "vitamin_b1_mg": 1.2,
                "vitamin_b2_mg": 1.6,
                "vitamin_b6_mg": 1.9,
                "vitamin_b12_mcg": 3.5,
                "biotin_mcg": 60,
                "niacin_mg": 15,
                "pantothenic_acid_mg": 6,
                "omega3_dha_mg": 200,
                "omega3_epa_mg": 30,
            }
        }
        
    def get_current_week(self) -> int:
        """Calculate current pregnancy week."""
        today = date.today()
        days_pregnant = (today - self.pregnancy_start_date).days
        weeks = days_pregnant // 7
        return max(1, min(weeks, 42))  # Clamp between 1-42 weeks
    
    def get_trimester(self) -> int:
        """Get current trimester (1, 2, or 3)."""
        week = self.get_current_week()
        if week <= 12:
            return 1
        elif week <= 27:
            return 2
        else:
            return 3
    
    def get_trimester_name(self) -> str:
        """Get trimester name."""
        trimester = self.get_trimester()
        return ["First", "Second", "Third"][trimester - 1]
    
    def get_context_string(self) -> str:
        """Get a formatted string with pregnancy context for LLM prompts."""
        week = self.get_current_week()
        trimester = self.get_trimester()
        trimester_names_de = {1: "Erstes", 2: "Zweites", 3: "Drittes"}
        trimester_name = trimester_names_de.get(trimester, "Erstes")
        
        supp = self.supplements["daily_nutrients"]
        
        return f"""SCHWANGERSCHAFTSPROFIL:
- Alter: {self.age} Jahre
- Gewicht: {self.weight_kg} kg
- Gesundheitszustand: {self.health_status}
- Aktuelle Schwangerschaftswoche: {week}
- Trimester: {trimester_name} Trimester (Trimester {trimester})
- Errechneter Geburtstermin: {self.due_date.strftime('%d.%m.%Y')}

NAHRUNGSERGÄNZUNG (täglich): {self.supplements['name']}
Das Supplement liefert bereits:
- Folsäure: {supp['folate_mcg']}mcg (aktive Form Metafolin - VOLLSTÄNDIG abgedeckt!)
- Eisen: {supp['iron_mg']}mg
- Vitamin D: {supp['vitamin_d_iu']} IE
- Vitamin B12: {supp['vitamin_b12_mcg']}mcg
- Omega-3 DHA: {supp['omega3_dha_mg']}mg (wichtig für Gehirnentwicklung)
- Jod: {supp['iodine_mcg']}mcg
- Zink: {supp['zinc_mg']}mg

WICHTIG: Bei Empfehlungen berücksichtigen, dass viele Mikronährstoffe bereits durch Orthomol Natal abgedeckt sind!
Fokus auf: Protein, Kalzium, Eisen (ergänzend), Ballaststoffe, Omega-3 aus Nahrung."""

    def get_supplement_nutrients(self) -> Dict[str, float]:
        """Get nutrients provided daily by Orthomol Natal supplement."""
        supp = self.supplements["daily_nutrients"]
        return {
            "folate_mcg": supp["folate_mcg"],  # 800mcg - more than daily need!
            "iron_mg": supp["iron_mg"],  # 15mg
            "calcium_mg": supp["calcium_mg"],  # 150mg
            "vitamin_d_iu": supp["vitamin_d_iu"],  # 800 IU
            "vitamin_c_mg": supp["vitamin_c_mg"],  # 110mg
            "vitamin_b12_mcg": supp["vitamin_b12_mcg"],  # 3.5mcg
            "zinc_mg": supp["zinc_mg"],  # 7.5mg
            "omega3_g": (supp["omega3_dha_mg"] + supp["omega3_epa_mg"]) / 1000,  # ~0.23g
        }
    
    def get_adjusted_requirements(self) -> Dict[str, float]:
        """
        Get nutrition requirements adjusted for pregnancy stage.
        Requirements vary by trimester.
        These are TOTAL requirements (food + supplements).
        """
        week = self.get_current_week()
        trimester = self.get_trimester()
        
        # Base requirements for pregnancy (total daily need)
        requirements = {
            "calories": 2200,
            "protein_g": 71,
            "carbohydrates_g": 175,
            "fiber_g": 28,
            "fat_g": 73,
            "folate_mcg": 600,
            "iron_mg": 27,
            "calcium_mg": 1000,
            "vitamin_d_iu": 600,
            "vitamin_c_mg": 85,
            "vitamin_a_mcg": 770,
            "vitamin_b12_mcg": 2.6,
            "zinc_mg": 11,
            "omega3_g": 1.4
        }
        
        # Adjust based on trimester
        if trimester == 1:
            # First trimester: Focus on folate, lower calorie needs
            requirements["calories"] = 1800  # May eat less due to nausea
            requirements["folate_mcg"] = 600  # Critical for neural tube development
        elif trimester == 2:
            # Second trimester: Increased calorie and protein needs
            requirements["calories"] = 2200
            requirements["protein_g"] = 75
            requirements["calcium_mg"] = 1000
        else:
            # Third trimester: Highest calorie and nutrient needs
            requirements["calories"] = 2400
            requirements["protein_g"] = 80
            requirements["iron_mg"] = 30  # Increased blood volume
            requirements["calcium_mg"] = 1200
        
        return requirements
    
    def get_food_requirements(self) -> Dict[str, float]:
        """
        Get what still needs to come from FOOD after Orthomol Natal supplement.
        This is total requirements minus supplement contribution.
        """
        total_req = self.get_adjusted_requirements()
        supplement = self.get_supplement_nutrients()
        
        food_req = {}
        for nutrient, total in total_req.items():
            supp_amount = supplement.get(nutrient, 0)
            # Don't go negative - supplement may exceed requirements for some nutrients
            food_req[nutrient] = max(0, total - supp_amount)
        
        return food_req
    
    def get_trimester_focus_nutrients(self) -> str:
        """Get key nutrients to focus on for current trimester (in German)."""
        trimester = self.get_trimester()
        
        # Note: Orthomol Natal already covers: Folate (800mcg), Vitamin D, B12, most vitamins
        # Focus recommendations on what FOOD needs to provide
        
        if trimester == 1:
            return """Wichtige Nährstoffe für das Erste Trimester:
✅ FOLSÄURE: Durch Orthomol Natal VOLLSTÄNDIG abgedeckt (800mcg Metafolin)!
✅ Vitamin D, B12, Zink: Auch durch Supplement abgedeckt

🍽️ Aus der Nahrung wichtig:
- PROTEIN: ca. 71g täglich (Fleisch, Fisch, Hülsenfrüchte, Eier)
- KALZIUM: 850mg noch aus Nahrung (Milchprodukte, grünes Gemüse)
- EISEN: noch 12mg aus Nahrung (rotes Fleisch, Spinat, Hülsenfrüchte)
- Kleine, häufige Mahlzeiten helfen bei Übelkeit
- Ingwertee kann bei Morgenübelkeit helfen"""
        elif trimester == 2:
            return """Wichtige Nährstoffe für das Zweite Trimester:
✅ Vitamine & Mikronährstoffe: Durch Orthomol Natal gut abgedeckt

🍽️ Aus der Nahrung wichtig:
- KALZIUM (850mg+): Babys Knochen entwickeln sich - viel Milch, Käse, Joghurt!
- PROTEIN (75g+): Baby wächst schnell - mehr Fleisch, Fisch, Eier
- EISEN: noch 12mg aus Nahrung - rotes Fleisch besonders gut
- Omega-3 aus fettem Fisch (Lachs, Makrele) ergänzt das Supplement
- Ballaststoffe für gute Verdauung"""
        else:
            return """Wichtige Nährstoffe für das Dritte Trimester:
✅ Vitamine & Mikronährstoffe: Durch Orthomol Natal abgedeckt

🍽️ Aus der Nahrung wichtig:
- EISEN (15mg+): Vorbereitung auf Geburt - rotes Fleisch, Leber (in Maßen)
- PROTEIN (80g+): Baby's letzter Wachstumsschub
- KALZIUM: Weiterhin viel Milchprodukte
- Omega-3 aus Fisch ergänzt DHA im Supplement
- Ballaststoffe: Helfen bei häufiger Verstopfung (Vollkorn, Obst, Gemüse)"""


# Global profile instance
pregnancy_profile = PregnancyProfile()

