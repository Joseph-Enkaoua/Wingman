from django.apps import AppConfig


class LogbookConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'logbook'
    
    def ready(self):
        import logbook.signals
