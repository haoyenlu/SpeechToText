import queue

from google.cloud import speech

class SpeechClientBridge:
    def __init__(self,streaming_config,on_response,sid):
        self._on_response = on_response
        self._queue = queue.Queue()
        self._ended = True
        self.streaming_config = streaming_config
        self._sid = sid

    def start(self):
        self._ended = False
        client = speech.SpeechClient()
        stream = self.generator()
        requests = (speech.StreamingRecognizeRequest(audio_content=content) for content in stream)
        responses = client.streaming_recognize(self.streaming_config,requests)
        self.process_response_loop(responses)
    
    def terminate(self):
        self._ended = True
    
    def add_request(self,buffer):
        self._queue.put(bytes(buffer))

    def process_response_loop(self,responses):
        for response in responses:
            self._on_response(self._sid,response)

            if self._ended:
                break

    def generator(self):
        while not self._ended:
            chunk = self._queue.get()
            if chunk is None:
                return
            
            data = [chunk]

            while True:
                try:
                    chunk = self._queue.get(block=False)
                    if chunk is None:
                        return 
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)
