import os
import logging
import numpy as np
import librosa
from scipy import signal
from pydub import AudioSegment
import glob

def setup_logging_preprocessing(log_level):
    """Sets up the logger for this module

    Args:
        log_level (str): the selected loglevel
    """
    global logger
    logger = logging.getLogger('AudioPreprocessing')
    logger.propagate = False
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
    
def change_rate(source_file, output_dir, new_rate = 16000):
    """Stores the source_file in the intermeditate_dir_path as a .wav with new_rate as its sample rate

    Args:
        source_file (str): path to the source file
        output_dir (str): path to the output directory
        new_rate (int, optional):The sample rate of the new file. Defaults to 16000.

    Returns:
        str: Path to the newly created file
    """
    new_audio = AudioSegment.from_mp3(source_file)
    file_name = os.path.basename(source_file).replace(".mp3", "")
    output_file = os.path.join(output_dir, file_name + "_trimmed.wav") 
    new_audio.export(output_file, format="wav", parameters=["-ac", str(1), "-ar", str(new_rate)])
    return output_file

def trim_audio(source_file, begin_sounds_dir, end_sounds_dir, output_dir, correlation_threshold, new_rate = 16000):
    """Trims the source file and saves it with a new rate

    Args:
        source_file (str): path to the source file
        begin_sounds_dir (str): path to the directory containing the sound samples played at the begin of a broadcast
        end_sounds_dir (str): path to the directory containing the sound samples played at the end of a broadcast
        output_dir (str): path to the output directory
        correlation_threshold (int): minimum correlation a sound sample has to have so that it is valid
        new_rate (int, optional): the new rate of the trimmed file. Defaults to 16000.

    Returns:
        bool: if trimming was successful
        str: path to the trimmed file
    """
    logger.info("Trimming file {}".format(os.path.basename(source_file)))
    y_source_audio, sr_source_audio = librosa.load(source_file)
    
    #Find the begin sample that has the highest correlation with the source audio 
    begin_max_correlation, begin_offset, begin_file = find_best_correlation(y_source_audio, sr_source_audio, begin_sounds_dir, correlation_threshold, True)
    if begin_max_correlation <= 0:
        logger.error("No valid begin sound sample")
        return False, source_file
    logger.debug("Begin sound file is: " + os.path.basename(begin_file))
    
    #Find the end sample that has the highest correlation with the source audio 
    end_max_correlation, end_offset, end_file = find_best_correlation(y_source_audio, sr_source_audio, end_sounds_dir, correlation_threshold)
    if end_max_correlation <= 0:
        logger.error("No valid end sound sample")
        return False, source_file
    logger.debug("End sound file is: " + os.path.basename(end_file))

    begin_time = begin_offset * 1000
    end_time = end_offset * 1000

    file_name = os.path.basename(source_file).replace(".mp3", "")
    output_file = os.path.join(output_dir, file_name + "_trimmed.wav") 

    #Trimming of the audio at the locations of the begin and end sample
    new_audio = AudioSegment.from_mp3(source_file)
    if(begin_time >= end_time):
        logger.error("Audio could not be trimmed")
        return False, source_file
    new_audio = new_audio[begin_time:end_time]
    new_audio.export(output_file, format="wav", parameters=["-ac", str(1), "-ar", str(new_rate)])
    return True, output_file
    
def find_best_correlation(y_source_audio, sr_source_audio, sounds_dir, threshold, bIsBeginn = False):
    """Finds the time in the source_audio with the highest correlation with a sound sample in the sourc_dir

    Args:
        y_source_audio (np.ndarray): audio time series of source_audio
        sr_source_audio (int): sampling rate of source_audio
        sounds_dir (str): path to the directory containing the sound samples
        threshold (int): values below this threshold are not valid
        bIsBeginn (bool, optional): if sounds_dir contains sound samples played at the beginning of broadcast. Defaults to False.

    Returns:
        float: highest correlation
        float: offset at which the highest correlation is located
        str: path to the file with the highest correlation
    """
    max_correlation = -1
    offset = -1
    file = None
    sound_files = glob.glob(os.path.join(sounds_dir, "*"))
    #Iteration through all .mp3 in the provided folder
    for sound_file in sound_files:
        if ".mp3" in sound_file:
            y_current_signal, sr_current_signal = librosa.load(sound_file)
            current_correlation, current_offset = find_offset(y_source_audio, sr_source_audio, y_current_signal, threshold, os.path.basename(sound_file)) 
            if bIsBeginn:
                current_offset += librosa.get_duration(y=y_current_signal, sr=sr_current_signal)
            #Update output if higher correlation is found
            if(current_correlation > max_correlation):
                max_correlation = current_correlation
                offset = current_offset
                file = sound_file
    return max_correlation, offset, file

def find_offset(y_source_audio, sr_source_audio, y_sound_sample, correlation_threshold, name):
    """Finds the highest correlation between a single sound sample and the source audio

    Args:
        y_source_audio (np.ndarray): audio time series of source_audio
        sr_source_audio (int): sampling rate of source_audio
        y_sound_sample (np.ndarray): values below this threshold are not valid
        correlation_threshold (int): values below this threshold are not valid
        name (str): the name of the current sample file

    Returns:
        float: highest correlation
        float: offset at which the highest correlation is located
    """
    correlation = signal.correlate(y_source_audio, y_sound_sample, mode='valid', method='fft')
    max_correlation = max(correlation)
    #Excluded files below the correlation threshold if it is provided
    if  correlation_threshold != -1 and max_correlation < correlation_threshold:
        logger.debug("Couldn't find valid trimming point for {}".format(name))
        return -1, -1
    else:
        logger.debug("Current correlation for {} is: {}".format(name ,max_correlation))
    peak = np.argmax(correlation)
    offset = round(peak/sr_source_audio, 2)  
    return max_correlation, offset

