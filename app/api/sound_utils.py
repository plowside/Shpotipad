import os, random
from pydub import AudioSegment
from moviepy.editor import VideoFileClip


def get_audio_duration_is_loud(audio_file):
    audio = AudioSegment.from_file(audio_file)
    duration_seconds = len(audio) / 1000
    loudness_db = audio.dBFS
    return duration_seconds, loudness_db

def convert_to_mp3(output_path, input_path = None, optimize=False, max_loudness_db=-20):
    input_obj = input_path
    input_ext = input_obj.split(".")[-1].lower()
    
    if input_ext in ['mp4', 'webm']:
        video_clip = VideoFileClip(input_obj)
        audio_clip = video_clip.audio
        audio_clip.write_audiofile(output_path)
        audio_clip.close()
        video_clip.close()
    elif input_ext in ['mp3', 'wav', 'ogg', 'm4a']:
        audio = AudioSegment.from_file(input_obj)
        if optimize:
            audio = audio.set_frame_rate(44100).set_channels(2)
        audio.export(output_path, format='mp3')
    else:
        return {'status': False, 'message': 'Invalid file extension'}
    
    duration, loudness = get_audio_duration_is_loud(output_path)
    return {'status': True, 'path': output_path, 'duration': duration, 'is_loud': loudness < max_loudness_db}
