# Deepstream Kit
客制化deepstream接口

## 环境配置
+ Deepstream 6.0.1+
+ GStreamer 1.14.5
+ Cuda 11.4+
+ NVIDIA driver 470.63.01+
+ TensorRT 8+
+ Python 3.6   

请按照[官方文档](https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_Quickstart.html#dgpu-setup-for-ubuntu)安装相关依赖。

## 预训练模型
请按照[tensorrtx](https://github.com/wang-xinyu/tensorrtx)来预训练与序列化你想使用的TensorRT引擎。

或者从[谷歌网盘](https://drive.google.com/drive/folders/1HTdIhGrKP7JnKY6n8F95mI7SBnx7-4R3?usp=sharing)下载。

现支持的模型:
+ yolov5s
+ retinaface
+ arcface

## 使用方式
在运行之前，请确保所有的**路径变量**正确。

运行demo程序.
```
python3 gui.py
```

1. Choose the mode: 
   1. OSD: on screen display
   2. Record: back stage
2. Add resource:
   You can add resource before the pipeline starts or during the runtime.
   1. URI: uri of rtsp stream input.
   2. UID/name/framerate: 
      1. unique id of each source, can't be re-used.
      2. name of source
      3. set max framerate of the source, notice only works if set-framerate is smaller than the source's own max framerate.
   3. enable/inROI/class-id/area:
      1. enable the analytics or not
      2. inROI to count object inside/outside the ROI
      3. class-id to count a specific class
      4. area:start with the name of this area, followed with vertexes in pairs spaced with commas. e.g. area1,500;500;1400;500;1400;900;500;900
3. Play: start pipeline.
4. Stop: stop the whole pipeline.
5. Quit: quit app.
6. Delete: 
   1. delete uid: input the uid of source you want to delete, then press DELETE button.
7. Get state of a specific source: doble click a source in listbox.

## Structure
Class *Pipeline* contains all basic operations about *Gstreamer-pipeline*.

Class *Source_Pool* contains operations about input sources.

To control the *Gstreamer-pipeline*, two parallel threading are necessary.

[api doc](./api-doc.md)