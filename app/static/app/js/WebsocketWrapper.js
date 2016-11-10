var WebsocketWrapper = L.Class.extend({
  ws_scheme: null,
  ws_uri: null,
  socket: null,

  options: {
    ws_path: ""
  },

  initialize: function (options) {
    L.setOptions(this, options);
    this.ws_scheme = window.location.protocol == "https:" ? "wss" : "ws"; // Correctly decide between ws:// and wss://
    this.ws_uri = this.ws_scheme + '://' + window.location.host + this.options.ws_path;

    console.debug("Connecting to " + this.ws_uri);

    this.socket = new ReconnectingWebSocket(this.ws_uri);

    this.socket.onmessage = function (message) {
      var data = JSON.parse(message.data)
      if (data.stream != null) {
        console.debug("StreamMessage: %s", data.stream);
        this.routeStream(data.stream, data.payload);
      }
      else {
        console.debug("Message: %s", message.data);
      }
    }.bind(this);

    this.socket.onopen = function () {
      console.debug("Connected to socket");
    };

    this.socket.onclose = function () {
      console.debug("Disconnected from socket");
    };
  },

  // whenReady: function (callback) {
  //   this.socket.onopen = callback;
  //   if (this.socket.readyState == WebSocket.OPEN) {
  //     callback();
  //   }
  // },

  send: function (stream, payload) {
    console.debug("Sending: %s", stream);
    return this.socket.send(JSON.stringify({'stream': stream, 'payload': payload}));
  },

  setMap: function (map) {
    this.map = map;
  },

  routeStream: function (stream, payload) {
    switch (stream) {
      case 'facility.info':
        this.map.facility(payload);
        break;
      case 'flight.info':
        this.map.flight(payload);
        break;
      case 'weather.info':
        this.map.weather(payload);
        break;
      default:
        this.map.other(payload);
    }
  },

  sendMove: function (bounds, zoom) {
    return this.send('map.move', {'bounds': bounds, 'zoom': zoom});
  }


});
