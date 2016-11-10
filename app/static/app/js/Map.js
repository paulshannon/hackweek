var AircraftIcon = L.Icon.extend({
  options: {
    iconUrl: '/static/app/img/plane.png',
    shadowUrl: null,
    iconSize: [19, 19],
    iconAnchor: [9, 9],
    popupAnchor: [0, -13]
  }
});

var FacilityIcon = L.Icon.extend({
  options: {
    iconUrl: '/static/app/img/facility.png',
    shadowUrl: null,
    iconSize: [10, 10],
    iconAnchor: [5, 5],
    popupAnchor: [5, 5]
  }
});


var Map = L.Class.extend({
  map: null,

  options: {
    center: [45.4215, -75.6972],
    zoom: 8,
  },

  boundsToBox: function (bounds) {
    // min_x, min_y, max_x, max_y
    return [bounds._southWest.lng, bounds._southWest.lat, bounds._northEast.lng, bounds._northEast.lat];
  },

  initMap: function () {
    this.layers = {
      facilities: L.geoJson(),
      flights: L.geoJson(),
      weather: L.geoJson(),
      temp: L.layerGroup(),
    }

    var overlays = {
      "Facilities": this.layers.facilities,
      "Flights": this.layers.flights,
      "Weather": this.layers.weather,
    };

    var mbAttr = 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, ' +
        '<a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, ' +
        'Imagery © <a href="http://mapbox.com">Mapbox</a>',
      mbUrl = 'https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpandmbXliNDBjZWd2M2x6bDk3c2ZtOTkifQ._QA7i5Mpkd_m30IGElHziw';

    var grayscale = L.tileLayer(mbUrl, {id: 'mapbox.light', attribution: mbAttr});
    var streets = L.tileLayer(mbUrl, {id: 'mapbox.streets', attribution: mbAttr});

    this.map = L.map('map', {
      center: this.options.center,
      zoom: this.options.zoom,
      layers: [
        grayscale,
        this.layers.facilities,
        this.layers.flights,
        this.layers.weather,
        this.layers.temp
      ]
    });

    var baseLayers = {
      "Grayscale": grayscale,
      "Streets": streets
    };

    L.control.layers(baseLayers, overlays, {collapsed: false}).addTo(this.map);

    this.info = L.control({position: 'bottomright'});
    this.info.onAdd = function (map) {
      this.div = L.DomUtil.create('div', 'info');
      this.infoBox = L.DomUtil.create('div', 'infoBox', this.div);
      this.infoStats = L.DomUtil.create('div', 'infoStats', this.div);
      this.infoStats.innerHTML = `
        <h4>Messages</h4>
        Facilities: <span id="facility_stats">0</span><br />
        Flights: <span id="flight_stats">0</span><br />
        Weather: <span id="weather_stats">0</span><br />
        Other: <span id="other_stats">0</span><br />
        `;
      return this.div;
    };
    this.info.addTo(this.map);
    this.hash = new L.Hash(this.map);
  },

  sendPosition: function () {
    this.socket.sendMove(this.boundsToBox(this.map.getBounds()), this.map.getZoom());
  },

  initialize: function (socket, options) {
    L.setOptions(this, options);

    this.socket = socket;
    this.socket.setMap(this);

    this.initMap();
    this.map.on('moveend', this.moveEnd.bind(this));

    this.db = {
      'facility': {},
      'flight': {},
      'weather': {}
    };
    this.stats = {
      facility: $('#facility_stats'),
      flight: $('#flight_stats'),
      weather: $('#weather_stats'),
      other: $('#other_stats'),
    }
  },

  moveEnd: function (event) {
    this.sendPosition();
    this.layers.temp.clearLayers();
  },

  flight: function (flight) {
    this.stats.flight.html(parseInt(this.stats.flight.html()) + 1);
    // Remove existing, drawn always
    var existing = this.db['flight'][flight.id]

    if (existing != undefined) {
      if (this.mouseover == 'flight') {
        this.layers.temp.clearLayers();
      }
      this.layers.flights.removeLayer(existing.properties.layer);
    }

    if (flight.properties.status == 'active') {
      flight.mouseover = function (e) {
        this.mouseover = 'flight';
        this.info.infoBox.innerHTML = `
        <b>${flight.id}</b><br />
        Departure: ${flight.properties.departureFacility}<br />
        Arrival: ${flight.properties.arrivalFacility}<br />
        Responsibility: ${flight.properties.facility}<br />
        `;
        this.layers.temp.addLayer(flight.properties.remainingLayer);
      }.bind(this);

      flight.mouseout = function (e) {
        this.info.infoBox.innerHTML = '';
        this.layers.temp.removeLayer(flight.properties.remainingLayer);
        this.mouseover = null;
      }.bind(this);

      flight.properties.layer = L.geoJSON(flight, {
        pointToLayer: function (feature, latlng) {
          return L.marker(latlng, {
            icon: new AircraftIcon(),
            rotationAngle: feature.properties.heading
          });
        }.bind(this),
        onEachFeature: function (feature, layer) {
          layer.on({
            mouseover: feature.mouseover,
            mouseout: feature.mouseout
          });
        }.bind(this)
      });
      var f = flight.properties;
      flight.properties.layer.bindPopup(`<p>
        ${flight.id} @ ${f.heading}°<br />
        ${f.departureFacility} - ${f.arrivalFacility}<br />
        ${f.status} with ${f.facility}
        </p>`);
      flight.properties.flightPathLayer = L.geoJSON(flight.properties.flightPath);
      flight.properties.remainingLayer = L.geoJSON(flight.properties.remaining);

      this.layers.flights.addLayer(flight.properties.layer);
    }
    this.db['flight'][flight.id] = flight;


  },

  facility: function (facility) {
    this.stats.facility.html(parseInt(this.stats.facility.html()) + 1);
    // Always on map once drawn
    var existing = this.db['facility'][facility.id];
    if (existing == undefined) {

      facility.mouseover = function (e) {
        this.mouseover = 'facility';
        this.info.infoBox.innerHTML = `<b>${facility.id}</b><br />${facility.properties.name}`;
        this.layers.temp.addLayer(facility.properties.responsibilityLayer);
      }.bind(this);

      facility.mouseout = function (e) {
        this.info.infoBox.innerHTML = '';
        this.layers.temp.removeLayer(facility.properties.responsibilityLayer);
        this.mouseover = null;
      }.bind(this);

      facility.properties.responsibilityLayer = L.geoJSON(facility.properties.responsibility, {
        style: function (feature) {
          return {color: '#AAA', weight: 1};
        }.bind(this)
      });

      facility.properties.layer = L.geoJSON(facility, {
        pointToLayer: function (feature, latlng) {
          return L.marker(latlng, {
            icon: new FacilityIcon()
          });
        }.bind(this),
        onEachFeature: function (feature, layer) {
          layer.on({
            mouseover: feature.mouseover,
            mouseout: feature.mouseout
          });
        }.bind(this)
      });

      this.layers.facilities.addLayer(facility.properties.layer);
      this.db['facility'][facility.id] = facility;
    }
  },

  weather: function (weather) {
    this.stats.weather.html(parseInt(this.stats.weather.html()) + 1);
    var existing = this.db['weather'][weather.id];
    if (existing != undefined) {
      this.layers.weather.removeLayer(existing.properties.layer);
    }
    if (weather.remove != true) {
      weather.properties.layer = L.geoJSON(weather, {
        style: function (feature) {
          return {color: '#e22904', weight: 1};
        }.bind(this)
      });

      this.layers.weather.addLayer(weather.properties.layer);
      this.db['weather'][weather.id] = weather;
    }
  },

  other: function (payload) {
    this.stats.other.html(parseInt(this.stats.other.html()) + 1);
    console.log(payload);
  }

});

