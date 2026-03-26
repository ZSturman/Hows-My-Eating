import os
import shutil
import datetime
import subprocess



def formatTime(timestamp):
    dt = datetime.datetime.fromtimestamp(float(timestamp))
    formatted_time = dt.strftime('%Y-%m-%d_%H-%M-%S') 
    return formatted_time

def convertToWav(m4a_file):
    wav_file = os.path.splitext(m4a_file)[0] + '.wav'
    subprocess.run(['ffmpeg', '-i', m4a_file, wav_file])
    return wav_file

def sortFiles(directory='./data'):
    for filename in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, filename)):
            # Create a folder with the same name as the file
            timestamp = os.path.getmtime(os.path.join(directory, filename))
            folder_name = formatTime(timestamp)
            folder_path = os.path.join(directory, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            
            # Move the json and m4a files into the folder
            if filename.endswith('.json'):
                new_json_name = f'motion.json'
                shutil.move(os.path.join(directory, filename), os.path.join(folder_path, new_json_name))
            elif filename.endswith('.m4a'):
                new_m4a_name = f'audio.m4a'
                shutil.move(os.path.join(directory, filename), os.path.join(folder_path, new_m4a_name))
                
                # Convert to WAV and move the wav file
                wav_file = convertToWav(os.path.join(folder_path, new_m4a_name))
                new_wav_name = f'audio.wav'
                shutil.move(wav_file, os.path.join(folder_path, new_wav_name))

sortFiles()