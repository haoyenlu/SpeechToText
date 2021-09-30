from flask import Flask, render_template , request , jsonify
from flask_socketio import SocketIO , emit , Namespace , disconnect , join_room , leave_room
from dotenv import load_dotenv
from pprint import pprint

import threading
import queue
import os 
import eventlet
from eventlet import tpool
from eventlet import greenthread

#from SpeechClient import SpeechClientBridge
from speechRecognition import SpeechRecognizer 
from textprocessor import TextProcessor

load_dotenv()

async_mode = 'eventlet'


if async_mode == 'eventlet':
    eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
socketio = SocketIO(app,async_mode=async_mode)

bridges = {}
recognizer = {}

thread = None

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect',namespace='/test')
def on_connect():
    join_room(request.sid)
    emit('reply','You are connected.')

@socketio.on('sample_rate',namespace='/test')
def on_sample_rate(data):
    sample_rate = data
    emit('reply','audio context sample rate: {}'.format(sample_rate))

@socketio.on('start_recording',namespace='/test')
def on_start_recording():
    recognizer[request.sid] = SpeechRecognizer(request.sid)
    #thread = eventlet.spawn(tpool.execute,recognizer[request.sid].recognize)
    emit('reply','recognizer created')

@socketio.on('micBinaryStream',namespace='/test')
def on_micBinaryStream(data):
    #bridges[request.sid].add_request(data) 
    recognizer[request.sid].add_stream(data)
    emit('reply','get stream.')

@socketio.on('stop_recording',namespace='/test')
def on_stop_recording():
    recognizer[request.sid].slice_buffer()
    results = recognizer[request.sid].recognize_sentence()
    emit('result',results)

@socketio.on('transcript',namespace='/test')
def on_transcript(data):
    alignment , final_result = recognizer[request.sid].final_result(data["transcript"],data["threshold"])
    final_result = TextProcessor.add_punctuation(final_result)
    jsonify_result = ({'alignment':alignment,'final_result':final_result,'origin_result':data["transcript"]})
    emit('final_result',jsonify_result)

@socketio.on('ace_parsing',namespace='/test')
def on_ace_parsing(data): # data should be a sentence and some argument of APE
    emit('ace_result',TextProcessor.ace_parsing(data["sentence"],*data["options"]))

@socketio.on('write_to_file',namespace='/test')
def on_write_to_file(data):
    print("pass")





    
if __name__ == '__main__':
    socketio.run(app,debug=True,port=8000)
