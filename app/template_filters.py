def get_tag_color_class(tag_name):
    """Template filter for tag color classes"""
    good_performance_tags = {
        "Front Run", "Confirmation", "Retest", "Proper Stop",
        "Let Run", "Partial Profit", "Disciplined", "Patient",
        "Calm", "Confident", "Followed Plan"
    }

    bad_performance_tags = {
        "Chased Entry", "Late Entry", "Moved Stop", "Cut Short",
        "FOMO", "Revenge Trading", "Impulsive", "Anxious",
        "Broke Rules", "Overconfident"
    }

    if tag_name in good_performance_tags:
        return "tag-good"
    elif tag_name in bad_performance_tags:
        return "tag-bad"
    else:
        return "tag-neutral"


def register_template_filters(app):
    """Register custom template filters"""
    app.jinja_env.filters['tag_color'] = get_tag_color_class