import logging
import os 
import glob
from AudioPreprocessing import trim_audio, change_rate, setup_logging_preprocessing
from RadioSummarizer import speech_to_text, setup_logging_summarizer
import argparse

intermediate_dir = "intermediate"

# Sets up the logger for this module 
def setup_logging(log_level):
    global logger 
    logger = logging.getLogger('Main')
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
    setup_logging_preprocessing(log_level)
    setup_logging_summarizer(log_level)

# Sets up the programs arguments
def setup_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--begin", dest = "begin_sounds_dir", help="Directory with sounds played at the begining")
    parser.add_argument("-c", "--min_correlation", dest = "min_correlation", default = -1, help="filter value for trim correlation")
    parser.add_argument("-d", "--delete", dest = "delete", action='store_true', help="Delete contents of intermediate Directory?")
    parser.add_argument("-db", "--debug", dest = "debug", action='store_true', help="Show debug information?")
    parser.add_argument("-e", "--end", dest = "end_sounds_dir", help="Directory with sound played at the ending")
    parser.add_argument("-i", "--input",dest ="input", help="Audiofile to summarize")
    parser.add_argument("-l", "--language",dest ="language", default="de", help="Language used in the audiofile")
    parser.add_argument("-o", "--output_dir", dest = "output_dir", default = "output", help="Output directory")
    parser.add_argument("-t", "--trimfile", dest = "trimfile", action='store_true', help="Trim the audio file before conversion?")
    return parser.parse_args()

# Checks if a provided path does exist
def does_path_exist(current_path, name):
    if not os.path.exists(current_path):
        logger.error("{} doesn't exist".format(name))
        exit()
# Reads and checks the arguments provided by the user 
def check_args(args):
    # Reads the input of the -db flag
    is_debug = args.debug
    log_level = "INFO"
    if is_debug:
        log_level = "DEBUG"
    setup_logging(log_level)
    
    # Reads the input of the -i flag
    if(args.input == None):
        logger.error("No source file provided!")
        exit()
    source_file = args.input
    does_path_exist(source_file, "SourceFile")
    
    # Reads the input of the -l flag
    language = args.language
    
    # Reads the input of the -t and c flag
    trim_file = args.trimfile
    min_correlation = int(args.min_correlation)

    # Reads the input of the -b flag
    if(trim_file and args.begin_sounds_dir == None):
        logger.error("No file with begin sound provided!")
        exit()
    begin_sounds_dir = args.begin_sounds_dir
    if trim_file:
        does_path_exist(begin_sounds_dir, "BeginSoundDir")

    # Reads the input of the -e flag
    if(trim_file and args.end_sounds_dir == None):
        logger.error("No directory with end sounds provided!")
        exit()
    end_sounds_dir = args.end_sounds_dir
    if trim_file:
        does_path_exist(end_sounds_dir, "EndSoundDir")

    # Reads the input of the -o flag
    output_dir = args.output_dir
    does_path_exist(output_dir, "OutputDir")
    if os.path.isfile(output_dir): 
        logger.error("Entered file as output folder")
        exit()
    
    # Reads the input of the -d flag
    delete_intermediate = args.delete

    return language, source_file, trim_file, min_correlation, begin_sounds_dir, end_sounds_dir, output_dir, delete_intermediate
 
# Handling of program arguments   
args = setup_args()
language, source_file, trim_file, min_correlation, begin_sounds_dir, end_sounds_dir, output_dir, delete_intermediate = check_args(args)
intermediate_dir_path = os.path.join(output_dir, intermediate_dir)
if not os.path.exists(intermediate_dir_path):
    os.makedirs(intermediate_dir_path)

# Trimming and Conversion of the source file
logger.info("Preparing audiofiles...")
trimmed_file = source_file
if trim_file:    
    trimmed_file = trim_audio(source_file, begin_sounds_dir, end_sounds_dir, intermediate_dir_path, min_correlation)
else:   
    trimmed_file = change_rate(trimmed_file, intermediate_dir_path)
   
# Conversion of audio to text 
logger.info("Starting conversion...")
output_file = os.path.join(output_dir, os.path.basename(source_file).replace(".mp3", ".txt"))

speech_to_text(trimmed_file, output_file, language)

# Deletion of contents in the intermediate folder
if delete_intermediate:
    logger.info("Deleting files in Intermediate folder...")
    files = glob.glob(intermediate_dir_path + "/*")
    for file in files:
        os.remove(file)

logger.info("Speech to text conversion finished!")
quit()