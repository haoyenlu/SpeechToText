var namespace = '/test';
var socket = null;

URL = window.URL || window.webkitURL;

var SpeechRecognition = SpeechRecognition || webkitSpeechRecognition
var SpeechRecognitionEvent = SpeechRecognitionEvent || webkitSpeechRecognitionEvent
var recognition = new SpeechRecognition();
recognition.continuous = true;
recognition.interimResults = true;

var final_transcript = '';
var textarea_text = "";
var recognizing = false;

recognition.onresult = function(event){
    var interim_transcript = '';
    for (var i = event.resultIndex; i < event.results.length ; i++){
        if (event.results[i].isFinal) {
            final_transcript += event.results[i][0].transcript;
            interim_transcript += event.results[i][0].transcript;
        } else {
            interim_transcript += event.results[i][0].transcript;
        }
    }
    $('#input_text').val(interim_transcript);
}

function linebreak(s)   {
    let two_line = /\n\n/g;
    let one_line = /\n/g;
    return s.replace(two_line,'<p></p>').replace(one_line,'<br>')
}


recognition.onstart = function() {
    recognizing = true;
}


recognition.onend = function() {
    recognizing = false;
    $('#input_text').val(final_transcript);

    
    var data = {"transcript":final_transcript,"threshold":$('#threshold').val()}
    socket.emit('transcript',data);
    final_transcript = '';
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


handle_socket();

function handle_socket(){
    if (socket == null)
    {
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
            let child = $(document.createElement('span')).prependTo('#response');
            let collapse_but = $(document.createElement('button')).click(function(){
                child.children('#api_result').toggle();
                child.children('#alignment').toggle();
            }).text("Show Speech To Text Process").attr('id','collapse_result_button').appendTo(child);
            let p = $(document.createElement("p")).html(
                "<b>Google Result:</b>" + data["google_result"] + "<br/> <b>IBM Result:</b>" + data["ibm_result"] + "<br/><b>Houndify Result:</b>" + data["houndify_result"] + "<br/><b>Wit Result:</b>" + data["wit_result"] + "<br/>" 
            ).attr('id','api_result').appendTo(child);
            child.addClass("get_result");
        })

        socket.on('final_result',function(data){
            let child = $("#response span:not(.get_final)").last();
            let p = $(document.createElement("pre")).html(data["alignment"]).appendTo(child).attr('id','alignment');
            if (data["final_result"] != null) {
                let final_p = $(document.createElement('p')).append("<strong>Final Result:<strong>" + data["final_result"]).appendTo(child);
                let delete_but = $(document.createElement('button')).click(function(){
                    child.remove();
                }).text('delete').appendTo(child);
                $('#input_text').val(data["final_result"]);
            }
            else {
                let final_p =  $(document.createElement('p')).append("<strong>No Final Result<strong>").appendTo(child);
                let transcript = $('#result p:not(.get_final').first().attr('id','get_final');
                let delete_but = $(document.createElement('button')).click(function(){
                    transcript.remove();
                    child.remove();
                }).text('delete').appendTo(child);
            }
            child.addClass("get_final");
        })

        socket.on('ace_result',function(data){  
            let ace_result = $("#ace_result").empty();
            for (const [key , value] of Object.entries(data)){
                let box = $(document.createElement('div')).appendTo(ace_result);
                let title = $(document.createElement('span')).html(key.toUpperCase()).appendTo(box);
                if (key == 'messages'){
                    let content = $(document.createElement('pre')).appendTo(box).text(JSON.stringify(value,null,'\n'));
                }
                else {
                    let content = $(document.createElement('pre')).appendTo(box).text(value);
                }
            }
        })

        socket.on('reasoner_result',function(data){
            let reasoner_result = $('#reasoner_result').empty();
            reasoner_result.html(data);
            createChatWidget(_content=data,isRobot=true);
        })
    } 
    else 
    {
        socket.connect();
    } 
}


function startRecording() { 
    console.log("recordBtn clicked");

    socket.emit('start_recording');

    var constraints = {audio:true,video:false};

    recordBtn.disabled = true;
    stopBtn.disabled = false;

    navigator.mediaDevices.getUserMedia(constraints).then(function(stream){
        console.log("getUserMedia available.");
        audioContext = new AudioContext();
        console.log("audio context created.");
        sampleRate = audioContext.sampleRate;
        socket.emit('sample_rate',sampleRate);

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

$('#reasoning').click(function(){
    var ace_text_list = []
    var ace_text = $('#chat_box .box p').text(function(index,string){
        ace_text_list.push(string);
    });
    console.log(ace_text_list);
    console.log("wait for reasoning.");
    socket.emit('write_to_file',ace_text_list);
})


var input = document.getElementById("input_text");
input.addEventListener("keyup",function(event){
    if (event.keyCode === 13){
        createChatWidget(_content = input.value,isRobot = false);
        input.value = "";
    }
})

function ape_analyze(a_sentence){
    var checked_array = new Array();
    $("input:checked").each(function(i) {checked_array[i] = this.value;});
    var ace_parse_data = {options:checked_array,sentence:a_sentence};
    socket.emit('ace_parsing',ace_parse_data);
}

function createChatWidget(_content,isRobot){
    var chat_box = $('#chat_box');
    if (isRobot){
        var box = $(document.createElement('div')).appendTo(chat_box).attr('class','box darker');
        var avatar = $(document.createElement('img')).appendTo(box).attr('src',"./static/images/robot_avatar.png").attr('class','right');
        sendToTTSApi(_content);
    }
    else {
        var box = $(document.createElement('div')).appendTo(chat_box).attr('class','box');
        var avatar = $(document.createElement('img')).appendTo(box).attr('src','./static/images/user_avatar.png');
    }
    var content = $(document.createElement('p')).html(_content).attr('contenteditable','true').appendTo(box);
    var _delete = $(document.createElement('a')).html('delete').appendTo(box).attr('class','right').click(function(){box.remove();});
    chat_box.scrollTop(chat_box.prop("scrollHeight"));
}

function sendToTTSApi(content){
    var text = content;
    var voice = document.getElementById("voicegender").value;
    var up = new FormData();
    var filename = new Date().getTime();
    up.append('voice',voice);
    up.append('text',text);
    up.append('filename',filename);
    console.log(filename);
    $.ajax({
        type: 'POST',
        url: '/TTSapi',
        data: up,
        processData: false,
        contentType: false
    }).done(function (data) {
        file=data['filename']+'.mp3';
		console.log(file);
		console.log("Text to Speech upload successful!");
        var newDiv = document.createElement('div');
        var newAudio = document.createElement('audio');
		var AudioSrc = document.createElement('source');
		AudioSrc.type = "audio/mpeg"
		AudioSrc.src = "../static/audio/"+file;
		newAudio.controls = true;
		newDiv.align = "left";
		newAudio.appendChild(AudioSrc);
		newDiv.appendChild(newAudio);
		document.getElementById("tts_result").appendChild(newDiv);

		newAudio.load();
		newAudio.play();

		if(data['result'] == true)
			console.log("Reload successfully!!!");
		else 
			console.log("TTS Failed");

	}).fail(function(jqXHR,textStatus,error){
			console.log("Upload text failed!");
	});

}