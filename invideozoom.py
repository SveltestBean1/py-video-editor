import cv2
import os
import wave
import contextlib
import librosa
import numpy as np
import urllib.request
from cv2 import VideoWriter, VideoWriter_fourcc
from PIL import Image
import tkinter as tk
from tkinter import filedialog
from pydub import AudioSegment
from tqdm import tqdm
import random as r
import argparse
import atexit
import shutil
from moviepy.editor import *

def exit_handler():
    try:
        shutil.rmtree(os.getcwd() + "\\TEMP")
    except:
        print("Could not be deleted")

parser = argparse.ArgumentParser(description='Zooms in on a video whenever a beat is detected in an audio file.')
parser.add_argument('--zoom', type=float, default=300, help="Amount of zoom during beat. Optional")
parser.add_argument('--name', type=str, help="Name of output video")
parser.add_argument('--blur', dest='blur', action='store_true', help="Enables blur. False by default")
parser.add_argument('--no_blur', dest='blur', action='store_false', help="Disables blur. False by default")
parser.set_defaults(blur=False)

args = parser.parse_args()

width = 1280
height = 720
radius = 150
FPS = 30
seconds = 10
length = 1280
mid = (int(width/2), int(height/2))
CHUNK = 1024
zoom = args.zoom
name = args.name
blur = args.blur

try:
    root = tk.Tk()
    root.geometry("1x1")
    vidpath = tk.filedialog.askopenfilename(filetypes=[(".mp4 files",".mp4")])
    root.destroy()

    sound = AudioSegment.from_file(vidpath, format="mp4")
    sound.export("audio.wav", format="wav")

    y, sr = librosa.load("audio.wav")
    with contextlib.closing(wave.open("audio.wav",'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
        frames = int(duration*FPS)

    onsets = librosa.onset.onset_detect(y=y,sr=sr,units='time')
    onsetframes = []
    for i in onsets:
        onsetframes.append(int(i*FPS))

    try:
        shutil.rmtree(os.getcwd() + "\\TEMP")
    except:
        pass
    os.mkdir(os.getcwd() + "\\TEMP")

    clip = VideoFileClip(vidpath)
    clip.write_videofile(os.getcwd() + "\\TEMP\\{name}.mp4".format(name=name), fps=FPS)
    clip.reader.close()

    vidcap = cv2.VideoCapture(os.getcwd() + "\\TEMP\\{name}.mp4".format(name=name))
    success,image = vidcap.read()
    count = 0
    while success:
        cv2.imwrite(os.getcwd() + "\\TEMP\\frame%d.jpg" % count, image)     # save frame as JPEG file
        success,image = vidcap.read()
        count += 1

    fourcc = VideoWriter_fourcc(*'MP42')
    video = VideoWriter('./{name}.avi'.format(name = name), fourcc, float(FPS), (width, height))

    for i in tqdm(range(int(count))):
        pil_image = Image.open(os.getcwd() + "\\TEMP\\frame%d.jpg" %i).convert('RGB')
        image = np.array(pil_image)
        image = image[:, :, ::-1].copy()
        r = 1280.0 / image.shape[1]
        dim = (1280, int(image.shape[0] * r))
        resized = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
        fimg = resized[:]
        if i in onsetframes:
            length = 1280 + zoom
        else:
            length -= (length-1280)/5

        length = int(length)
        r = length / fimg.shape[1]
        dim = (length, int(fimg.shape[0] * r))
        frimg = cv2.resize(fimg, dim, interpolation = cv2.INTER_AREA)

        if blur:
            kernel = np.ones((5, 5),np.float32)/25
            frimg = cv2.filter2D(frimg,-1,kernel)

        crop = (int((length-width)/2), length-int((length-width)/2), int((frimg.shape[0]-height)/2), frimg.shape[0]-int((frimg.shape[0]-height)/2))
        frame = frimg[crop[2]:crop[3], crop[0]:crop[1]]

        video.write(frame)

    video.release()

    os.system("ffmpeg -i \"{path}\\{input}.avi\" -i audio.wav -ac 2 -b:v 1000k -c:a aac -c:v libx264 -b:a 300k -vprofile high -bf 0 -strict experimental -f mp4 {output}.mp4".format(path = os.getcwd(), input = name, output = name))
    os.remove("{name}.avi".format(name = name))
    os.remove("audio.wav")
except:
    pass

atexit.register(exit_handler)