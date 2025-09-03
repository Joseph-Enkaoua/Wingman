from django import template
from django.forms import TimeInput

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

@register.inclusion_tag('logbook/time_input_with_button.html')
def time_input_with_button(field):
    """Render a time input field with a button to fill the full flight time"""
    return {
        'field': field,
        'field_id': field.auto_id or field.name
    }
