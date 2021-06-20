from flask import Flask, render_template , request , jsonify
from flask_socketio import SocketIO , emit , Namespace , disconnect
from google.cloud.speech import RecognitionConfig, StreamingRecognitionConfig
from dotenv import load_dotenv
from pprint import pprint

import threading
import queue
import os 


from google.cloud import speech
from SpeechClient import SpeechClientBridge
from speechRecognition import SpeechRecognizer 


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
socketio = SocketIO(app)

bridges = {}
recognizer = {}


class StreamingNamespace(Namespace):

    def on_connect(self):
        emit('reply','You are connected.')
    
    def on_sample_rate(self,data):
        self._sample_rate = data
        emit('reply','audio context sample rate: {}'.format(self._sample_rate))

    def on_start_recording(self):
        config = RecognitionConfig(
            encoding = RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz= 16000,
            language_code ="en-US",
        )
        streaming_config = StreamingRecognitionConfig(
            config = config,
            interim_results = True,
        )
        bridges[request.sid] = SpeechClientBridge(streaming_config,self._response_handler,request.sid)
        recognizer[request.sid] = SpeechRecognizer(self._result_handler,request.sid)
        self.t1 = threading.Thread(target = bridges[request.sid].start)
        self.t2 = threading.Thread(target = recognizer[request.sid].recognize)
        self.t1.start()
        self.t2.start()
    
    def on_micBinaryStream(self,data):
        bridges[request.sid].add_request(data)    
        recognizer[request.sid].add_stream(data)


    def on_stop_recording(self):
        bridges[request.sid].terminate()
        self.t1.join()
        bridges.pop(request.sid)

        recognizer[request.sid].terminate()
        self.t2.join()
        recognizer.pop(request.sid)

        emit("reply","Speech to Text client finished.")



    @staticmethod
    def _response_handler(sid,response):
        if not response.results:
            return 

        result = response.results[0]
        if not result.alternatives:
            return
        
        if result.is_final:
            recognizer[sid].slice_buffer()

        transcription = result.alternatives[0].transcript

        jsonify_result = ({'transcription':result.alternatives[0].transcript,'is_final':result.is_final})
        socketio.emit("transcription",jsonify_result,namespace='/test',room=sid)

    @staticmethod
    def _result_handler(sid,result):
        socketio.emit("result",result,namespace='/test',room=sid)
        

@app.route('/')
def index():
    return render_template('index.html')


socketio.on_namespace(StreamingNamespace('/test'))

if __name__ == '__main__':
    load_dotenv()
    socketio.run(app,host='0.0.0.0',debug=True)
