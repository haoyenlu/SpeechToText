from flask_socketio import Namespace , emit
from flask import request

from speechrecognition import SpeechRecognizer 
from textprocessor import TextProcessor

recognizer = {}

class CustomNamespace(Namespace):
    def on_connect(self):
        emit('reply','You are connected.')

    def on_sample_rate(self,data):
        sample_rate = data
        emit('reply','audio context sample rate: {}'.format(sample_rate))

    def on_start_recording(self):
        recognizer[request.sid] = SpeechRecognizer(request.sid)
        #thread = eventlet.spawn(tpool.execute,recognizer[request.sid].recognize)
        emit('reply','recognizer created')

    def on_micBinaryStream(self,data):
        #bridges[request.sid].add_request(data) 
        recognizer[request.sid].add_stream(data)
        emit('reply','get stream.')

    def on_stop_recording(self):
        recognizer[request.sid].slice_buffer()
        results = recognizer[request.sid].recognize_sentence()
        emit('result',results)

    def on_transcript(self,data):
        alignment , final_result = recognizer[request.sid].final_result(data["transcript"],data["threshold"])
        final_result = TextProcessor.add_punctuation(final_result)
        jsonify_result = ({'alignment':alignment,'final_result':final_result,'origin_result':data["transcript"]})
        emit('final_result',jsonify_result)

    def on_ace_parsing(self,data): # data should be a sentence and some argument of APE
        emit('ace_result',TextProcessor.ace_parsing(data["sentence"],*data["options"]))

    def on_write_to_file(self,data):
        from datetime import datetime
        now = datetime.now()
        current_time = now.strftime("%b-%d-%Y %H:%M:%S")
        filename = 'ace_text/' + current_time + '.txt'
        with open(filename,'w+') as f:
            for line in data:
                f.write(line)
                f.write('\n')

        from reasoning import getAnswer
        reasoner_answer = getAnswer(filename)
        print(reasoner_answer)

        from answering import answer
        if reasoner_answer[0] is True:
            response = answer(reasoner_answer[2],reasoner_answer[1])
            emit('reasoner_result',response)
        else :
            emit('reasoner_result',"I don't have an answer.")