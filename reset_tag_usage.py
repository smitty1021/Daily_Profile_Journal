# Create a script to reset tag usage counts to match actual trade counts
# Save this as reset_tag_usage.py in your project root

from app import create_app, db
from app.models import TagUsageStats, Tag, Trade


def reset_tag_usage_counts():
    """Reset all tag usage counts to match actual trade counts"""
    app = create_app()

    with app.app_context():
        print("🔄 Resetting tag usage counts...")

        # Get all tag usage stats
        all_stats = TagUsageStats.query.all()

        for stat in all_stats:
            # Count actual trades that have this tag for this user
            actual_count = (Trade.query
                            .filter(Trade.user_id == stat.user_id)
                            .filter(Trade.tags.contains(stat.tag))
                            .count())

            if actual_count != stat.usage_count:
                print(f"📊 Tag '{stat.tag.name}' for user {stat.user_id}: {stat.usage_count} → {actual_count}")
                stat.usage_count = actual_count

            # If no trades use this tag, remove the usage stat
            if actual_count == 0:
                print(f"🗑️ Removing unused tag stat for '{stat.tag.name}'")
                db.session.delete(stat)

        try:
            db.session.commit()
            print("✅ Tag usage counts reset successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error resetting counts: {e}")


if __name__ == "__main__":
    reset_tag_usage_counts()