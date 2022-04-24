RadioSummarizer is an application with which you can convert news broadcasts on the radio into text. 

OVERVIEW:
To execute the application, you can provide either a snippet of the news broadcast itself or a snippet of a recording of more than just the news broadcast, meaning some advertisements or music before and after.
If you provided a recording with more than the news broadcast, you also have to provide an audio snippet of the sounds played at the beginning and the end of the broadcast. 
If you provide booth additional files, the application will trim your original audio to just the broadcast and will then proceed with using this file. 
The project is therefore divided into three different files. 
The Main.py is the start of the execution flow and has to be called for starting the application.
The AudioPreprocessing.py is used to preprocess the audio file properly. Meaning trimming the original one, converting .mp3s to .wav files, and converting the final audio file to a 16KHz version for later use
The RadioSummarizer.py is the heart of the project. It uses different models to convert the news broadcast into its text representation.

After trimming and converting the source file, a .txt is created in the desired output folder, which contains a translation of the audio to its text form. 
Additionally, the change of speakers is noted with a <--Neuer Sprecher-->. The input of the .txt is also printed on the console as a reference. 
Like the trimmed audio file, byproducts are placed in a folder called "intermediate," located in the output folder. 

Other libraries which are used in the project are:
- Vosk for the speech to text transformation
- Stanza to restore the capitalization of the text
- Deep Multilingual Punctuation to restore the punctuation of the text
- pyannote-audio to apply speaker diarization on the audio
- pydub is used to work with the audio (like finding the points for trimming)

SETUP:
	-To execute the program, you have to download the vosk model for your language manually and place in the model's folder and rename it to "vosk_model".
	- Call pip install -r requirements.txt to install the requirements.

EXECUTION:
To start the application, you have to run: python Main.py

Additionally, you have to provide additional flags to run the program correctly. The available flags are:
-b path	=> Path to a folder with the audio files that contain one of the sound samples that is played at the beginning of the broadcast. 
		   They should be relatively close in their length, and no spoken words must be in this sample. The files have to be of type .mp3.
-c number 	=> (Optional) Threshold, which will be applied at the search for the start and end signal.
		   If the highest correlation value is below the provided number, it will be counted as no valid point was found.
-d 		=> (Optional) Delete the contents of the intermediate folder after execution. If not used, files are stored in the intermediate folder after execution.
-db		=> (Optional) Prints debug information to the console. Like the calculated correlation value for the sound sample in the current audio.
-e path 	=> Path to a folder with the audio files that contain one of the sound samples that is played at the end of the broadcast. 
		   They should be relatively close in their length, and no spoken words must be in this sample. The files have to be of type .mp3.
-h 		=> To display all available flags include a short description
-i path	=> Path to the source file containing the news broadcast. It has to be of type .mp3.
-l string	=> (Optional) Can be used to set the language which is used in the source audio. For this, you have to provide the specific language code 
		   which you can find in the stanza documentation. Defaults to "de"
-o path 	=> (Optional) Path to the output directory. Defaults to "output".
-t 		=> (Optional) When you have to trim your audio beforehand. If not used, it is suspected that the audio contains the news broadcast.

So a valid call to start the application would be:
	python Main.py -i path_to_source -t -b path_to_begin_sample	-e path_to_end_sample -d


 