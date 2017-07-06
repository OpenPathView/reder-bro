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

var ws = new function(){
    this.ws = null;
    this.userPos = L.marker([0,0], {icon: posIcon});
    var thatUserPos = this.userPos;

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
                // TODO : add map with panorama coordinates and user position
                L.marker([rep.pano.lat, rep.pano.lon]).addTo(this.map);
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
