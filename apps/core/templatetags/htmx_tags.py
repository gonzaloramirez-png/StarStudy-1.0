from django import template

register = template.Library()


@register.simple_tag
def htmx_trigger(event_name, detail=None):
    """
    Genera header HX-Trigger para respuesta HTMX.
    Uso: {% htmx_trigger 'toast' '{"message": "Tarea completada", "type": "success"}' %}
    """
    if detail:
        return f'{event_name}: {detail}'
    return event_name


@register.simple_tag
def htmx_trigger_after_swap(event_name, detail=None):
    """Header HX-Trigger-After-Swap (se dispara después del swap)."""
    if detail:
        return f'{event_name}: {detail}'
    return event_name


@register.simple_tag
def htmx_trigger_after_settle(event_name, detail=None):
    """Header HX-Trigger-After-Settle (se dispara después de settle)."""
    if detail:
        return f'{event_name}: {detail}'
    return event_name


@register.inclusion_tag('partials/_toast.html')
def render_toast(message, type='info', icon=''):
    """Incluye partial de toast para respuestas HTMX."""
    icons = {
        'success': '<i class="bi bi-check-circle me-2" aria-hidden="true"></i>',
        'error': '<i class="bi bi-exclamation-triangle me-2" aria-hidden="true"></i>',
        'warning': '<i class="bi bi-exclamation-circle me-2" aria-hidden="true"></i>',
        'info': '<i class="bi bi-info-circle me-2" aria-hidden="true"></i>',
    }
    return {
        'message': message,
        'type': type,
        'icon': icon or icons.get(type, icons['info']),
    }