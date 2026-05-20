from pydantic import BaseModel
from typing import Optional
from enum import Enum


class ObjectiveEnum(str, Enum):
    weight_loss = "weight_loss"
    muscle_gain = "muscle_gain"
    endurance = "endurance"
    maintenance = "maintenance"


class DietEnum(str, Enum):
    vegan = "vegan"
    vegetarian = "vegetarian"
    pescatarian = "pescatarian"
    gluten_free = "gluten_free"
    lactose_free = "lactose_free"
    halal = "halal"
    kosher = "kosher"
    none = "none"


class UserProfile(BaseModel):
    objective: ObjectiveEnum = ObjectiveEnum.maintenance
    gender: str = "male"
    age: Optional[int] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    diet: DietEnum = DietEnum.none
    allergies: list[str] = []
    budget: Optional[str] = None  # "low", "medium", "high"


class FoodItem(BaseModel):
    name: str
    confidence: float
    portion_g: float = 100.0
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None


class MealAnalysisResponse(BaseModel):
    detected_foods: list[FoodItem]
    total_calories: float
    target_calories: Optional[float] = None
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    imbalances: list[str]
    suggestions: list[str]
    macros_ratios: dict


class MealPlanRequest(BaseModel):
    days: int = 7
    meals_per_day: int = 3


class Meal(BaseModel):
    name: str
    type: str
    foods: list[str]
    estimated_calories: float
    prep_time_min: int


class DayPlan(BaseModel):
    day: int
    meals: list[Meal]
    total_calories: float


class MealPlanResponse(BaseModel):
    user_id: int
    user_profile: UserProfile
    plan: list[DayPlan]
    weekly_notes: list[str]
