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

def dl_img(url, filename):
    full_path = os.getcwd() + filename + ".jpg"
    urllib.request.urlretrieve(url, full_path)
    return full_path

parser = argparse.ArgumentParser(description='Zooms in on a picture whenever a beat is detected in an audio file.')
parser.add_argument('--zoom', type=float, default=300, help="Amount of zoom during beat. Optional")
parser.add_argument('--name', type=str, help="Name of output video")
parser.add_argument('--blur', dest='blur', action='store_true', help="Enables blur. False by default")
parser.add_argument('--no_blur', dest='blur', action='store_false', help="Disables blur. False by default")
parser.set_defaults(blur=False)
parser.add_argument('--url', type=str, default="", help="Video URL. Optional")

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
url = args.url

root = tk.Tk()
root.geometry("1x1")
mp3path = tk.filedialog.askopenfilename(filetypes=[(".mp3 files",".mp3")])
root.destroy()

sound = AudioSegment.from_mp3(mp3path)
sound.export("audio.wav", format="wav")

y, sr = librosa.load("audio.wav")
with contextlib.closing(wave.open("audio.wav",'r')) as f:
    frames = f.getnframes()
    rate = f.getframerate()
    duration = frames / float(rate)
    frames = int(duration*FPS)
os.remove("audio.wav")

onsets = librosa.onset.onset_detect(y=y,sr=sr,units='time')
onsetframes = []
for i in onsets:
    onsetframes.append(int(i*FPS))

fourcc = VideoWriter_fourcc(*'MP42')
video = VideoWriter('./{name}.avi'.format(name = name), fourcc, float(FPS), (width, height))

if not url:
    root = tk.Tk()
    root.geometry("1x1")
    picpath = tk.filedialog.askopenfilename(filetypes=[("Compatible pictures",".png .jpg .jpeg")])
    pil_image = Image.open(picpath).convert('RGB')
    image = np.array(pil_image)
    image = image[:, :, ::-1].copy()
    root.destroy()
else:
    picpath = dl_img(url, name)
    pil_image = Image.open(picpath).convert('RGB')
    image = np.array(pil_image)
    image = image[:, :, ::-1].copy()

r = 1280.0 / image.shape[1]
dim = (1280, int(image.shape[0] * r))
resized = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)

for i in tqdm(range(frames)):
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

os.system("ffmpeg -i \"{path}\\{input}.avi\" -i \"{mp3path}\" -ac 2 -b:v 9000k -c:a aac -c:v libx264 -b:a 300k -vprofile high -bf 0 -strict experimental -f mp4 {output}.mp4".format(path = os.getcwd(), mp3path = mp3path, input = name, output = name))
os.remove("{name}.avi".format(name = name))