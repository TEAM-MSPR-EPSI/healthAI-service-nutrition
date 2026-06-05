import asyncio

from app.models.schemas import DietEnum, MealPlanRequest, ObjectiveEnum, UserProfile
from app.routes import meal_plan


def test_generate_meal_plan_builds_weekly_plan(monkeypatch) -> None:
    saved_payload = {}

    def fake_save_meal_plan(user_id, user_profile, plan):
        saved_payload["user_id"] = user_id
        saved_payload["user_profile"] = user_profile
        saved_payload["plan"] = plan
        return "meal-plan-id"

    monkeypatch.setattr(meal_plan, "save_meal_plan", fake_save_meal_plan)

    request = MealPlanRequest(
        user_id=42,
        user_profile=UserProfile(
            objective=ObjectiveEnum.muscle_gain,
            gender="male",
            diet=DietEnum.vegan,
        ),
        days=2,
        meals_per_day=4,
    )

    response = asyncio.run(meal_plan.generate_meal_plan(request))

    assert response.user_id == 42
    assert len(response.plan) == 2
    assert response.plan[0].meals[0].name == "Porridge protéiné"
    assert response.plan[0].meals[-1].type == "snack"
    assert any("protéines végétales" in note for note in response.weekly_notes)
    assert saved_payload["user_id"] == 42
    assert saved_payload["user_profile"]["objective"] == "muscle_gain"
    assert len(saved_payload["plan"]) == 2