import torch
import cv2
import numpy as np
import tensorflow as tf 
from re import DEBUG, sub
from flask import Flask, render_template, request, redirect, send_file, url_for, Response
from werkzeug.utils import secure_filename, send_from_directory
import os
import subprocess
from subprocess import Popen
import re
import requests
import shutil
import time
import glob
import argparse


from ultralytics import YOLO

app = Flask(__name__)
@app.route("/")
def hello_world():
    return render_template('index.html')
##

@app.route("/",methods=["GET","POST"])
def predict_img():
    if request.method == "POST":
        if 'file' in request.files:
            f= request.files['file']
            basepath= os.path.dirname(__file__)
            filepath=os.path.join(basepath,'uploads',f.filename)
            print("upload folder is", filepath)
            f.save(filepath)
            global imgpath
            predict_img.imgpath=f.filename
            print("printing predict_img ::::",predict_img)
            
            file_extension= f.filename.rsplit('.',1)[1].lower()
            
            if file_extension == 'jpg':
                img= cv2.imread(filepath)
                frame=cv2.imencode('.jpg',cv2.UMat(img))[1].tobytes()
                
                yolo=YOLO('best.pt')
                detection= yolo.predict(img, save=True)
                return display(f.filename)
            elif file_extension=='mp4':
                video_path=filepath
                cap= cv2.VideoCapture(video_path)
                
                frame_width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                frame_height= int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                fourcc=cv2.VideoWriter_fourcc(*'mp4v')
                out=cv2.VideoWriter('output.mp4',fourcc,30.0,(frame_width, frame_height))
                
                model=YOLO('best.pt')
                
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                    results=model(frame, save=True)
                    print(results)
                    cv2.waitKey(1)
                    
                    res_plotted= results[0].plot()
                    cv2.imshow("result",res_plotted)
                    
                    out.write(res_plotted)
                    
                    if cv2.waitKey(1)== ord('q'):
                        break
                    
                return video_feed()
        
    folder_path='runs/detect'
    subfolders=[f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
    latest_subfolder= max(subfolders, key=lambda x: os.path.getctime(os.path.join(folder_path,x)))
    image_path=folder_path+'/'+latest_subfolder+'/'+f.filename
    return render_template('index.html', image_path=image_path)

@app.route('/<path:filename>')

def display(filename):
    folder_path='runs/detect'
    subfolders=[f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
    latest_subfolder= max(subfolders, key=lambda x: os.path.getctime(os.path.join(folder_path,x)))
    directory=folder_path+'/'+latest_subfolder
    print("printing directory: ",directory)
    files=os.listdir(directory)
    latest_file=files[0]
    
    print(latest_file)
    filename=os.path.join(folder_path, latest_subfolder, latest_file)
    file_extension=filename.rsplit('.',1)[1].lower()
    
    environ=request.environ
    if file_extension=='jpg':
        return send_from_directory(directory, latest_file,environ)
    else:
        return "Invalid file Format"
#

def get_frame():
    folder_path=os.getcwd()
    mp4_files='output.mp4'
    video=cv2.VideoCapture(mp4_files)
    while True:
        success, image=video.read()
        if not success:
            break
        ret, jpeg=cv2.imencode('.jpg', image)
        yield(b'--frame\r\n'
              b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() +b'\r\n\r\n')
        time.sleep(0.1)
#
@app.route("/video_feed")

def video_feed():
    print("function called")
    return Response(get_frame(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
                    
                    
if __name__ == "__main__":
    parser=argparse.ArgumentParser(description="Flask App")
    parser.add_argument("--port", default=2345, type=int, help="port number")
    args=parser.parse_args()
    app.run(host="0.0.0.0", port=args.port) #debug=True)
