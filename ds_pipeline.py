import ctypes
import sys

from numpy import uint
sys.path.append('../')
import gi
import configparser
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
from gi.repository import GLib
import sys
import math
import random
import time
import threading
import ctypes

from common.is_aarch_64 import is_aarch64
from common.bus_call import bus_call


# import pyds
import utils.file
from utils.fps import Timer
from ds_probe import tiler_sink_pad_buffer_probe
ctypes.cdll.LoadLibrary('/opt/nvidia/deepstream/deepstream/sources/pythonapps/models/yolov5/yolov5s/libYoloV5Decoder.so')
ctypes.cdll.LoadLibrary('/opt/nvidia/deepstream/deepstream/sources/pythonapps/models/retinaface/libRetinafaceDecoder.so')
ctypes.cdll.LoadLibrary('/opt/nvidia/deepstream/deepstream/sources/pythonapps/models/arcface/libArcFaceDecoder.so')

MAX_SOURCE_NUMBER = 6
MAX_SGIE_NUMBER = 3
# mem_type = int(pyds.NVBUF_MEM_CUDA_UNIFIED)


class Pipeline(object):
    ''' 
    This class contains basic operation of gst-pipeline including init/create, start/end, add/delete resource, 
    Details:
    '''
    def __init__(self, max_source_num, sink_type):
        '''
        + Args:
            1. max_source_num:最大播放源数量
            2. sink_type:输出模式: OSD-屏幕显示(可能一段时间后会宕掉), FAKE-后台, FILE-保存文件(待实现), RTSP(待实现)
        + Members:
            sgie: a list of sgie nvinfer.
            sgie_index: index of sgie list.
            source_bin_list: a list of source bins.
        '''
        self._create_pipeline()
        self.max_source_number = max_source_num
        if sink_type == "OSD":
            print("type:osd")
            self.sink_type = "nveglglessink"
        if sink_type == "FAKE":
            print("type:fake")
            self.sink_type = "fakevideosink"

        self._create_streammux()
        self.sgie = [None] * MAX_SGIE_NUMBER
        self.queue_sgie = [None] * MAX_SGIE_NUMBER
        self.sgie_index = 0
                
        # list of sources_pool controlers
        self.source_bin_list = [None] * max_source_num
        self.source_index_list = [0] * max_source_num
        self.source_enabled = [False] * max_source_num
        self.source_index = 0
        self.source_number = 0

        # list of pipeline source plugins
        self.videorate = [None] * max_source_num
        self.depay = [None] * max_source_num
        self.h264parser = [None] * max_source_num
        self.decoder = [None] * max_source_num
    
    def _create_pipeline(self):
        GObject.threads_init()
        Gst.init(None)

        # Create Pipeline element that will form a connection of other elements
        print("****** Creating Pipeline ******\n ")
        self.pipeline = Gst.Pipeline()

        if not self.pipeline:
            sys.stderr.write(" Unable to create Pipeline \n")

    def add_pgie(self, pgie_name):
        '''
        This funciton create a nvinfer element and a queue. Then set a inference config file of this infer.
        THis function is necessary for creating a gst-pipeline.

        + Args:
            pgie_name: name of pgie, should be supported gie, now available: yolov5/retinaface
        '''    
        print("****** Creating PGIEs ******\n ")
        self.pgie = Gst.ElementFactory.make("nvinfer", "primary-inference")
        self.pipeline.add(self.pgie)
        PGIE_CONFIG_FILE = "config/config_{}.txt".format(pgie_name)
        self.pgie.set_property('config-file-path', PGIE_CONFIG_FILE)

        self.queue_pgie = Gst.ElementFactory.make("queue","queue_pgie")
        self.pipeline.add(self.queue_pgie)

        self.pgie.link(self.queue_pgie)

        print("****** PGIE {} IS SET ******\n".format(pgie_name))
       
    def add_sgie(self, sgie_name):
        '''
        This function create a nvinfer element and a queue. Then set a inference config file of this infer.
        THis function is optional for a gst-pipeline.
        + NOTICE that pgie and sgie CAN NOT be the same inference.

        + Args:
            sgie_name: name of sgie, should be supported gie, now available: yolov5s/retinaface/arcface.
        '''
        self.sgie[self.sgie_index] = Gst.ElementFactory.make("nvinfer", "secondary-nvinference-engine-{}".format(sgie_name))
        self.pipeline.add(self.sgie[self.sgie_index])
        SGIE_CONFIG_FILE = "config/config_{}.txt".format(sgie_name)
        self.sgie[self.sgie_index].set_property('config-file-path', SGIE_CONFIG_FILE)

        self.queue_sgie[self.sgie_index] = Gst.ElementFactory.make("queue","queue_sgie_{}".format(sgie_name))
        self.pipeline.add(self.queue_sgie[self.sgie_index])

        self.sgie[self.sgie_index].link(self.queue_sgie[self.sgie_index])
        self.sgie_index += 1

        print("****** SGIE_{} IS SET ******\n".format(sgie_name))

    def add_tracker(self, tracker_type):
        '''
        This function create a nvtracker elements. Then set a tracker config file.
        + Args:
            tracker_type: type of the tracker, should be supported type, now available: 
                IOU:
                NvDCF(Nv-discriminative correlation filter):
                Deepsort:
        '''
        print("****** Creating nvtracker ******\n ")
        self.tracker = Gst.ElementFactory.make("nvtracker", "tracker")
        if not self.tracker:
            sys.stderr.write(" Unable to create tracker \n")
        
        TRACKER_CONFIG_FILE = 'config/config_tracker.txt'
        #Set properties of tracker
        config = configparser.ConfigParser()
        config.read(TRACKER_CONFIG_FILE)
        config.sections()

        for key in config['tracker']:
            if key == 'tracker-width' :
                tracker_width = config.getint('tracker', key)
                self.tracker.set_property('tracker-width', tracker_width)
            if key == 'tracker-height' :
                tracker_height = config.getint('tracker', key)
                self.tracker.set_property('tracker-height', tracker_height)
            if key == 'gpu-id' :
                tracker_gpu_id = config.getint('tracker', key)
                self.tracker.set_property('gpu_id', tracker_gpu_id)
            if key == 'll-lib-file' :
                tracker_ll_lib_file = config.get('tracker', key)
                self.tracker.set_property('ll-lib-file', tracker_ll_lib_file)
            if key == 'll-config-file' :
                tracker_ll_config_file = config.get('tracker', key)
                self.tracker.set_property('ll-config-file', tracker_ll_config_file)
            if key == 'enable-batch-process' :
                tracker_enable_batch_process = config.getint('tracker', key)
                self.tracker.set_property('enable_batch_process', tracker_enable_batch_process)
        
        self.pipeline.add(self.tracker)

    def _create_streammux(self):
        '''
        This function creates a nvstreammux element. The properties are set by using macro parameter.
        '''
        print("Creating streamux \n ")
        # Create nvstreammux instance to form batches from one or more sources.
        self.streammux = Gst.ElementFactory.make("nvstreammux", "Stream-muxer")
        if not self.streammux:
            sys.stderr.write(" Unable to create NvStreamMux \n")
        self.pipeline.add(self.streammux)
    
        # self.streammux.set_property("nvbuf-memory-type", mem_type)
        # Boolean property to sychronization of input frames using PTS
        self.streammux.set_property('sync-inputs', 1)
        self.streammux.set_property('width', 1280)
        self.streammux.set_property('height', 720)
        self.streammux.set_property('batch-size', self.max_source_number)
        self.streammux.set_property('batched-push-timeout', 4000)
        self.streammux.set_property('live-source', 1)

    def _create_head(self):
        '''
        This function creates decode plugins for rtsp sources
        '''
        for i in range(self.max_source_number):
            self.videorate[i] = Gst.ElementFactory.make("videorate", "videorate%u"%i)
            self.depay[i] = Gst.ElementFactory.make('rtph264depay', "depay%u"%i)
            self.h264parser[i] = Gst.ElementFactory.make("h264parse", "h264-parser%u"%i)
            self.decoder[i] = Gst.ElementFactory.make("nvv4l2decoder", "nvv4l2-decoder%u"%i)
            self.pipeline.add(self.videorate[i])
            self.pipeline.add(self.depay[i])
            self.pipeline.add(self.h264parser[i])
            self.pipeline.add(self.decoder[i])

            self.depay[i].link(self.h264parser[i])
            self.h264parser[i].link(self.decoder[i])
            self.decoder[i].link(self.videorate[i])
        
    def _create_body(self):
        '''
        This function creates nvdsanalytics, nvmultistreamtiler, nvvideoconvert, nvdsosd and sink elements.
        '''
        utils.file.init_analytics_config_file(self.max_source_number)
        print("Creating nvdsanalytics \n ")
        self.nvanalytics = Gst.ElementFactory.make("nvdsanalytics", "analytics")
        if not self.nvanalytics:
            sys.stderr.write(" Unable to create nvanalytics \n")
        #  set an empty init config file to nvanalytics 
        self.nvanalytics.set_property("config-file", "config/config_nvdsanalytics.txt")
        
        # Add nvvidconv1 and filter1 to convert the frames to RGBA
        # which is easier to work with in Python.
        print("Creating nvvidconv1 \n ")
        self.nvvidconv1 = Gst.ElementFactory.make("nvvideoconvert", "convertor1")
        if not self.nvvidconv1:
            sys.stderr.write(" Unable to create nvvidconv1 \n")
        print("Creating filter1 \n ")
        caps1 = Gst.Caps.from_string("video/x-raw(memory:NVMM), format=RGBA")
        self.filter1 = Gst.ElementFactory.make("capsfilter", "filter1")
        if not self.filter1:
            sys.stderr.write(" Unable to get the caps filter1 \n")
        self.filter1.set_property("caps", caps1)

        print("Creating tiler \n ")
        self.tiler=Gst.ElementFactory.make("nvmultistreamtiler", "nvtiler")
        if not self.tiler:
            sys.stderr.write(" Unable to create tiler \n")

        print("Creating nvvidconv \n ")
        self.nvvideoconvert = Gst.ElementFactory.make("nvvideoconvert", "convertor")
        if not self.nvvideoconvert:
            sys.stderr.write(" Unable to create nvvidconv \n")

        print("Creating nvosd \n ")
        self.nvosd = Gst.ElementFactory.make("nvdsosd", "onscreendisplay")
        if not self.nvosd:
            sys.stderr.write(" Unable to create nvosd \n")

        print("Creating EGLSink \n")
        self.sink = Gst.ElementFactory.make(self.sink_type, "nvvideo-renderer")
        if not self.sink:
            sys.stderr.write(" Unable to create egl sink \n")
        
        tiler_rows=int(math.sqrt(self.max_source_number))
        tiler_columns=int(math.ceil((1.0*self.max_source_number)/tiler_rows))
        self.tiler.set_property("rows",tiler_rows)
        self.tiler.set_property("columns",tiler_columns)
        self.tiler.set_property("width", 1280)
        self.tiler.set_property("height", 720)

        self.pipeline.add(self.nvanalytics)
        self.pipeline.add(self.nvvidconv1)
        self.pipeline.add(self.filter1)
        self.pipeline.add(self.tiler)
        self.pipeline.add(self.nvvideoconvert)
        self.pipeline.add(self.nvosd)
        self.pipeline.add(self.sink)
        
    def set_ready(self):
        '''
        Link all elements in the pipeline and wait for the source.
        '''
        self._create_body()
        self._create_head()
        self.streammux.link(self.pgie)
        # self.queue_pgie.link(self.tracker)
        
        # if there are sgies, link them.
        if len([s for s in self.sgie if s is not None]) != 0:
            self.queue_pgie.link(self.sgie[0])
            for i in range(self.sgie_index - 1):
                self.queue_sgie[i].link(self.sgie[i + 1])
            self.queue_sgie[self.sgie_index-1].link(self.tracker)
        else:
            self.queue_pgie.link(self.tracker)
        self.tracker.link(self.nvanalytics)
        self.nvanalytics.link(self.nvvidconv1)
        self.nvvidconv1.link(self.filter1)
        self.filter1.link(self.tiler)
        self.tiler.link(self.nvvideoconvert)
        self.nvvideoconvert.link(self.nvosd)
        self.nvosd.link(self.sink)

        print("****** Link Done. Waiting for Sources ****** \n")
   
    def add_source(self, uri, framerate, analytics_enable, inverse_roi_enable, class_id, **kwargs):
        '''
        This function adds a single source to the pipeline.
        At least one source should be added before the pipeline starts.
        Return True if add successfully.
        + Args:
            uri(string):uri
            framerate(int):framerate
            analytics_enable(boolean):analytics_enable
            inverse_roi_enable(boolean):inverse_roi_enable
            class_id(string):class_id
            **kwargs(dict):
                format:{ROI-name:1;1;1;1;1;1}
                ROI-name(string):name of ROI
                vertexes:at least 3 pairs of int, shoul be valid number.
            
        '''
        self.space_to_add = True
        
        # If the last source_index is used
        # Check if there is a blank spot
        # select an un-enabled source to add
  
        for index in range(self.max_source_number):
            if self.source_enabled[index] == False:
                self.source_index = index
                self.space_to_add = True
                break
        # 如果遍历后无空闲播放位, 返回
        if self.space_to_add == False:
            print("reach the max source number!")
            return False
        
        print("Calling Start %d " % self.source_index)
        

        # set the framerate of source
        self.videorate[self.source_index].set_property("max-rate", framerate)
        self.videorate[self.source_index].set_property("drop-only", 1)

        # create rtspsrc plugin for source
        source_bin = self._create_rtsp_bin(self.source_index, uri)
        if (not source_bin):
            sys.stderr.write("Failed to create source bin. Exiting.")
            exit(1)
        
        # Add source bin to our list and to pipeline
        self.source_bin_list[self.source_index] = source_bin
        self.pipeline.add(self.source_bin_list[self.source_index])

        # Enable the source
        self.source_enabled[self.source_index] = True
        # set the nvanalytics before change the rtspsrc plugin's state
        utils.file.modify_analytics_config_file(max_source_number=self.max_source_number, index=self.source_index, enable=analytics_enable, inverse_roi=inverse_roi_enable, class_id=class_id, **kwargs)
        self.nvanalytics.set_property("config-file", "config/config_nvdsanalytics.txt")


        # Set state of source bin to playing
        # if the pipeline is at PLAYING State, then play the source added immediately.
        # if not, just add sources and wait for the pipeline to start.
        if self.pipeline.get_state(Gst.CLOCK_TIME_NONE)[1] == Gst.State.PLAYING:
            state_return = self.source_bin_list[self.source_index].set_state(Gst.State.PLAYING)
            if state_return == Gst.StateChangeReturn.SUCCESS:
                print("STATE CHANGE SUCCESS\n")

            elif state_return == Gst.StateChangeReturn.FAILURE:
                print("STATE CHANGE FAILURE\n")
                return False
            
            elif state_return == Gst.StateChangeReturn.ASYNC:
                state_return = self.source_bin_list[self.source_index].get_state(Gst.CLOCK_TIME_NONE)

            elif state_return == Gst.StateChangeReturn.NO_PREROLL:
                print("STATE CHANGE NO PREROLL\n")
        
        return True

    def _drop_send_signal(self, message, data):
        '''
        Emitted before each RTSP request is sent, in order to allow the application to modify send parameters or to skip the message entirely.
        '''
        print("Delete rtsp source, drop the PAUSE signal to avoid error.")
        return False

    def _create_rtsp_bin(self, index, uri):
        self.source_index_list[index] = index

        # Create a source GstBin to abstract this bin's content from the rest of the
        # pipeline
        print("Creating rtspsrc for [%s]" % uri) 

        bin_name="source-bin-%02d" % index
        print(bin_name)

        # Source element for reading from the uri.
        bin=Gst.ElementFactory.make("rtspsrc", bin_name)
        if not bin:
            sys.stderr.write(" Unable to create rtspsrc bin \n")
        # We set the input uri to the source element
        bin.set_property("location",uri)

        # Because rtspsrc only has 'sometimes' pad
        # Thus connect to the "pad-added" signal of the rtspsrc which generates a
        # callback once a new pad for raw data has been created by the rtspsrc
        bin.connect("pad-added",self._combine_newpad,self.source_index_list[index])

        return bin

    def delete_source(self, index):
        '''
        This function deletes a single source by given index. Return True if delete successfully.
        '''
        if self.source_bin_list[index] is None:
            print("No match for this index, please check.")
            return False
        if self.source_bin_list[index].get_state(Gst.CLOCK_TIME_NONE)[1] != Gst.State.PLAYING :
            print("State error, current state is {}".format(str(self.source_bin_list[index].get_state(Gst.CLOCK_TIME_NONE)[1])))
            return False
        
        #Disable the source
        self.source_enabled[index] = False
        #Release the source
        print("Calling Stop %d " % index)
        self.source_bin_list[index].connect("before-send", self._drop_send_signal)
        self._stop_release_source(index)

        #Quit if no sources remaining
        if (len([x for x in self.source_enabled if x is True]) == 0):
            self.loop.quit()
            print("All sources stopped quitting\n")
            return False
        return True

    def _stop_release_source(self, index):
        state_return = self.source_bin_list[index].set_state(Gst.State.NULL)

        if state_return == Gst.StateChangeReturn.SUCCESS:
            print("SOURCE BIN STATE CHANGE SUCCESS\n")
            pad_name = "sink_%u" % index
            print(pad_name)
            # Retrieve sink pad to be released
            sinkpad = self.streammux.get_static_pad(pad_name)
            # Send flush stop event to the sink pad, then release from the streammux
            sinkpad.send_event(Gst.Event.new_flush_stop(False))
            self.streammux.release_request_pad(sinkpad)
            print("STREAMMUX STATE CHANGE SUCCESS\n")
            # Remove the source bin from the pipeline
            self.pipeline.remove(self.source_bin_list[index])

        elif state_return == Gst.StateChangeReturn.FAILURE:
            print("STATE CHANGE FAILURE\n")
        
        elif state_return == Gst.StateChangeReturn.ASYNC:
            state_return = self.source_bin_list[index].get_state(Gst.CLOCK_TIME_NONE)
            pad_name = "sink_%u" % index
            print(pad_name)
            sinkpad = self.streammux.get_static_pad(pad_name)
            sinkpad.send_event(Gst.Event.new_flush_stop(False))
            self.streammux.release_request_pad(sinkpad)
            print("STATE CHANGE ASYNC\n")
            self.pipeline.remove(self.source_bin_list[index])

    def _combine_newpad(self, rtspsrc, pad, data):
        print("In combine_newpad\n")
        caps=pad.get_current_caps()
        gststruct=caps.get_structure(0)
        gstname=gststruct.get_name()

        print("gstname=",gstname)
        source_id = data
        # Get the sink pad from rtph264depay and src pad from rtspsrc
        sinkpad = self.depay[source_id].get_static_pad("sink")
        if not sinkpad:
            print("fail to get depay sink pad\n")
        if pad.link(sinkpad) == Gst.PadLinkReturn.OK:
            print("Rtspsrc linked to depay\n")
        else:
            sys.stderr.write("Failed to link decodebin to videorate\n")
        
        # Retrive a sink pad from the streammux and src pad from videorate
        pad_name = "sink_%u" % source_id
        print("pad name:", pad_name)
        srcpad = self.videorate[source_id].get_static_pad("src")
        sinkpad = self.streammux.get_request_pad(pad_name)
        if srcpad.link(sinkpad) == Gst.PadLinkReturn.OK:
            print("videorate linked to streammux")
        else:
            sys.stderr.write("Failed to link videorate to streammux\n")

    def start_pipeline(self):
        Timer(self.max_source_number)
        self.loop = GObject.MainLoop()
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect ("message", bus_call, self.loop)

        # Lets add probe to get informed of the meta data generated, we add probe to
        # the sink pad of the osd element, since by that time, the buffer would have
        # had got all the metadata.
        tiler_sink_pad = self.tiler.get_static_pad("sink")
        if not tiler_sink_pad:
            sys.stderr.write(" Unable to get sink pad \n")
        else:
            tiler_sink_pad.add_probe(Gst.PadProbeType.BUFFER, tiler_sink_pad_buffer_probe, 0)
        """
        osdsinkpad = nvosd.get_static_pad("sink")
        if not osdsinkpad:
            sys.stderr.write(" Unable to get sink pad of nvosd \n")

        osdsinkpad.add_probe(Gst.PadProbeType.BUFFER, osd_sink_pad_buffer_probe, 0)
        """
        # start play back and listen to events
        print("Starting pipeline \n")
        
        self.pipeline.set_state(Gst.State.PLAYING)
        try:
            self.loop.run()
        except:
            pass
        # cleanup
        self.pipeline.set_state(Gst.State.NULL)

    def end_pipeline(self):
        self.pipeline.set_state(Gst.State.NULL)

    def get_source_bin_state(self, index):
        '''
        This function to get state of a source by given index.
        + Return:
            False: if no match.
            String: current state of given source.
        '''
        if self.source_bin_list[index] is not None:
            print("source_bin_list[{}] state : {}".format(index, self.source_bin_list[index].get_state(Gst.CLOCK_TIME_NONE)))
            return self.source_bin_list[index].get_state(Gst.CLOCK_TIME_NONE)[1]
        else:
            return "no match"

    def get_all_attribute(self):
        '''
        Print all members.
        '''
        return self.__dict__


    
class Pipeline_T(threading.Thread):
    def __init__(self, source_number, pgie_name, sgie_name=None, sinkt="OSD"):
        threading.Thread.__init__(self)
        self.daemon = True
        self.pipeline = Pipeline(max_source_num=source_number, sink_type=sinkt) 
        self.pipeline.add_pgie(pgie_name)
        if sgie_name is not None:
            for i in range(len(sgie_name)):
                self.pipeline.add_sgie(sgie_name[i])

        self.pipeline.add_tracker("deepsort")
        self.pipeline.set_ready()
    
    def run(self):
        self.pipeline.start_pipeline()

    def get_pipeline(self):
        return self.pipeline