$(function () {

  $(function () {
    window.socket = new WebsocketWrapper({'ws_path': '/flightplan'});
    socket.onmessage = function (e) {
      console.log(JSON.parse(e.data));
    }

  });

  // var FacilitySocket = Websocket.extend({
  //   sendState: function (acid, state) {
  //     return this.send('flightplan.status',
  //       {
  //         "acid": acid,
  //         "aircraft_type": "A10",
  //         "state": state,
  //         "departure": "CYOW",
  //         "destination": "CYYZ",
  //         "total_eet": "60",
  //       }
  //     );
  //   }
  // });
});