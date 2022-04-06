import sys
from optparse import OptionParser
import time

import ds_source_pool
import ds_pipeline

def main(args):
    pipeline_thread = ds_pipeline.Pipeline_T(source_number=4, sinkt='OSD', pgie_name='yolov5', sgie_name=['retinaface', 'arcface'])
    source_pool_thread = ds_source_pool.Source_Pool(pipeline=pipeline_thread.get_pipeline(), \
        max_source_number=4, timeout=10)
    source_pool_thread.start()
    uri1 = 'rtsp://admin:sh123456@192.168.1.235:554/h264/ch1/main/av_stream'
    uri2 = "rtsp://admin:sh123456@192.168.1.237:554/h264/ch1/main/av_stream"
    uri3 = 'rtsp://admin:sh242@192.168.1.239:554/h264/ch1/main/av_stream'
    signal = source_pool_thread.add_source_to_pool(uri=uri2, user_id=1, framerate=33, name='001')
    # wait(5)
    while signal:
        pipeline_thread.start()
        # pipeline_thread.join()
    time.sleep(10)

    source_pool_thread.end_pipeline()


    return
if __name__ == '__main__':
    # ret = parse_args()
    # If argument parsing fails, returns failure (non-zero)
    # if ret == 1:
        # sys.exit(1)
    sys.exit(main(sys.argv))