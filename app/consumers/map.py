from channels.auth import channel_session_user
from channels.generic.websockets import WebsocketDemultiplexer

from app.gis import bounding_box_to_polygon
from app.models import MapSession


class Demultiplexer(WebsocketDemultiplexer):
    mapping = {
        "map.move": "map.move",
    }

    def connection_groups(self, *args, **kwargs):
        return ["map"]


@channel_session_user
def move(message):
    MapSession.objects.update_or_create(channel=message.reply_channel.name, defaults={
        'zoom': message.content['zoom'],
        'bounds': bounding_box_to_polygon(message.content['bounds']),
    })
