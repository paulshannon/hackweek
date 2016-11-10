from django.apps import AppConfig


class AppAppConfig(AppConfig):
    name = 'app'

    def ready(self):
        from .signals import flight_saved, map_session_saved, weather_saved
