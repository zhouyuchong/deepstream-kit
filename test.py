import sys
import source_pool
import create_pip
import time 
import tkinter



def main(args):
    pipeline = create_pip.Pipeline(max_source_num=4, sink_type="OSD", is_live=True)
    pipeline.create_streammux()
    pipeline.add_pgie("yolov5")
    
    pipeline.add_sgie("retinaface")
    # pipeline.add_sgie("arcface")
    pipeline.add_tracker("deepsort")
    pipeline.set_ready()


      
    # att = pipeline.get_all_attribute()
    # print(att)
    # pipeline.temp_add_source("../../videos/london_buses.h264")
    # pipeline.add_source("rtsp://admin:sh123456@192.168.1.237:554/h264/ch1/main/av_stream", 30)
    
    
    t1 = source_pool.Source_Pool(pipeline, 4, 1)
    t1.start()
    t1.add_source_to_pool("rtsp://admin:sh123456@192.168.1.237:554/h264/ch1/main/av_stream", 1, 30, "first")
    pipeline.start_pipeline()
    # time.sleep(10)
    # pipeline.add_source("rtsp://admin:sh123456@192.168.1.234:554/h264/ch1/main/av_stream", 30)
    return

if __name__ == '__main__':
    sys.exit(main(sys.argv))