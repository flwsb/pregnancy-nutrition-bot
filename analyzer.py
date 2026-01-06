"""Analysis and recommendation logic for nutrition tracking."""
from typing import Dict, Tuple
from nutrition_db import NutritionDB
from meal_diary import MealDiary
from openai_service import OpenAIService


class NutritionAnalyzer:
    """Analyzes nutrition intake and generates recommendations."""
    
    def __init__(self):
        """Initialize analyzer with required services."""
        self.nutrition_db = NutritionDB()
        self.meal_diary = MealDiary()
        self.openai_service = OpenAIService()
    
    def analyze_daily_intake(self, user_id: int) -> Dict:
        """
        Analyze daily nutrition intake and identify gaps.
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            Dictionary with analysis results
        """
        requirements = self.nutrition_db.get_daily_requirements()
        totals = self.meal_diary.get_daily_totals(user_id)
        meals = self.meal_diary.get_daily_meals(user_id)
        
        # Calculate gaps
        gaps = {}
        percentages = {}
        for nutrient, required in requirements.items():
            consumed = totals.get(nutrient, 0)
            gap = required - consumed
            gaps[nutrient] = gap
            percentages[nutrient] = (consumed / required * 100) if required > 0 else 0
        
        # Generate recommendations
        missing_nutrients = {k: v for k, v in gaps.items() if v > 0}
        recommendations = self.openai_service.generate_recommendations(
            missing_nutrients, totals, requirements
        )
        
        return {
            "requirements": requirements,
            "totals": totals,
            "gaps": gaps,
            "percentages": percentages,
            "missing_nutrients": missing_nutrients,
            "recommendations": recommendations,
            "meal_count": len(meals)
        }
    
    def analyze_weekly_intake(self, user_id: int) -> Dict:
        """
        Analyze weekly nutrition intake and identify gaps.
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            Dictionary with analysis results
        """
        requirements = self.nutrition_db.get_weekly_requirements()
        totals = self.meal_diary.get_weekly_totals(user_id)
        meals = self.meal_diary.get_weekly_meals(user_id)
        
        # Calculate gaps
        gaps = {}
        percentages = {}
        for nutrient, required in requirements.items():
            consumed = totals.get(nutrient, 0)
            gap = required - consumed
            gaps[nutrient] = gap
            percentages[nutrient] = (consumed / required * 100) if required > 0 else 0
        
        # Generate recommendations
        missing_nutrients = {k: v for k, v in gaps.items() if v > 0}
        recommendations = self.openai_service.generate_recommendations(
            missing_nutrients, totals, requirements
        )
        
        return {
            "requirements": requirements,
            "totals": totals,
            "gaps": gaps,
            "percentages": percentages,
            "missing_nutrients": missing_nutrients,
            "recommendations": recommendations,
            "meal_count": len(meals)
        }
    
    def format_daily_summary(self, analysis: Dict) -> str:
        """
        Format daily analysis as a readable summary.
        
        Args:
            analysis: Analysis results from analyze_daily_intake
        
        Returns:
            Formatted summary text
        """
        totals = analysis["totals"]
        requirements = analysis["requirements"]
        percentages = analysis["percentages"]
        meal_count = analysis["meal_count"]
        
        summary = f"📊 Daily Nutrition Summary ({meal_count} meals logged)\n\n"
        
        # Key nutrients to highlight
        key_nutrients = [
            ("calories", "Calories", ""),
            ("protein_g", "Protein", "g"),
            ("iron_mg", "Iron", "mg"),
            ("folate_mcg", "Folate", "mcg"),
            ("calcium_mg", "Calcium", "mg"),
            ("vitamin_c_mg", "Vitamin C", "mg")
        ]
        
        for nutrient_key, nutrient_name, unit in key_nutrients:
            consumed = totals.get(nutrient_key, 0)
            required = requirements.get(nutrient_key, 0)
            percentage = percentages.get(nutrient_key, 0)
            
            emoji = "✅" if percentage >= 90 else "⚠️" if percentage >= 70 else "❌"
            
            summary += f"{emoji} {nutrient_name}: {consumed:.1f}{unit} / {required:.1f}{unit} ({percentage:.0f}%)\n"
        
        summary += "\n"
        
        if analysis["missing_nutrients"]:
            summary += "💡 Recommendations:\n"
            summary += analysis["recommendations"]
        else:
            summary += "🎉 Great job! You're meeting all your nutritional targets today!"
        
        return summary
    
    def format_weekly_summary(self, analysis: Dict) -> str:
        """
        Format weekly analysis as a readable summary.
        
        Args:
            analysis: Analysis results from analyze_weekly_intake
        
        Returns:
            Formatted summary text
        """
        totals = analysis["totals"]
        requirements = analysis["requirements"]
        percentages = analysis["percentages"]
        meal_count = analysis["meal_count"]
        
        summary = f"📊 Weekly Nutrition Summary ({meal_count} meals logged)\n\n"
        
        # Key nutrients to highlight
        key_nutrients = [
            ("calories", "Calories", ""),
            ("protein_g", "Protein", "g"),
            ("iron_mg", "Iron", "mg"),
            ("folate_mcg", "Folate", "mcg"),
            ("calcium_mg", "Calcium", "mg"),
            ("vitamin_c_mg", "Vitamin C", "mg")
        ]
        
        for nutrient_key, nutrient_name, unit in key_nutrients:
            consumed = totals.get(nutrient_key, 0)
            required = requirements.get(nutrient_key, 0)
            percentage = percentages.get(nutrient_key, 0)
            
            emoji = "✅" if percentage >= 90 else "⚠️" if percentage >= 70 else "❌"
            
            summary += f"{emoji} {nutrient_name}: {consumed:.1f}{unit} / {required:.1f}{unit} ({percentage:.0f}%)\n"
        
        summary += "\n"
        
        if analysis["missing_nutrients"]:
            summary += "💡 Recommendations for next week:\n"
            summary += analysis["recommendations"]
        else:
            summary += "🎉 Excellent! You're meeting all your weekly nutritional targets!"
        
        return summary

