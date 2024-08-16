import moviepy.editor as mp

def convert_to_mp4(input_file, output_file):
    video = mp.VideoFileClip(input_file)
    video.write_videofile(output_file, codec='libx264', audio_codec='aac')
    
