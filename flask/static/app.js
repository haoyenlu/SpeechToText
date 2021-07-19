URL = window.URL || window.webkitURL;

var gumStream;
var rec;
var source;

var getResponse = true

var AudioContext = window.AudioContext || window.webkitAudioContext;
var audioContext;
var processor;

var recordBtn = document.getElementById('recordBtn');
var stopBtn = document.getElementById('stopBtn');
var response = document.getElementById('response');

recordBtn.addEventListener("click",startRecording);
stopBtn.addEventListener("click",stopRecording);

var namespace = '/test';
var socket = null;


function startRecording() { 
    console.log("recordBtn clicked");
    // Connect to server when record button clicked
    if (socket == null){
        socket = io.connect('http://' + document.domain + ':' + location.port + namespace)
        socket.on('connect',function(){
            console.log("connect to: "+ 'http://' + document.domain + ':' + location.port + namespace);
        })
        socket.on('reply',function(msg){
            console.log("Server reply: "+ msg);
        })
        socket.on('disconnect',function(){
            console.log('disconnect to server.')
        })
        socket.on('transcription',function(data){
            let child = response.lastChild;
            if (child == null || child.classList.contains('is_final')){
                let newChild = document.createElement("div");
                let p = document.createElement("p");
                p.innerHTML = data["transcription"];
                newChild.append(p);
                response.append(newChild);
            } else {
                let p = child.children[0];
                p.innerHTML = data["transcription"];
                if (data["is_final"]){
                    child.classList.add("is_final");
                }
            }
        })
        socket.on('result',function(data){
            console.log(data);
            let child = $('#response div:not(.get_result) ').first()
            let p = document.createElement("p");
            p.innerHTML = "<b>Google Result:</b>" + data["google_result"] + "<br/> <b>IBM Result:</b>" + data["ibm_result"] + "<br/><b>Houndify Result:</b>" + data["houndify_result"] + "<br/><b>Wit Result:</b>" + data["wit_result"];
            p.setAttribute("style","background-color:yellow");
            child.append(p);
            child.addClass("get_result");
        })
    } else {
        socket.disconnect();
        socket.connect();
    }

    var constraints = {audio:true,video:false};

    recordBtn.disabled = true;
    stopBtn.disabled = false;

    navigator.mediaDevices.getUserMedia(constraints).then(function(stream){
        console.log("getUserMedia available.");
        audioContext = new AudioContext();
        console.log("audio context created.");
        sampleRate = audioContext.sampleRate;
        socket.emit('sample_rate',sampleRate);
        socket.emit('start_recording');

        let bufferSize = 1024 * 16;
        processor = audioContext.createScriptProcessor(bufferSize,1,1); // 1 input channel and 1 output channel
        processor.connect(audioContext.destination);

        gumStream = stream;
        source = audioContext.createMediaStreamSource(stream);
        source.connect(processor);

        processor.onaudioprocess = e => {
            const left = e.inputBuffer.getChannelData(0);
            const left16 = convertFloat32ToInt16(left);
            socket.emit('micBinaryStream',left16);
        }
    })
}

function stopRecording() {
    console.log("stopBtn clicked");

    stopBtn.disabled = true;
    recordBtn.disabled = false;


    gumStream.getAudioTracks()[0].stop();
    audioContext.close();
    socket.emit('stop_recording');

}


function createDownloadLink(blob){
    var url = URL.createObjectURL(blob);
    var au = document.createElement('audio');
    var li = document.createElement('li');
    var link = document.createElement('a');

    var filename = new Date().toISOString();

    au.controls = true;
    au.src = url;

    link.href = url;
    link.download = filename+".wav";
    link.innerHTML = "Save";

    li.appendChild(au);

    li.appendChild(document.createTextNode(filename+".wav"));

    li.appendChild(link);

    document.getElementById("recordingList").appendChild(li);
}

function convertFloat32ToInt16(buffer) {
    let l = buffer.length;
    const buf = new Int16Array(l / 3);

    while (l--) {
      if (l % 3 === 0) {
        buf[l / 3] = buffer[l] * 0xFFFF;
      }
    }
    return buf.buffer;
  }