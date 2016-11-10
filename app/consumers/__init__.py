from channels.generic.websockets import WebsocketDemultiplexer


class DefaultDemultiplexer(WebsocketDemultiplexer):
    mapping = {}

    def connection_groups(self, *args, **kwargs):
        return []
