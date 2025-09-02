from django import template

register = template.Library()

@register.filter
def minutes_to_time(minutes):
    """Convert minutes to HH:MM format"""
    if minutes is None or minutes == 0:
        return "00:00"
    
    try:
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
    except (ValueError, TypeError):
        return "00:00"

@register.filter
def minutes_to_hours(minutes):
    """Convert minutes to decimal hours for display"""
    if minutes is None or minutes == 0:
        return "0.0"
    
    try:
        hours = minutes / 60
        return f"{hours:.1f}"
    except (ValueError, TypeError):
        return "0.0"
