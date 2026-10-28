"""Probe four hash-pinned OpenCV models. Synthetic frames only; never package/publish."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys
import urllib.request
import urllib.parse
import time
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
COMMIT = '48b10fa505aeb51fbd127fc60a5c660040e823b7'
MODELS = (
 ('palm_detection_mediapipe','palm_detection_mediapipe_2023feb.onnx',3905734,'78ff51c38496b7fc8b8ebdb6cc8c1abb02fa6c38427c6848254cdaba57fcce7c',(1,192,192,3)),
 ('handpose_estimation_mediapipe','handpose_estimation_mediapipe_2023feb.onnx',4099621,'db0898ae717b76b075d9bf563af315b29562e11f8df5027a1ef07b02bef6d81c',(1,224,224,3)),
 ('human_segmentation_pphumanseg','human_segmentation_pphumanseg_2023mar.onnx',6163938,'552d8a984054e59b5d773d24b9b12022b22046ceb2bbc4c9aaeaceb36a9ddf24',(1,3,192,192)),
 ('face_detection_yunet','face_detection_yunet_2023mar.onnx',232589,'8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4',None),
)

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--require-intel',action='store_true')
 parser.add_argument('--models-dir',type=Path)
 args=parser.parse_args()
 native=sys.platform=='darwin' and platform.machine().lower()=='x86_64'
 if args.require_intel and not native:raise RuntimeError('The requested experiment requires a native Intel Mac.')
 if cv2.__version__!='4.14.0':raise RuntimeError('Use the reviewed OpenCV 4.14 wheel.')
 folder=args.models_dir or ROOT/'work/intel-dnn-probe/models'
 folder.mkdir(parents=True,exist_ok=True)
 results=[]
 cv2.setNumThreads(2)
 for task,name,size,expected,shape in MODELS:
  path=folder/name
  if not path.exists():
   url='https://media.githubusercontent.com/media/opencv/opencv_zoo/'+COMMIT+'/models/'+task+'/'+name
   with urllib.request.urlopen(url,timeout=60) as response:
    if urllib.parse.urlsplit(response.url).hostname!='media.githubusercontent.com':raise ValueError('Unexpected model redirect')
    data=response.read(size+1)
   if len(data)!=size or hashlib.sha256(data).hexdigest()!=expected:raise ValueError('Model size/hash mismatch')
   with path.open('xb') as output:output.write(data)
  data=path.read_bytes()
  if len(data)!=size or hashlib.sha256(data).hexdigest()!=expected:raise ValueError('Existing model size/hash mismatch')
  if shape is None:
   net=cv2.FaceDetectorYN.create(str(path),'',(320,320),backend_id=cv2.dnn.DNN_BACKEND_OPENCV,target_id=cv2.dnn.DNN_TARGET_CPU)
   def infer():
    _,faces=net.detect(np.zeros((320,320,3),np.uint8))
    if faces is not None:raise ValueError('Unexpected face on synthetic black frame')
    return []
  else:
   net=cv2.dnn.readNet(str(path));net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV);net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
   def infer():
    net.setInput(np.zeros(shape,np.float32));outputs=net.forward(net.getUnconnectedOutLayersNames())
    if not all(np.isfinite(value).all() for value in outputs):raise ValueError('Non-finite synthetic output')
    return [list(value.shape) for value in outputs]
  outputs=infer();started=time.perf_counter()
  for _ in range(3):infer()
  results.append({'task':task,'model_sha256':expected,'model_bytes':size,'output_shapes':outputs,'synthetic_mean_ms':round((time.perf_counter()-started)*1000/3,2)})
 report={'ok':True,'native_intel_probe':native,'opencv':cv2.__version__,'zoo_commit':COMMIT,'camera_opened':False,'personal_frames_used':False,'app_backend_integrated':False,'frozen_app_tested':False,'distribution_ready':False,'results':results}
 destination=ROOT/'work/intel-dnn-probe/report.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps(report))

if __name__=='__main__':
 try:main()
 except Exception as error:
  print('OpenCV DNN probe failed:',type(error).__name__,file=sys.stderr)
  raise SystemExit(1)
