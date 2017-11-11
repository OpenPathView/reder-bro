var qs = function(s){
    return document.querySelector(s);
};

var posIcon = L.icon({
    iconUrl: 'static/images/marker-pos.png',
    shadowUrl: 'static/images/marker-pos-shadow.png',
    iconSize:     [75, 76], // size of the icon
    shadowSize:   [103, 57], // size of the shadow
    iconAnchor:   [37, 71], // point of the icon which will correspond to marker's location
    shadowAnchor: [36, 51],  // the same for the shadow
    popupAnchor:  [-3, -76] // point from which the popup should open relative to the iconAnchor
});

var Chrono = function(el){
    var that = this;
    this.chronoDisplayEl = el;
    this.startDate = new Date();
    this.isRunning = false;
    this.lastAlertTime = null;

    this.reset = function(){
        that.startDate = new Date();
        if(!that.isRunning){
            that.start();
        }
        that.render();
        that.lastAlertTime = null;
    };
    this.getAlertTime = function(){
        return parseInt(document.querySelector("#timeToAlert").value);
    };
    this.render = function(){
        var d = new Date();
        var diffms = d.getTime() - that.startDate.getTime();
        if(diffms > that.getAlertTime()){
            var displayAlert = true;
            if(that.lastAlertTime != null){
                var diffLastAlert = d.getTime() - that.lastAlertTime.getTime();
                displayAlert = !(diffLastAlert < 2*60*1000);
            }
            if( displayAlert ){
                that.lastAlertTime = new Date();
                notify("It's been "+(diffms/1000).toFixed(3)+" s since last picture.");
            }
        }
        that.chronoDisplayEl.innerHTML = (diffms / 1000).toFixed(3);
    };
    this.start = function(){
        that.interval = setInterval(function(){ that.render();}, 50);
        that.isRunning = true;
    };
    this.stop = function(){
        clearInterval(that.interval);
        that.isRunning = false;
    };
    this.toggle = function(){
        if(that.isRunning){
            that.stop();
        }else{
            that.start();
        }
    };
};

function log(msg){
    var d = new Date();
    var log = document.querySelector("#logs");
    log.scrollTop = log.scrollHeight;
    log.innerHTML += "<b> " + d.getHours() + ":"+d.getMinutes()+" : </b> "+msg+" <br>";
}

function soundHey(){
    var player = document.querySelector("#audioPlayer");
    player.currentTime = 0;
    player.play();
}

function notify(message) {
  // Let's check if the browser supports notifications
  if (!("Notification" in window)) {
    alert("This browser does not support system notifications");
  }

  // Let's check whether notification permissions have already been granted
  else if (Notification.permission === "granted") {
    // If it's okay let's create a notification
    var notification = new Notification(message);
    soundHey();
  }

  // Otherwise, we need to ask the user for permission
  else if (Notification.permission !== 'denied') {
    Notification.requestPermission(function (permission) {
      // If the user accepts, let's create a notification
      if (permission === "granted") {
        var notification = new Notification(message);
        soundHey();
      }
    });
  }

  log(message);

  // Finally, if the user has denied notifications and you
  // want to be respectful there is no need to bother them any more.
}

var ws = new function(){
    this.ws = null;
    this.userPos = L.marker([0,0], {icon: posIcon});
    this.chrono = null;
    var thatUserPos = this.userPos;
    var _that_ = this;

    this.openSocket = function(){
        this.ws = new WebSocket(qs("#ws_url").value, "chat");

        this.ws.onopen = function(e){
            //console.log("WebSocket opened, event :");
            //console.log(e);
            qs("#connectionInfos").style.display = "none";
            qs("#controles").style.display = null;

            this.map = L.map('map').setView([48.41416, -4.47197], 13);
            L.tileLayer('/map/{z}/{x}/{y}.png', {
            attribution: 'tmp',
            maxZoom: 19,
            minZoom: 1
            }).addTo(this.map);

            // TODO : add right attribution
            this.map.attributionControl.setPrefix(''); // Don't show the 'Powered by Leaflet' text. Attribution overload
            thatUserPos.addTo(this.map);

            // Timer
            _that_.chrono = new Chrono(document.querySelector("#lastTakenChrono"));
        };

        this.ws.onerror = function(e){
            //console.log("Error, event :");
            //console.log(e);
        };

        window.onbeforeunload = function(){
            this.close();
            alert("WebSocket connexion closed");
        };

        this.ws.onclose = function(e){
            //console.log("WebSocket closed, event :");
            //console.log(e);
            qs("#connectionInfos").style.display = null;
            qs("#controles").style.display = "none";
            this.close();
            alert("WebSocket connexion closed");
        };

        this.ws.onmessage = function(e){
            //console.log(e.data);
            var rep = JSON.parse(e.data);
            //console.log(rep);

            if( rep.hasOwnProperty('pos') ){
                qs("#lat").innerHTML=rep.pos.lat;
                qs("#lon").innerHTML=rep.pos.long;
                qs("#alt").innerHTML=rep.pos.alt;
                qs("#rad").innerHTML=rep.pos.rad;
                var valideData = false;
                var latlng;
                try{
                    latlng = L.latLng(rep.pos.lat, rep.pos.long);
                    valideData = true;
                }
                catch(err)
                {
                    valideData = false;
                }
                if(valideData==true){
                    thatUserPos.setLatLng(latlng);
                    thatUserPos.update();
                }
            }
            else if(rep.hasOwnProperty('config')){
                if (rep.auto == "True"){
                    qs("#mode").value = rep.dist
                }
                else{
                    qs("#mode").value = 0
                }
            }
            else if(rep.hasOwnProperty('pano')){
                if(rep.pano.succes){
                    L.marker([rep.pano.lat, rep.pano.lon]).addTo(this.map);
                    log("Taken");
                    _that_.chrono.reset();
                }else{
                    apnNumber = _that_.goProFailedToCameraList(rep.pano.goProFailed);
                    var errorString = "Following camera failed : ";
                    errorString += apnNumber.join(", ");
                    notify(errorString);
                }
                // '{"pano" : {"lat": "%F", lon:"%F", alt:"%F", rad:"%s"}}'
            }
            else if(rep.hasOwnProperty('succes')){
                if(rep.succes=="false"){
                    alert("echec du serveur")
                }
            }
            // TODO : Add information about failling camera : vibration or sound

        };
    };

    this.goProFailedToCameraList = function(goProFailedString){
        camFailedListApnID = []
        for(var i=0; i<6; i++){
            if(goProFailedString.charAt(i) == '1'){
                camFailedListApnID.push(5-i);
            }
        }
        return camFailedListApnID;
    }

    this.setAutoMode = function(){
        selectedDist = qs("#mode").value
        var data = { set: "automode", dist: selectedDist};
        this.ws.send( JSON.stringify(data) );
    };

    this.turnOn = function(){
        var data = { action: "turnon" };
        this.ws.send( JSON.stringify(data) );
    };

    this.turnOff = function(){
        var data = { action: "turnoff" };
        this.ws.send( JSON.stringify(data) );
    };

    this.goProPowerOff = function(){
        var data = { action: "gopropoweroff" };
        this.ws.send( JSON.stringify(data) );
    };

    this.goProPowerOn = function(){
        var data = { action: "gopropoweron" };
        this.ws.send( JSON.stringify(data) );
    };

    this.takePic = function(){
        var data = { action: "takepic" };
        this.ws.send( JSON.stringify(data) );
    };

}();
