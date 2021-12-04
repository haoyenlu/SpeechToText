from pprint import pprint

import threading 
import queue
import io

import speech_recognition as sr 
from API_keys import *

r = sr.Recognizer()


class SpeechRecognizer:
    def __init__(self,sid):
        self._buffer = []
        self._audio_queue = queue.Queue()
        self._ended = False
        self._sample_rate = 16000
        self._sample_width = 2
        self._sid = sid
        self._result_queue = queue.Queue()

    def add_stream(self,audio_stream):
        self._buffer.append(audio_stream)


    def get_buffer(self):
        return b"".join(self._buffer)
    
    def slice_buffer(self):
        buff = self.get_buffer()
        self._audio_queue.put(buff)
        self._buffer = []

    def terminate(self):
        self._ended = True

    def print_queue(self):
        while True:
            try:
                q = self._audio_queue.get(block=False)
                print(q)
            except queue.Empty: 
                print("queue is empty.")
                break
    
    def recognize_sentence(self):
        buff = self._audio_queue.get(block=False)
        if buff is None:
            return 
        
        audio_data = sr.AudioData(buff,self._sample_rate,self._sample_width)

        try:
            google_result = r.recognize_google(audio_data)
        except sr.UnknownValueError:
            google_result = "Google Speech Recognition could not understand audio"
        except sr.RequestError as e:
            google_result = "Could not request results from Google Speech Recognition service; {0}".format(e)
            
        # recognize from IBM speech to text
        try:
            ibm_result = r.recognize_ibm(audio_data,username=IBM_USERNAME,password=IBM_PASSWORD)
        except sr.UnknownValueError:
            ibm_result = "IBM Speech to Text could not understand audio"
        except sr.RequestError as e:
            ibm_result = "Could not request results from IBM Speech to Text service; {0}".format(e)

        #recognize from houndify 
        try:
            houndify_result = r.recognize_houndify(audio_data, client_id=HOUNDIFY_ID, client_key=HOUNDIFY_KEY)
        except sr.UnknownValueError:
            houndify_result = "Houndify could not understand audio"
        except sr.RequestError as e:
            houndify_result = "Could not request results from Houndify service; {0}".format(e)

        #recognize from wit
        try:
            wit_result = r.recognize_wit(audio_data, key=WIT_KEY)
        except sr.UnknownValueError:
            wit_result = "Wit could not understand audio"
        except sr.RequestError as e:
            wit_result = "Could not request results from Wit service; {0}".format(e)

        results = {"google_result":google_result,"ibm_result":ibm_result,"houndify_result":houndify_result,"wit_result":wit_result}
        self._result_queue.put(results)
        return results

    def final_result(self,transcript,threshold):
        from StringAlign import StringAlign , give_param
        S = StringAlign()
        S += transcript
        results = self._result_queue.get(block=True)
        for key, value in results.items():
            if "not" not in value: 
                S += value
        
        p = give_param('james') # two options wayne or james
        p.lowercast = True
        p.use_stem = True
        S.evaluate(p)
        try:
            S.big_anchor_concat_heuristic(p)
            alignment = S.str_big_anchor()
            weight = [1,1,1,1,1]
            final_result = " ".join(S.final_result(weight,int(threshold)))
        except:
            alignment = "No alignment"
            final_result = None

        return alignment , final_result


    def recognize(self):
        print(f"{self._sid} recognizer start")
        while not self._ended or not self._audio_queue.empty():
            while not self._audio_queue.empty():
                results = self.recognize_sentence()


                


                
                

