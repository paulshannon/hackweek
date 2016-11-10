$(function () {
  window.socket = new WebsocketWrapper({'ws_path': '/app/map'});
  window.map = new Map(socket);

  setTimeout(function () {
    map.sendPosition();
  }, 1000);

});