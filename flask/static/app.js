var namespace = '/test';
var socket = null;

URL = window.URL || window.webkitURL;

var SpeechRecognition = SpeechRecognition || webkitSpeechRecognition
var SpeechRecognitionEvent = SpeechRecognitionEvent || webkitSpeechRecognitionEvent
var recognition = new SpeechRecognition();
recognition.continuous = true;
recognition.interimResults = true;

var final_transcript = '';
var latest_transcript = '';
var recognizing = false;
recognition.onresult = function(event){
    var interim_transcript = '';
    for (var i = event.resultIndex; i < event.results.length ; i++){
        if (event.results[i].isFinal) {
            final_transcript +=  event.results[i][0].transcript;
            latest_transcript += event.results[i][0].transcript;
        } else {
            interim_transcript += event.results[i][0].transcript;
        }
    }
    $('#final_span').html(linebreak(final_transcript));
    $('#interim_span').html(linebreak(interim_transcript));
}
recognition.onstart = function() {
    recognizing = true;
}
recognition.onend = function() {
    recognizing = false;
    var temp = {"transcript":latest_transcript,"threshold":$('#threshold').val()}
    socket.emit('transcript',temp);
    latest_transcript = '';
    final_transcript += '<br>';
}

let two_line = /\n\n/g;
let one_line = /\n/g;
function linebreak(s)   {
    return s.replace(two_line,'<p></p>').replace(one_line,'<br>')
}

var gumStream;
var rec;
var source;

var AudioContext = window.AudioContext || window.webkitAudioContext;
var audioContext;
var processor;

var recordBtn = document.getElementById('recordBtn');
var stopBtn = document.getElementById('stopBtn');
var response = document.getElementById('response');

recordBtn.addEventListener("click",startRecording);
stopBtn.addEventListener("click",stopRecording);


function startRecording() { 
    console.log("recordBtn clicked");
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
            let child = $(document.createElement('span')).appendTo('#response');
            let p = $(document.createElement("p")).html(
                "<b>Google Result:</b>" + data["google_result"] + "<br/> <b>IBM Result:</b>" + data["ibm_result"] + "<br/><b>Houndify Result:</b>" + data["houndify_result"] + "<br/><b>Wit Result:</b>" + data["wit_result"]  
            ).appendTo(child);
            child.addClass("get_result");
        })
        socket.on('final_result',function(data){
            let child = $("#response span:not(.get_final)").first();
            let p = $(document.createElement("pre")).html(data["alignment"]).appendTo(child);
            final_transcript = final_transcript.replace(data["origin_result"],data["origin_result"] + " -> " + data["final_result"]);
            $('#final_span').html(final_transcript);
            child.addClass("get_final");
        })
    } else {
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

    if (recognizing) {
        recognition.stop();
        return
    }

    recognition.lang = 'en_US';
    recognition.start();
}

function stopRecording() {
    console.log("stopBtn clicked");

    stopBtn.disabled = true;
    recordBtn.disabled = false;

    recognition.stop();

    gumStream.getAudioTracks()[0].stop();
    audioContext.close();
    socket.emit('stop_recording');
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