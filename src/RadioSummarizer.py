import logging
import os
import wave
import json
import stanza
from pydub import AudioSegment
from pydub.silence import split_on_silence
from vosk import Model, KaldiRecognizer, SetLogLevel
from deepmultilingualpunctuation import PunctuationModel
from pyannote.audio import Pipeline

model_path = os.path.join("models", "vosk_model")

def setup_logging_summarizer(log_level):
    """Sets up the logger for this module

    Args:
        log_level (str): the selected loglevel
    """
    global logger 
    logger = logging.getLogger('RadioSummarizer')
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

def speech_to_text(source_file, output_file, language):
    """Converts source_file to an output file containing the text representation of the broadcast 

    Args:
        source_file (str): path to the source file
        output_file (str): path to the output file
        language (str): language code
    """
    SetLogLevel(-1)
    logger.info('Setting up speech-to-text model...')
    model = Model(model_path)
    
    word_list = generate_text(source_file, model)
    result_diarization = diarize_text(source_file)
    text = insert_speakers(word_list, result_diarization)
    text = punctuate_text(text)
    text = adjust_text_after_punctuation(text)
    text = correct_capitalization(text, language)
    text = adjust_text_after_capitalization(text)
    logger.info(text)
    save_to_txt(text,output_file) 

def generate_text(source_file, model):
    """Converts the source_file into its text representation

    Args:
        source_file (str): path to the source file
        model (vosk.Model): the vosk model to use

    Returns:
        list: list containing the recognized words with their start and end time
    """
    wf = wave.open(source_file, "rb")
    logger.info('Converting speech to text...')
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)

    word_list = []
    frames = split_audio(source_file, 500, -20)
    frames = merge_splits(frames, 10)
    logger.debug("Splitted into " + str(len(frames)) + " Segments")
    index = 0
    rest = wf.getnframes()
    # Convert speech using vosk model
    while True:
        current_frames = rest
        if index < len(frames):
            current_frames = frames[index]
            rest -= current_frames
        data = wf.readframes(current_frames)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            part_result = json.loads(rec.Result())
            for cur_word in part_result["result"]:
                word_list.append([cur_word["word"], True, cur_word["start"], cur_word["end"]])
        index += 1
    part_result = json.loads(rec.FinalResult())
    if part_result["text"] != "":
        for cur_word in part_result["result"]:
            word_list.append([cur_word["word"], True, cur_word["start"], cur_word["end"]])
    return word_list

