# import queue

# from google.cloud import speech
# from google.cloud.speech import RecognitionConfig, StreamingRecognitionConfig

# config = RecognitionConfig(
#     encoding = RecognitionConfig.AudioEncoding.LINEAR16,
#     sample_rate_hertz= 16000,
#     language_code ="en-US",
# )

# streaming_config = StreamingRecognitionConfig(
#     config = config,
#     interim_results = True,
# )

# class SpeechClientBridge:
#     def __init__(self,on_response,sid):
#         self._on_response = on_response
#         self._queue = queue.Queue()
#         self._ended = False
#         self._sid = sid

#     def start(self):
#         print(f"{self._sid} client start")
#         client = speech.SpeechClient()
#         stream = self.generator()
#         requests = (speech.StreamingRecognizeRequest(audio_content=content) for content in stream)
#         """ above pass """
#         responses = client.streaming_recognize(streaming_config,requests)
#         self.process_response_loop(responses)
    
#     def terminate(self):
#         self._ended = True
    
#     def add_request(self,buffer):
#         self._queue.put(bytes(buffer))  

#     def process_response_loop(self,responses):
#         for response in responses:
#             self._on_response(self._sid,response)

#             if self._ended:
#                 break

#     def generator(self):
#         while not self._ended:
#             chunk = self._queue.get()
#             if chunk is None:
#                 return
            
#             data = [chunk]

#             while True:
#                 try:
#                     chunk = self._queue.get(block=False)
#                     if chunk is None:
#                         return 
#                     data.append(chunk)
#                 except queue.Empty:
#                     break

#             yield b"".join(data)
