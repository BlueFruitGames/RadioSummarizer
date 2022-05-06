# RadioSummarizer

RadioSummarizer is an application that converts news broadcasts on the radio to their text representation.

## OVERVIEW

To execute the application, you can provide either a snippet of the news broadcast itself or a snippet of a recording of more than just the news broadcast, meaning some advertisements or music before and after.
If you provided a recording with more than the news broadcast, you also have to provide an audio snippet of the sounds played at the beginning and the end of the broadcast.
With booth additional files provided, the application can trim your original audio to just the broadcast and will then proceed with using this file.
The project itself is divided into three different files.

**Main.py** is the start of the execution flow and has to be called for starting the application.
**AudioPreprocessing.py** is used to preprocess the audio file properly. Meaning trimming the original one, converting the .mp3 input file to a .wav file, and converting the final audio file to a 16KHz version for later use.
**RadioSummarizer.py** uses different models to convert the news broadcast into a text representation.

After trimming and converting the source file, a .txt is created in the specified output folder, which contains the text representation of the broadcast.
Additionally, the change of speakers is noted with *"<--Neuer Sprecher-->"*. The input of the .txt is also printed on the console as a reference.
Like the trimmed audio file, byproducts are placed in a folder called "intermediate," located in the output folder.

## Libraries

Other libraries that are used in this project are:

- **Vosk** for the speech to text transformation

- **Stanza** to restore the capitalization of the text

- **Deep Multilingual Punctuation** to restore the punctuation of the text

- **pyannote-audio** to apply speaker diarization on the audio

- **pydub** is used to work with the audio (like finding the times for trimming)

## SETUP

- To execute the program, you have to download the vosk model for your language manually and place in the model's folder and rename it to "vosk_model".

- Call
`pip install -r requirements.txt`
to install the requirements.

## EXECUTION

To start the application, you have to run:
`python Main.py`

Additionally, you have to provide additional flags to run the program correctly. The available flags are:
- `-b path` *(Required if -t is used)*
Path to a folder with the audio files, each containing one of the possible sound samples played at the beginning of the broadcast. The Sound files should have about the same length.
A Length between 0.5s to 2s should be sufficient. The files have to be of type .mp3.

- `-c number` *(Optional)*
Threshold that will be applied during the search for the start and end signal.
If the highest correlation value is below the provided threshold, it will be judged as no valid point was found.
If not set, no checking of the correlation value will be done.

- `-d` *(Optional)*
If set, the program will delete the contents of the intermediate folder after its execution.

- `-db` *(Optional)*
Prints debug information to the console.
Like the highest correlation value for each sound sample with the source audio.

- `-e path` *(Required if -t is used)*  => Path to a folder with the audio files that contain one of the sound samples that is played at the end of the broadcast.
The Sound files should have about the same length.
A Length between 0.5s to 2s should be sufficient. The files have to be of type .mp3.

- `-h` (Optional)
Displays all available flags, including a short description.

- `-i path`  *(Required)*
Path to the source file containing the news broadcast. It has to be of type .mp3 or .wav.
Or a path to a folder containing multiple source files. Only files of type .mp3 will be converted. 
For files of type .wav it is suspected, that they were generated with this program and have the right settings.

- `-l language_code` *(Optional)*
It can be used to set the language used in the source audio. For this, you have to provide the specific language code that you can find in the stanza documentation. Defaults to "de"

- `-o path` *(Optional)*
Path to the output directory. Defaults to "output".

- `-t` *(Optional)*
Tells the program to trim the audio.
If not used, it is suspected that the audio contains the news broadcast.

A valid call to start the application would be:
`python Main.py -i path_to_source -t -b path_to_begin_sample  -e path_to_end_sample -d`


 
