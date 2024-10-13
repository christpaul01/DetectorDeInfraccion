from django.apps import AppConfig

class CamarasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'camaras'

    def ready(self):
        # Import and register signals inside the ready method
        from .signals import register_signals
        register_signals()
