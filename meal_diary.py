"""Meal diary database operations using SQLite."""
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from config import DATABASE_PATH


class MealDiary:
    """Manages meal diary database operations."""
    
    def __init__(self):
        """Initialize database connection and create tables if needed."""
        self.db_path = DATABASE_PATH
        self._init_database()
    
    def _init_database(self):
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                timestamp DATETIME NOT NULL,
                food_items TEXT NOT NULL,
                nutrients TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_meal(self, user_id: int, food_items: List[Dict], nutrients: Dict[str, float], 
                 meal_timestamp: Optional[datetime] = None) -> int:
        """
        Add a meal to the diary.
        
        Args:
            user_id: Telegram user ID
            food_items: List of identified food items
            nutrients: Calculated nutrient values
            meal_timestamp: Optional custom timestamp for the meal (defaults to now)
        
        Returns:
            Meal ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        import json
        food_items_json = json.dumps(food_items)
        nutrients_json = json.dumps(nutrients)
        
        # Use custom timestamp if provided, otherwise use current time
        if meal_timestamp is None:
            meal_timestamp = datetime.now()
        
        cursor.execute("""
            INSERT INTO meals (user_id, timestamp, food_items, nutrients)
            VALUES (?, ?, ?, ?)
        """, (user_id, meal_timestamp.isoformat(), food_items_json, nutrients_json))
        
        meal_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return meal_id
    
    def get_daily_meals(self, user_id: int, date: Optional[datetime] = None) -> List[Dict]:
        """
        Get all meals for a user on a specific date.
        
        Args:
            user_id: Telegram user ID
            date: Date to query (defaults to today)
        
        Returns:
            List of meal dictionaries
        """
        if date is None:
            date = datetime.now()
        
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, food_items, nutrients
            FROM meals
            WHERE user_id = ? AND timestamp >= ? AND timestamp < ?
            ORDER BY timestamp ASC
        """, (user_id, start_date.isoformat(), end_date.isoformat()))
        
        rows = cursor.fetchall()
        conn.close()
        
        import json
        meals = []
        for row in rows:
            meals.append({
                "id": row[0],
                "timestamp": row[1],
                "food_items": json.loads(row[2]),
                "nutrients": json.loads(row[3])
            })
        
        return meals
    
    def get_weekly_meals(self, user_id: int, end_date: Optional[datetime] = None) -> List[Dict]:
        """
        Get all meals for a user in the past week.
        
        Args:
            user_id: Telegram user ID
            end_date: End date for the week (defaults to today)
        
        Returns:
            List of meal dictionaries
        """
        if end_date is None:
            end_date = datetime.now()
        
        start_date = end_date - timedelta(days=7)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, food_items, nutrients
            FROM meals
            WHERE user_id = ? AND timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp ASC
        """, (user_id, start_date.isoformat(), end_date.isoformat()))
        
        rows = cursor.fetchall()
        conn.close()
        
        import json
        meals = []
        for row in rows:
            meals.append({
                "id": row[0],
                "timestamp": row[1],
                "food_items": json.loads(row[2]),
                "nutrients": json.loads(row[3])
            })
        
        return meals
    
    def get_daily_totals(self, user_id: int, date: Optional[datetime] = None) -> Dict[str, float]:
        """
        Calculate total nutrients consumed in a day.
        
        Args:
            user_id: Telegram user ID
            date: Date to query (defaults to today)
        
        Returns:
            Dictionary of total nutrient values
        """
        meals = self.get_daily_meals(user_id, date)
        
        totals = {
            "calories": 0,
            "protein_g": 0,
            "carbohydrates_g": 0,
            "fiber_g": 0,
            "fat_g": 0,
            "folate_mcg": 0,
            "iron_mg": 0,
            "calcium_mg": 0,
            "vitamin_d_iu": 0,
            "vitamin_c_mg": 0,
            "vitamin_a_mcg": 0,
            "vitamin_b12_mcg": 0,
            "zinc_mg": 0,
            "omega3_g": 0
        }
        
        for meal in meals:
            nutrients = meal["nutrients"]
            for nutrient, value in nutrients.items():
                if nutrient in totals:
                    totals[nutrient] += value
        
        return totals
    
    def get_weekly_totals(self, user_id: int, end_date: Optional[datetime] = None) -> Dict[str, float]:
        """
        Calculate total nutrients consumed in the past week.
        
        Args:
            user_id: Telegram user ID
            end_date: End date for the week (defaults to today)
        
        Returns:
            Dictionary of total nutrient values
        """
        meals = self.get_weekly_meals(user_id, end_date)
        
        totals = {
            "calories": 0,
            "protein_g": 0,
            "carbohydrates_g": 0,
            "fiber_g": 0,
            "fat_g": 0,
            "folate_mcg": 0,
            "iron_mg": 0,
            "calcium_mg": 0,
            "vitamin_d_iu": 0,
            "vitamin_c_mg": 0,
            "vitamin_a_mcg": 0,
            "vitamin_b12_mcg": 0,
            "zinc_mg": 0,
            "omega3_g": 0
        }
        
        for meal in meals:
            nutrients = meal["nutrients"]
            for nutrient, value in nutrients.items():
                if nutrient in totals:
                    totals[nutrient] += value
        
        return totals

