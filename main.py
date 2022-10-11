#

import os
from google.cloud import dialogflow_v2
from google.api_core.exceptions import InvalidArgument
from google.cloud import dialogflow
import sounddevice as sd
import pyaudio
import wave
import numpy as np
import scipy.io.wavfile as wav
import argparse
import uuid
import speech_recognition as sr

#set up dialoflow agent
#google application credentials need to be changed to the individual credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "..."
project_id = '...'
language_code = 'en'
session_id = 'me'



# [START dialogflow_detect_intent_audio]
def detect_intent_audio(project_id, session_id, audio_file_path, language_code):
    """Returns the result of detect intent with an audio file as input.
    Using the same `session_id` between requests allows continuation
    of the conversation."""
    #starts speech recognition to detect the key word
    r = sr.Recognizer()
    #set the key word
    keyWord = 'Hi Robot'
    exitWord = 'Goodbye'

    with sr.Microphone() as source:
        print('Please start speaking..\n')
        while True:
            audio = r.listen(source)
            try:
                text = r.recognize_google(audio)
                if keyWord.lower() in text.lower():
                    print('Keyword detected in the speech.')
                    #once keyword detected, move on to recording what user wants
                    chunk = 1024  # Record in chunks of 1024 samples
                    sample_format = pyaudio.paInt16  # 16 bits per sample
                    channels = 1
                    fs = 16000  # Record at 44100 samples per second
                    seconds = 4 #how long it records for
                    filename = "output.wav"

                    p = pyaudio.PyAudio()  # Create an interface to PortAudio

                    print('Recording')

                    stream = p.open(format=sample_format,
                                    channels=channels,
                                    rate=fs,
                                    frames_per_buffer=chunk,
                                    input=True)

                    frames = []  # Initialize array to store frames

                    # Store data in chunks for 3 seconds
                    for i in range(0, int(fs / chunk * seconds)):
                        data = stream.read(chunk)
                        frames.append(data)

                    # Stop and close the stream
                    stream.stop_stream()
                    stream.close()
                    # Terminate the PortAudio interface
                    p.terminate()

                    print('Finished recording')

                    # Save the recorded data as a WAV file
                    wf = wave.open(filename, 'wb')
                    wf.setnchannels(channels)
                    wf.setsampwidth(p.get_sample_size(sample_format))
                    wf.setframerate(fs)
                    wf.writeframes(b''.join(frames))
                    wf.close()

                    session_client = dialogflow.SessionsClient()

                    # Note: hard coding audio_encoding and sample_rate_hertz for simplicity.
                    audio_encoding = dialogflow.AudioEncoding.AUDIO_ENCODING_LINEAR_16
                    sample_rate_hertz = 16000

                    session = session_client.session_path(project_id, session_id)
                    #print("Session path: {}\n".format(session))

                    with open(audio_file_path, "rb") as audio_file:
                        input_audio = audio_file.read()

                    audio_config = dialogflow.InputAudioConfig(
                        audio_encoding=audio_encoding,
                        language_code=language_code,
                        sample_rate_hertz=sample_rate_hertz,
                    )
                    query_input = dialogflow.QueryInput(audio_config=audio_config)

                    request = dialogflow.DetectIntentRequest(
                        session=session, query_input=query_input, input_audio=input_audio,
                    )
                    response = session_client.detect_intent(request=request)

                    print("=" * 20)
                    print("Query text: {}".format(response.query_result.query_text))
                    print(
                        "Detected intent: {} (confidence: {})\n".format(
                            response.query_result.intent.display_name,
                            response.query_result.intent_detection_confidence,
                        )
                    )
                    print("Fulfillment text: {}\n".format(response.query_result.fulfillment_text))
                    #write to file
                    file.write("Fulfillment text: {}\n".format(response.query_result.fulfillment_text))

                    #need to loop back to the of recording
                    continue
                # if the exit key word, goodbye,  is heard then it will stop running
                if exitWord.lower() in text.lower():
                    print('Exit word detected in the speech.')
                    print('Goodbye.')
                    break

            #if no key word detected, it will ask the user to speak again
            except Exception as e:
                print('Please speak again.')

# [END dialogflow_detect_intent_audio]
if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--project-id", help="Project/agent id.  Required.",
        default='hsr-project-342014',
    )
    parser.add_argument(
        "--session-id",
        help="Identifier of the DetectIntent session. " "Defaults to a random UUID.",
        default=str(uuid.uuid4()),
    )
    parser.add_argument(
        "--language-code",
        help='Language code of the query. Defaults to "en-US".',
        default="en-US",
    )
    parser.add_argument(
        "--audio-file-path", help="Path to the audio file.",
        default="output.wav",
    )

    args = parser.parse_args()

    detect_intent_audio(
        args.project_id, args.session_id, args.audio_file_path, args.language_code
    )
