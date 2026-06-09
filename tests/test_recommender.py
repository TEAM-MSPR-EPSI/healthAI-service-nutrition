from app.models.schemas import ObjectiveEnum, UserProfile
from app.services.recommender import analyze_nutritional_balance


def test_analyze_nutritional_balance_handles_zero_calories() -> None:
    profile = UserProfile(objective=ObjectiveEnum.maintenance, gender="female")

    result = analyze_nutritional_balance(0, 0, 0, 0, profile)

    assert result["target_calories"] == 1800
    assert result["imbalances"] == []
    assert result["suggestions"] == [
        "Impossible de calculer les macros : aucune calorie détectée."
    ]
    assert result["macros_ratios"] == {"protein_pct": 0, "carbs_pct": 0, "fat_pct": 0}


def test_analyze_nutritional_balance_flags_multiple_imbalances() -> None:
    profile = UserProfile(objective=ObjectiveEnum.weight_loss, gender="male")

    result = analyze_nutritional_balance(800, 20, 20, 40, profile)

    assert "Déficit en protéines" in result["imbalances"]
    assert "Déficit en glucides" in result["imbalances"]
    assert "Excès de lipides" in result["imbalances"]
    assert any("protéines" in suggestion for suggestion in result["suggestions"])
    assert any("glucides" in suggestion for suggestion in result["suggestions"])
    assert any("graisses" in suggestion for suggestion in result["suggestions"])
    assert any("40%" in suggestion for suggestion in result["suggestions"])