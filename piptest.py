import ds_pipeline
import threading


class Mypipeline(threading.Thread):
    def __init__(self, source_number, sinkt="OSD"):
        threading.Thread.__init__(self)
        self.daemon = True
        self.pipeline = ds_pipeline.Pipeline(max_source_num=source_number, sink_type=sinkt) 
        self.pipeline.add_pgie("yolov5")
        
        self.pipeline.add_sgie("retinaface")
        # pipeline.add_sgie("arcface")
        self.pipeline.add_tracker("deepsort")
        self.pipeline.set_ready()
    

    def run(self):
        self.pipeline.start_pipeline()