def split_audio(source_file, min_silence_len, silence_thresh):
    """Splits the audio at times where a dB is below silence_thresh

    Args:
        source_file (str): path to the source audio
        min_silence_len (int): length of silence_thresh needed to be recognized as separation point
        silence_thresh (int): dB threshold for silent parts

    Returns:
        list: Contains the seperated chunks of frames
    """
    audio = AudioSegment.from_wav(source_file)
    chunks = split_on_silence(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
    frames = []
    for chunk in chunks:
        frames.append(int(chunk.frame_count()))
    return frames

def merge_splits(frames, max_split_count):
    """merges the separated frames together until count of splits is <= max_split_count

    Args:
        frames (list): list containing the separated frames
        max_split_count (int): number of maximum splits

    Returns:
        list: updated list of frames
    """
    temp = []
    while len(frames) > max_split_count:
        temp = [];
        smallest_index = 0
        merge_index = -1
        for index in range(0, len(frames)):
            if(frames[index] <= frames[smallest_index]):
                smallest_index = index
                if(index == 0 and index + 1 == len(frames)):
                    merge_index = -1
                elif(index == 0):
                    merge_index = index + 1
                elif(index + 1 == len(frames)):
                    merge_index = index - 1
                else:
                    prev_value = frames[index - 1]
                    next_value = frames[index + 1]
                    if (prev_value > next_value):
                        merge_index = index + 1
                    else:
                        merge_index = index - 1
        if(merge_index == -1): 
            break
        for index in range(0, len(frames)):
            if(index == merge_index):
                continue
            if(index == smallest_index):
                temp.append(frames[smallest_index] + frames[merge_index])
            else:
                temp.append(frames[index])
        frames = temp.copy()
    return frames   

def diarize_text(source_file):
    """Diarizes the audio in source_file

    Args:
        source_file (str): path to the source_file

    Returns:
        list: Containging the speakers and the time they spoke
    """
    logger.info('Diarizing audio...')
    result = []
    discarded = False
    discard_limit = 4.0
    
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization")
    diarization = pipeline(source_file)
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        if len(result) == 0:
            result.append([turn.start, turn.end, speaker])
        # If the same speaker is recognized in a row, update the ending of the previous entry
        elif result[-1][2] == speaker and not discarded:
            result[-1][1] = turn.end
        # If period is to short, discard the entry
        elif turn.end - turn.start  <= discard_limit:
            discarded = True
        else:
            # If previous entry was discarded, then update the start time to the time of the last in the list
            if(discarded):
                result.append([result[-1][1], turn.end, speaker])
            else:
                result.append([turn.start, turn.end, speaker])
            discarded = False

    
    return result     

def insert_speakers(word_list, diarization):
    """Generates text of the word_list and the speaker changes in between

    Args:
        word_list (list): recognized words and their start and end time
        diarization (list): recognized speakers and their start and end time

    Returns:
        str: generated text
    """
    logger.info('Inserting speakers in text...')
    word_index = 0
    word_list_len = len(word_list)
    speaker_index = 1
    speaker_text = "<---Neuer Sprecher--->"
    result = "<---Neuer Sprecher--->"
    offset = 0.5
    
    while word_index < word_list_len:
        # If the time of the current word is greater than the time of the next speaker, then add a speaker change to the text
        if word_list[word_index][1] and speaker_index < len(diarization) and diarization[speaker_index][0] - offset < word_list[word_index][2]:
            result = result + speaker_text
            speaker_index += 1
        result = result + " " + word_list[word_index][0]
        word_index += 1
    return result 
    
def punctuate_text(text):
    """Restores punctuation for a given text

    Args:
        text (str): text to add punctuation too

    Returns:
        str: punctuated version of the text
    """
    logger.info("Setting up punctuation model...")
    model = PunctuationModel(model ="oliverguhr/fullstop-punctuation-multilang-large")
    logger.info("Adding punctuation...")
    return model.restore_punctuation(text)

def adjust_text_after_punctuation(text):
    """Cleans up the text after punctuation

    Args:
        text (str): text to clean up

    Returns:
        str: cleaned up version of the text
    """
    text = text.replace(". <---Neuer", " <---Neuer")
    text = text.replace(" <---Neuer", ". <---Neuer")
    text = text.replace("<---Neuer", ". <---Neuer")
    text = text.replace("--->.", "---> ")
    text = text.replace("--->,", "---> ")
    text = text.replace("--->!", "---> ")
    text = text.replace("--->?", "---> ")
    text = text.replace("--->:", "---> ")
    return text

def correct_capitalization(text, language):
    """Restores the capitalization for a given text

    Args:
        text (str): text to capitalize
        language (str): language code

    Returns:
        str: capitalized text
    """
    logger.info('Correcting capitalization...')
    stanza.download(lang = language, logging_level="ERROR")
    capitalized_text = ""
    nlp = stanza.Pipeline(processors="tokenize,pos", lang=language, logging_level="ERROR")
    doc = nlp(text)
    previous_entry = "."
    for sent in doc.sentences:
        for w in sent.words:
            if w.text[0] == "-":
                capitalized_text = capitalized_text + w.text
            elif w.upos in ["PROPN","NOUN"]:
                capitalized_text = capitalized_text + " " + w.text.capitalize()
            # Because of earlier transformations two . in sequence are possible -> remove the second one
            elif previous_entry == "." and w.text  == ".":
                continue
            # If a specific punctuation marker is in front of our word, we know that the word must be capitalized
            elif previous_entry in [".", "?", "!", ":"] or ">" in previous_entry:
                capitalized_text = capitalized_text + " " + w.text.capitalize()
            elif w.text in [".", ",", ":", "?", "!", ":"]:
                capitalized_text = capitalized_text + w.text  
            else:
                capitalized_text = capitalized_text + " " + w.text
            previous_entry = w.text
    return capitalized_text

def adjust_text_after_capitalization(text):
    """Cleans up the text after capitalization

    Args:
        text (str): text to clean up

    Returns:
        str: cleaned up version of the text
    """
    text = text.replace("--->.","--->")
    text = text.replace("---> .","--->")
    text = text.replace("--->", "--->\n")
    text = text.replace("<--- ", "\n<---")
    text = text.replace(".", ".\n")
    text = text.replace(":", ":\n")
    text = text.replace("!", "!\n")
    text = text.replace("?", "?\n")
    return text

def save_to_txt(text, output_file):
    """saves the text to output_file

    Args:
        text (str): the generated text
        output_file (str): path to the output file
    """
    logging.info("Writing to .txt...")
    with open(output_file, "w") as f:
            f.write(text)
            f.write("\n\n\n")

