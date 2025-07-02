#!/usr/bin/env python3
"""
Populate P12 Scenarios with Trading Model Recommendations
=========================================================

This script updates existing P12 scenarios with model recommendations
based on Random's (Matt Mickey) methodology.

Run this after updating the P12Scenario model to add the new fields.

Usage: python populate_p12_model_recommendations.py
"""

import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import P12Scenario


def populate_model_recommendations():
    """Add model recommendations to existing P12 scenarios."""

    app = create_app()

    with app.app_context():
        print("🔧 Populating P12 scenarios with model recommendations...")

        # Define model recommendations for each scenario based on Random's teachings
        scenario_recommendations = {
            1: {
                'models_to_activate': ['HOD/LOD Reversal', 'P12 Scenario-Based'],
                'models_to_avoid': ['0930 Opening Snap'],
                'risk_guidance': 'Use standard 0.35% stop loss. This scenario has clear rejection levels.',
                'preferred_timeframes': ['5-minute', '15-minute'],
                'key_considerations': 'Watch for clean rejection at P12 Mid. Volume should support the rejection. Look for follow-through after initial bounce.'
            },
            2: {
                'models_to_activate': ['P12 Scenario-Based', 'Quarterly & 05 Box'],
                'models_to_avoid': ['Captain Backtest'],
                'risk_guidance': 'Tighter stops may be needed due to range-bound nature. Consider 0.25% risk.',
                'preferred_timeframes': ['5-minute', '15-minute', '1-hour'],
                'key_considerations': 'Respect the P12 range boundaries. This is often a Range 1 or Range 2 day setup. Watch for time-based exits.'
            },
            3: {
                'models_to_activate': ['HOD/LOD Reversal', 'P12 Scenario-Based', 'Midnight Open Retracement'],
                'models_to_avoid': [],
                'risk_guidance': 'Standard risk management applies. 0.35% stop loss with potential for 0.5% targets.',
                'preferred_timeframes': ['5-minute', '15-minute'],
                'key_considerations': 'Strong directional bias scenario. Look for momentum continuation. Previous session high/low likely to be tested.'
            },
            4: {
                'models_to_activate': ['P12 Scenario-Based', 'Captain Backtest'],
                'models_to_avoid': ['0930 Opening Snap'],
                'risk_guidance': 'Extended moves require wider stops. Consider 0.5% risk for extended targets.',
                'preferred_timeframes': ['15-minute', '1-hour'],
                'key_considerations': 'Strong trend continuation expected. Look for dynamic support/resistance at breached P12 levels. Extended daily targets possible.'
            },
            5: {
                'models_to_activate': ['0930 Opening Snap', 'Quarterly & 05 Box'],
                'models_to_avoid': ['P12 Scenario-Based', 'HOD/LOD Reversal'],
                'risk_guidance': 'Choppy conditions require tighter risk management. Use 0.25% stops and be quick to exit.',
                'preferred_timeframes': ['5-minute', '15-minute'],
                'key_considerations': 'Avoid P12-based trades. Focus on post-9:30 setups. Expect both HOD and LOD to form during RTH. Range 1 day likely.'
            }
        }

        updated_count = 0

        try:
            # Get all existing scenarios
            scenarios = P12Scenario.query.all()

            for scenario in scenarios:
                if scenario.scenario_number in scenario_recommendations:
                    rec = scenario_recommendations[scenario.scenario_number]

                    # Update the scenario with model recommendations
                    scenario.models_to_activate = rec['models_to_activate']
                    scenario.models_to_avoid = rec['models_to_avoid']
                    scenario.risk_guidance = rec['risk_guidance']
                    scenario.preferred_timeframes = rec['preferred_timeframes']
                    scenario.key_considerations = rec['key_considerations']
                    scenario.updated_date = datetime.utcnow()

                    updated_count += 1
                    print(f"✅ Updated Scenario {scenario.scenario_number}: {scenario.scenario_name}")
                    print(f"   - Models to activate: {', '.join(rec['models_to_activate'])}")
                    print(
                        f"   - Models to avoid: {', '.join(rec['models_to_avoid']) if rec['models_to_avoid'] else 'None'}")
                    print(f"   - Preferred timeframes: {', '.join(rec['preferred_timeframes'])}")
                    print()

            # Commit all changes
            db.session.commit()
            print(f"🎉 Successfully updated {updated_count} P12 scenarios with model recommendations!")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error updating scenarios: {e}")
            raise


def verify_trading_models_exist():
    """Verify that the referenced trading models exist in the database."""

    app = create_app()

    with app.app_context():
        from app.models import TradingModel

        print("🔍 Verifying trading models exist...")

        # All models referenced in the recommendations
        required_models = [
            '0930 Opening Snap',
            'HOD/LOD Reversal',
            'Captain Backtest',
            'P12 Scenario-Based',
            'Quarterly & 05 Box',
            'Midnight Open Retracement'
        ]

        existing_models = TradingModel.query.filter(
            TradingModel.name.in_(required_models)
        ).all()

        existing_names = [model.name for model in existing_models]
        missing_models = [name for name in required_models if name not in existing_names]

        print(f"✅ Found {len(existing_models)} of {len(required_models)} required models")

        if missing_models:
            print("⚠️  Missing trading models:")
            for model in missing_models:
                print(f"   - {model}")
            print("\nPlease run the trading models creation script first!")
            return False
        else:
            print("✅ All required trading models found!")
            return True


if __name__ == "__main__":
    print("P12 Scenario Model Recommendations Populator")
    print("=" * 50)

    try:
        # First verify trading models exist
        if verify_trading_models_exist():
            print()
            # Then populate the scenario recommendations
            populate_model_recommendations()
        else:
            print("\n❌ Cannot proceed without all trading models. Please create them first.")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Script failed: {e}")
        sys.exit(1)