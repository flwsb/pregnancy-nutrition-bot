"""Pregnancy profile and personalized nutrition requirements."""
from datetime import datetime, date
from typing import Dict, Optional


class PregnancyProfile:
    """Stores and calculates pregnancy-specific information."""
    
    def __init__(self):
        """Initialize with user's pregnancy data."""
        # Personal information
        self.age = 31
        self.weight_kg = 63
        self.height_cm = None  # Can be added if needed
        self.health_status = "healthy, good shape"
        
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
        trimester_name = self.get_trimester_name()
        
        return f"""PREGNANCY PROFILE:
- Age: {self.age} years old
- Weight: {self.weight_kg} kg
- Health status: {self.health_status}
- Current pregnancy week: {week}
- Trimester: {trimester_name} trimester (trimester {trimester})
- Due date: {self.due_date.strftime('%B %d, %Y')}"""

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
        """Get key nutrients to focus on for current trimester."""
        trimester = self.get_trimester()
        
        if trimester == 1:
            return """Key nutrients for First Trimester:
- FOLATE (600mcg): Critical for baby's neural tube development
- Vitamin B6: Helps with nausea
- Iron: Building blood supply
- Zinc: Cell development
- Small, frequent meals may help with nausea"""
        elif trimester == 2:
            return """Key nutrients for Second Trimester:
- CALCIUM (1000mg): Baby's bones are developing
- Vitamin D: Helps calcium absorption
- PROTEIN (75g+): Baby is growing rapidly
- Iron: Increased blood volume
- Omega-3: Brain development"""
        else:
            return """Key nutrients for Third Trimester:
- IRON (30mg): Preparing for delivery, preventing anemia
- PROTEIN (80g+): Baby's final growth spurt
- Calcium: Baby storing calcium for bones
- DHA/Omega-3: Brain development continues
- Fiber: Helps with common constipation"""


# Global profile instance
pregnancy_profile = PregnancyProfile()

