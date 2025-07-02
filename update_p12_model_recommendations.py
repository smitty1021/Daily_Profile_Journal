# Create this file: update_p12_model_recommendations.py
# Run this after adding the new fields to populate existing scenarios

from app import create_app, db
from app.models import P12Scenario


def update_scenario_recommendations():
    """Update existing P12 scenarios with model recommendations."""
    app = create_app()

    with app.app_context():
        print("🔄 Updating P12 scenarios with model recommendations...")

        # Model recommendations based on Random's teachings
        scenario_recommendations = {
            1: {  # P12 Mid Rejection, Stay Outside
                'models_to_activate': ["0930 Opening Snap", "P12 Scenario-Based", "Captain Backtest"],
                'models_to_avoid': ["HOD/LOD Reversal"],
                'risk_guidance': "2.5% - 5% risk (higher confidence due to clear direction)",
                'preferred_timeframes': ["5m", "15m", "1h"],
                'key_considerations': "Strong directional bias established. HOD/LOD likely already in. Look for trend continuation patterns."
            },
            2: {  # Look Outside P12 and Fail
                'models_to_activate': ["HOD/LOD Reversal", "P12 Scenario-Based", "Quarterly & 05 Box"],
                'models_to_avoid': ["Captain Backtest"],
                'risk_guidance': "2.5% - 7% risk (good reversal setup)",
                'preferred_timeframes': ["1m", "5m", "15m"],
                'key_considerations': "Failed breakout scenario. HOD/LOD likely set by the 'look outside' move. Strong reversal potential."
            },
            3: {  # Range Between P12 Mid and Extreme, Then Breakout
                'models_to_activate': ["P12 Scenario-Based", "Quarterly & 05 Box", "0930 Opening Snap"],
                'models_to_avoid': [],
                'risk_guidance': "2.5% - 5% risk (wait for clear breakout confirmation)",
                'preferred_timeframes': ["5m", "15m"],
                'key_considerations': "Wait for clear breakout direction. HOD/LOD likely already established. Breakout direction indicates session bias."
            },
            4: {  # Look and Stay Outside P12
                'models_to_activate': ["Captain Backtest", "P12 Scenario-Based", "0930 Opening Snap"],
                'models_to_avoid': ["HOD/LOD Reversal"],
                'risk_guidance': "5% - 10% risk (A+ trend continuation setups)",
                'preferred_timeframes': ["15m", "1h", "4h"],
                'key_considerations': "Strong trend day. HOD/LOD likely not in. Expect significant continuation. Use P12 level as dynamic support/resistance."
            },
            5: {  # Swiping the Mid - Expect HOD/LOD in RTH
                'models_to_activate': ["HOD/LOD Reversal", "Quarterly & 05 Box", "0930 Opening Snap"],
                'models_to_avoid': ["Captain Backtest"],
                'risk_guidance': "2.5% risk (lower due to choppy conditions)",
                'preferred_timeframes': ["1m", "5m"],
                'key_considerations': "Choppy conditions. Both HOD and LOD expected in RTH. Avoid P12-based trades. Focus on post-09:30 setups."
            }
        }

        updated_count = 0
        for scenario_number, recommendations in scenario_recommendations.items():
            scenario = P12Scenario.query.filter_by(scenario_number=scenario_number).first()
            if scenario:
                scenario.models_to_activate = recommendations['models_to_activate']
                scenario.models_to_avoid = recommendations['models_to_avoid']
                scenario.risk_guidance = recommendations['risk_guidance']
                scenario.preferred_timeframes = recommendations['preferred_timeframes']
                scenario.key_considerations = recommendations['key_considerations']
                updated_count += 1
                print(f"✅ Updated Scenario {scenario_number}: {scenario.scenario_name}")

        try:
            db.session.commit()
            print(f"🎉 Successfully updated {updated_count} scenarios with model recommendations!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error updating scenarios: {e}")
            raise


if __name__ == "__main__":
    update_scenario_recommendations()