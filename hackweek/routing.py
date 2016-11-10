from channels import route, route_class

from app.consumers import DefaultDemultiplexer, flightplan, map

channel_routing = [

    route_class(flightplan.Demultiplexer, path=r'^/flightplan'),
    route('flightplan.state', flightplan.state),
    route('flightplan.simulate', flightplan.simulate),

    route_class(map.Demultiplexer, path=r'^/app/map'),
    route("map.move", map.move),

    route_class(DefaultDemultiplexer),
]
