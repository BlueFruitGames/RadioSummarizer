import os
import logging
import numpy as np
import librosa
from scipy import signal
from pydub import AudioSegment
import glob

# Sets up the logger for this module
def setup_logging_preprocessing(log_level):
    global logger
    logger = logging.getLogger('AudioPreprocessing')
    ch = logging.StreamHandler()
    if log_level == "INFO":
        logger.setLevel(logging.INFO)
        ch.setLevel(logging.INFO)
    elif log_level == "DEBUG":
        logger.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s:%(name)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
# Changes the rate of the source file to 16kHz and save the file in the intermediate folder
# Returns the path to the file with correct samplerateo 
def change_rate(source_file, intermediate_dir_path, new_rate = 16000):
    new_audio = AudioSegment.from_mp3(source_file)
    intermediate_dir_path
    file_name = os.path.basename(source_file).replace(".mp3", "")
    output_file = os.path.join(intermediate_dir_path, file_name + "_trimmed.wav") 
    new_audio.export(output_file, format="wav", parameters=["-ac", str(1), "-ar", str(new_rate)])
    return output_file

# Trims the source file at the locations where the highest correlation for a begin and end sound is found.
# If a correlation threshold is provided, values below are filtered.
# Returns the path to the trimmed audiofile 
def trim_audio(source_file, begin_sounds_dir, end_sounds_dir, output_dir, correlation_threshold, new_rate = 16000):
    logger.info("Trimming file...")
    y_source_audio, sr_source_audio = librosa.load(source_file)
    
    # Find the beginssample that has the highest correlation with the source audio 
    begin_max_correlation, begin_offset, begin_file = find_best_correlation(y_source_audio, sr_source_audio, begin_sounds_dir, correlation_threshold, True)
    if begin_max_correlation <= 0:
        logger.error("No valid audio file")
        exit()
    logger.debug("Begin sound file is: " + begin_file)
    
    # Find the  endsample that has the highest correlation with the source audio 
    end_max_correlation, end_offset, end_file = find_best_correlation(y_source_audio, sr_source_audio, end_sounds_dir, correlation_threshold)
    if end_max_correlation <= 0:
        logger.error("No valid audio file")
        exit()
    logger.debug("End sound file is: " + end_file)

    begin_time = begin_offset * 1000
    end_time = end_offset * 1000

    file_name = os.path.basename(source_file).replace(".mp3", "")
    output_file = os.path.join(output_dir, file_name + "_trimmed.wav") 

    # Trimming of the audio at the locations of the begin- and endsample
    new_audio = AudioSegment.from_mp3(source_file)
    if(begin_time >= end_time):
        logger.error("Audio could not be trimmed")
        exit()
    new_audio = new_audio[begin_time:end_time]
    new_audio.export(output_file, format="wav", parameters=["-ac", str(1), "-ar", str(new_rate)])
    return output_file
    
# Finds the time in an audio, where the highest correlation between a sound sample and the source audio is.   
# Returns the correlation, time_offset and file_path to the audiosample with the highest correlation
def find_best_correlation(y_source_audio, sr_source_audio, sounds_dir, threshold, bIsBeginn = False):
    max_correlation = -1
    offset = -1
    file = None
    sound_files = glob.glob(sounds_dir + "/*")
    #Iteration through all .mp3 in the provided folder
    for sound_file in sound_files:
        if ".mp3" in sound_file:
            y_current_signal, sr_current_signal = librosa.load(sound_file)
            current_correlation, current_offset = find_offset(y_source_audio, sr_source_audio, y_current_signal, threshold) 
            if bIsBeginn:
                current_offset += librosa.get_duration(y=y_current_signal, sr=sr_current_signal)
            #Update output if higher correlation is found
            if(current_correlation > max_correlation):
                max_correlation = current_correlation
                offset = current_offset
                file = sound_file
    return max_correlation, offset, file

# Finds the highest correlation between a single sound sample and the source audio
# If a correlation threshold is provided, values below are filtered.
# Returns the offset and correlation of the current audiosample
def find_offset(complete_audio, sr_complete_audio, audio_signal, correlation_threshold):
    correlation = signal.correlate(complete_audio, audio_signal, mode='valid', method='fft')
    max_correlation = max(correlation)
    logger.debug("Current correlation is: " + str(max_correlation))
    #Excluded files below the correlation threshold if it is provided
    if  correlation_threshold != -1 and max_correlation < correlation_threshold:
        logger.error("Couldn't find valid trimming point!")
        return -1, -1
    peak = np.argmax(correlation)
    offset = round(peak/sr_complete_audio, 2)  
    return max_correlation, offset

