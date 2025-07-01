# debug_form_fields.py
# Run this to see what fields are actually in your DailyJournalForm

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.forms import DailyJournalForm

app = create_app()

with app.app_context():
    form = DailyJournalForm()

    print("=== DailyJournalForm Fields ===")

    # Get all field names
    field_names = [field.name for field in form]

    print(f"Total fields: {len(field_names)}")
    print("\nAll field names:")
    for i, name in enumerate(sorted(field_names), 1):
        print(f"{i:3}. {name}")

    # Check specifically for P12 fields
    p12_fields = [name for name in field_names if 'p12' in name.lower()]
    print(f"\nP12-related fields ({len(p12_fields)}):")
    for field in p12_fields:
        print(f"  - {field}")

    # Check if p12_expected_outcomes exists
    print(f"\np12_expected_outcomes exists: {'p12_expected_outcomes' in field_names}")

    if hasattr(form, 'p12_expected_outcomes'):
        print("✅ form.p12_expected_outcomes attribute exists")
        print(f"Field type: {type(form.p12_expected_outcomes)}")
        print(f"Field label: {form.p12_expected_outcomes.label}")
    else:
        print("❌ form.p12_expected_outcomes attribute does NOT exist")

        # Look for similar field names
        similar = [name for name in field_names if 'outcome' in name.lower() or 'expect' in name.lower()]
        if similar:
            print(f"Similar fields found: {similar}")