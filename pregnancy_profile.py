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
        
        return f"""SCHWANGERSCHAFTSPROFIL:
- Alter: {self.age} Jahre
- Gewicht: {self.weight_kg} kg
- Gesundheitszustand: {self.health_status}
- Aktuelle Schwangerschaftswoche: {week}
- Trimester: {trimester_name} Trimester (Trimester {trimester})
- Errechneter Geburtstermin: {self.due_date.strftime('%d.%m.%Y')}"""

    def get_adjusted_requirements(self) -> Dict[str, float]:
        """
        Get nutrition requirements adjusted for pregnancy stage.
        Requirements vary by trimester.
        """
        week = self.get_current_week()
        trimester = self.get_trimester()
        
        # Base requirements for pregnancy
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
    
    def get_trimester_focus_nutrients(self) -> str:
        """Get key nutrients to focus on for current trimester (in German)."""
        trimester = self.get_trimester()
        
        if trimester == 1:
            return """Wichtige Nährstoffe für das Erste Trimester:
- FOLSÄURE (600mcg): Kritisch für die Entwicklung des Neuralrohrs
- Vitamin B6: Hilft gegen Übelkeit
- Eisen: Aufbau der Blutversorgung
- Zink: Zellentwicklung
- Kleine, häufige Mahlzeiten können bei Übelkeit helfen"""
        elif trimester == 2:
            return """Wichtige Nährstoffe für das Zweite Trimester:
- KALZIUM (1000mg): Babys Knochen entwickeln sich
- Vitamin D: Hilft bei der Kalziumaufnahme
- PROTEIN (75g+): Baby wächst schnell
- Eisen: Erhöhtes Blutvolumen
- Omega-3: Gehirnentwicklung"""
        else:
            return """Wichtige Nährstoffe für das Dritte Trimester:
- EISEN (30mg): Vorbereitung auf die Geburt, Anämie vorbeugen
- PROTEIN (80g+): Baby's letzter Wachstumsschub
- Kalzium: Baby speichert Kalzium für Knochen
- DHA/Omega-3: Gehirnentwicklung geht weiter
- Ballaststoffe: Helfen bei häufiger Verstopfung"""


# Global profile instance
pregnancy_profile = PregnancyProfile()

