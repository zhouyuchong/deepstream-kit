#!/bin/sh
export LD_PRELOAD=../../models/yolov5/yolov5s/libYoloV5Decoder.so:../../models/retinaface/libRetinafaceDecoder.so:../../models/arcface/libArcFaceDecoder.so
python3 gui.py
