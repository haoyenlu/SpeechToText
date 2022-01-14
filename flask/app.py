from flask import Flask, render_template , request , jsonify , send_file
from flask_socketio import SocketIO
from google.cloud import texttospeech

import sqlite3
import platform
import os 
import json
import eventlet
from eventlet import tpool
from eventlet import greenthread


async_mode = 'eventlet'


if async_mode == 'eventlet':
    eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
socketio = SocketIO(app,async_mode=async_mode)

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google_API.json'
exec_head = "./" if platform.system() != "Windows" else ""

database = "database/database.db"


from namespace import CustomNamespace
socketio.on_namespace(CustomNamespace('/test'))

def get_db_connection():
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/get_puzzle',methods=["POST"])
def get_puzzle():
    conn = get_db_connection()
    puzzle = conn.execute('SELECT * FROM puzzle').fetchall()
    conn.close()
    return json.dumps( [dict(ix) for ix in puzzle] ) 

@app.route('/submit_puzzle',methods=["GET","POST"])
def submit_puzzle():
    if request.method == 'POST':
        content = request.values['content']
        question = request.values['question']
        useable = request.values['uesable']

        conn = get_db_connection()
        cur = conn.cursor()
        if useable == "on":
            cur.execute("INSERT INTO puzzle (content,question,useable) VALUES(?,?,?)",
                        (content,question,'TRUE'))
        else :
            cur.execute("INSERT INTO puzzle (content,question,useable) VALUES(?,?,?)",
                        (content,question,'FALSE'))
        conn.commit()
        conn.close()
    return render_template("submit_puzzle.html")


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/TTSapi', methods=['POST'])
def TTSapi():
    if request.method == 'POST':
        text = request.values['text']
        filename = request.values['filename']
        pitch = 0
        speed = 1
        lang = 'en-US'
        if(request.values['voice']) == 'male1':
            name = "en-US-Wavenet-D"
            gender = texttospeech.SsmlVoiceGender.MALE
        elif(request.values['voice'] == 'female1'):
            name = "en-US-Wavenet-F"
            gender = texttospeech.SsmlVoiceGender.FEMALE
        elif(request.values['voice'] == 'male2'):
            name = "en-US-Wavenet-A"
            gender = texttospeech.SsmlVoiceGender.MALE
        elif(request.values['voice'] == 'female2'):
            name = "en-US-Wavenet-E"
            gender = texttospeech.SsmlVoiceGender.FEMALE
        elif(request.values['voice'] == 'robot'):
            name = "en-GB-standard-A"
            gender = texttospeech.SsmlVoiceGender.MALE
            speed = 0.66
            pitch = -10.40
            lang = 'en-GB'
        message = json.dumps({
            'lang': lang,
            'inputtext': text,
            'name': name,
            'gender': gender,
            'speed': speed,
            'pitch': pitch
        })
        applic(message, filename)
        return jsonify({'result': True, 'filename': filename})
    return jsonify({'result': False})




    

def applic(message, filename):
    """
    this function connect google textToSpeech API and return audio(mp3) file.
    2 args as below, 
    message: json(
        'lang': 'en-US' or 'en_GB'
        'inputtext': The text to speak out,
        'name': name,
        'gender': gender,
        'speed': speaking speed,
        'pitch': speaking pitch
    ),
    filename: str()
        name of audio file
    """
    client = texttospeech.TextToSpeechClient()
    message = json.loads(message)
    synthesis_input = texttospeech.SynthesisInput(text=message['inputtext'])
    voice = texttospeech.VoiceSelectionParams(
        language_code=message['lang'],
        ssml_gender=message['gender'],
        name=message['name'])
    audio_config = texttospeech.AudioConfig(
        speaking_rate=message['speed'],
        pitch=message['pitch'],
        audio_encoding=texttospeech.AudioEncoding.MP3)
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config)
    with open(f'./static/audio/{filename}.mp3', 'wb') as out:
        out.write(response.audio_content)
        #print(f'Audio content written to "{filename}.mp3"')
    return send_file(f'./static/audio/{filename}.mp3', attachment_filename=f'{filename}.mp3')



    
if __name__ == '__main__':
    socketio.run(app,debug=True)
