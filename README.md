# Deepstream Kit
This repo is a deepstream tool kit contains some interfaces.

## Requirements
+ Deepstream 6.0.1+
+ GStreamer 1.14.5
+ Cuda 11.4+
+ NVIDIA driver 470.63.01+
+ TensorRT 8+
+ Pyathon 3.6   

Follow [deepstream](https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_Quickstart.html#dgpu-setup-for-ubuntu) official doc to install dependencies.

Deepstream docker is more recommended.
## Pretrained
Please refer to the [tensorrtx](https://github.com/wang-xinyu/tensorrtx) for pretrained models and serialized TensorRT engine.

Or download from [Google driver](https://drive.google.com/drive/folders/1HTdIhGrKP7JnKY6n8F95mI7SBnx7-4R3?usp=sharing).

Now available:
+ yolov5s
+ retinaface
+ arcface

## Usage
To run the demo gui.
```
sh demo.sh
```
Make sure all **PATH** in config files and shell script are right.

## Structure
Class *Pipeline* contains all basic operations about *Gstreamer-pipeline*.

Class *Source_Pool* contains operations about input sources.

To control the *Gstreamer-pipeline*, two parallel threading are necessary.

[api doc](./api-doc.md)