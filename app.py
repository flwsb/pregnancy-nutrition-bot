"""Streamlit web app for pregnancy nutrition tracking."""
import streamlit as st
import tempfile
import os
from pathlib import Path
from PIL import Image
from openai_service import OpenAIService
from nutrition_db import NutritionDB
from meal_diary import MealDiary
from analyzer import NutritionAnalyzer
from config import OPENAI_API_KEY

# Page config
st.set_page_config(
    page_title="Pregnancy Nutrition Tracker",
    page_icon="🤰",
    layout="wide"
)

# Initialize services
@st.cache_resource
def get_services():
    """Initialize and cache services."""
    return {
        'openai_service': OpenAIService(),
        'nutrition_db': NutritionDB(),
        'meal_diary': MealDiary(),
        'analyzer': NutritionAnalyzer()
    }

services = get_services()
openai_service = services['openai_service']
nutrition_db = services['nutrition_db']
meal_diary = services['meal_diary']
analyzer = services['analyzer']

# Get user ID from session state (or use a default for web app)
if 'user_id' not in st.session_state:
    st.session_state.user_id = 1  # Default user ID for web app

user_id = st.session_state.user_id

# Main title
st.title("🤰 Pregnancy Nutrition Tracker")
st.markdown("Upload meal photos to track your nutrition and get personalized recommendations!")

# Sidebar
with st.sidebar:
    st.header("📊 Quick Actions")
    if st.button("📅 Today's Summary", use_container_width=True):
        st.session_state.show_diary = True
        st.session_state.show_weekly = False
    
    if st.button("📈 Weekly Report", use_container_width=True):
        st.session_state.show_diary = False
        st.session_state.show_weekly = True
    
    st.markdown("---")
    st.markdown("### How to Use")
    st.markdown("""
    1. 📸 Upload a photo of your meal
    2. 🤖 AI analyzes the foods
    3. 📊 Nutrients are automatically logged
    4. 💡 Get personalized recommendations
    """)

# Main content area
tab1, tab2, tab3 = st.tabs(["📸 Log Meal", "📅 Today's Diary", "📈 Weekly Report"])

with tab1:
    st.header("Upload Meal Photo")
    
    uploaded_file = st.file_uploader(
        "Choose a meal image...",
        type=['jpg', 'jpeg', 'png'],
        help="Upload a clear photo of your meal"
    )
    
    if uploaded_file is not None:
        # Display image
        image = Image.open(uploaded_file)
        st.image(image, caption="Your meal", use_container_width=True)
        
        if st.button("🔍 Analyze Meal", type="primary", use_container_width=True):
            with st.spinner("Analyzing your meal... This may take a moment."):
                try:
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                        image.save(tmp_file.name, 'JPEG')
                        tmp_path = tmp_file.name
                    
                    try:
                        # Analyze image
                        result = openai_service.analyze_meal_image(tmp_path)
                        food_items = result["food_items"]
                        
                        # Calculate nutrients
                        nutrients = nutrition_db.estimate_nutrients(food_items)
                        
                        # Save to diary
                        meal_id = meal_diary.add_meal(user_id, food_items, nutrients)
                        
                        # Display results
                        st.success("✅ Meal logged successfully!")
                        
                        st.subheader("📝 Foods Identified")
                        for item in food_items:
                            st.write(f"• **{item['name']}** ({item.get('quantity', 100)}g)")
                        
                        st.subheader("📊 Key Nutrients")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Calories", f"{nutrients.get('calories', 0):.0f} kcal")
                            st.metric("Protein", f"{nutrients.get('protein_g', 0):.1f}g")
                        with col2:
                            st.metric("Iron", f"{nutrients.get('iron_mg', 0):.1f}mg")
                            st.metric("Folate", f"{nutrients.get('folate_mcg', 0):.1f}mcg")
                        with col3:
                            st.metric("Calcium", f"{nutrients.get('calcium_mg', 0):.1f}mg")
                            st.metric("Vitamin C", f"{nutrients.get('vitamin_c_mg', 0):.1f}mg")
                        
                        st.balloons()
                        
                    finally:
                        # Clean up
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                
                except Exception as e:
                    st.error(f"❌ Error analyzing meal: {str(e)}")
                    st.info("Please try again with a clearer image.")

with tab2:
    st.header("📅 Today's Nutrition Summary")
    
    try:
        analysis = analyzer.analyze_daily_intake(user_id)
        summary = analyzer.format_daily_summary(analysis)
        
        # Display summary
        st.markdown(summary)
        
        # Show meals logged today
        meals = meal_diary.get_daily_meals(user_id)
        if meals:
            st.subheader(f"Meals Logged Today ({len(meals)})")
            for meal in meals:
                with st.expander(f"Meal at {meal['timestamp'][:16]}"):
                    st.write("**Foods:**")
                    for item in meal['food_items']:
                        st.write(f"• {item['name']} ({item.get('quantity', 100)}g)")
        else:
            st.info("No meals logged today yet. Upload a meal photo to get started!")
    
    except Exception as e:
        st.error(f"Error loading diary: {str(e)}")

with tab3:
    st.header("📈 Weekly Nutrition Report")
    
    try:
        analysis = analyzer.analyze_weekly_intake(user_id)
        summary = analyzer.format_weekly_summary(analysis)
        
        # Display summary
        st.markdown(summary)
        
        # Show meals logged this week
        meals = meal_diary.get_weekly_meals(user_id)
        if meals:
            st.subheader(f"Meals Logged This Week ({len(meals)})")
            for meal in meals:
                with st.expander(f"Meal at {meal['timestamp'][:16]}"):
                    st.write("**Foods:**")
                    for item in meal['food_items']:
                        st.write(f"• {item['name']} ({item.get('quantity', 100)}g)")
        else:
            st.info("No meals logged this week yet. Upload meal photos to get started!")
    
    except Exception as e:
        st.error(f"Error loading weekly report: {str(e)}")

# Footer
st.markdown("---")
st.markdown("💡 **Tip**: Upload clear, well-lit photos of your meals for best results!")

