import sys
sys.path.append('../')
import gi
import configparser
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
from gi.repository import GLib
import sys
import math
from common.is_aarch_64 import is_aarch64
from common.bus_call import bus_call
import collections
import random
import time
import threading



import pyds

MAX_SOURCE_NUMBER = 6
MAX_SGIE_NUMBER = 3
mem_type = int(pyds.NVBUF_MEM_CUDA_UNIFIED)

class Pipeline(object):
    ## parameters:
    ## 1. 最大播放源数量
    ## 2. 输出模式
    ## 3. 是否实时
    def __init__(self, max_source_num, sink_type):
        self._create_pipeline()
        self.max_source_number = max_source_num
        if sink_type == "OSD":
            self.sink_type = "nveglglessink"
        if sink_type == "FAKE":
            self.sink_type = "fakevideosink"

        self._create_streammux()
        self.sgie = [None] * MAX_SGIE_NUMBER
        self.queue_sgie = [None] * MAX_SGIE_NUMBER
        self.sgie_index = 0
                
        self.source_bin_list = [None] * max_source_num
        self.source_index_list = [0] * max_source_num
        self.source_enabled = [False] * max_source_num
        self.source_index = 0
        self.source_number = 0

    def _create_pipeline(self):
        GObject.threads_init()
        Gst.init(None)

        # Create gstreamer elements */
        # Create Pipeline element that will form a connection of other elements
        print("****** Creating Pipeline ******\n ")
        self.pipeline = Gst.Pipeline()

        if not self.pipeline:
            sys.stderr.write(" Unable to create Pipeline \n")


    def add_pgie(self, pgie_name):    
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
        print("Creating streamux \n ")
        # Create nvstreammux instance to form batches from one or more sources.
        self.streammux = Gst.ElementFactory.make("nvstreammux", "Stream-muxer")
        if not self.streammux:
            sys.stderr.write(" Unable to create NvStreamMux \n")
        self.pipeline.add(self.streammux)
    
        self.streammux.set_property("nvbuf-memory-type", mem_type)
        self.streammux.set_property('sync-inputs', 1)
        self.streammux.set_property('width', 1280)
        self.streammux.set_property('height', 720)
        self.streammux.set_property('batch-size', self.max_source_number)
        # 40000 performance better, don't know why
        self.streammux.set_property('batched-push-timeout', 4000)
        self.streammux.set_property('live-source', 1)


    def _create_body(self):
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

        self.pipeline.add(self.tiler)
        self.pipeline.add(self.nvvideoconvert)
        self.pipeline.add(self.nvosd)
        self.pipeline.add(self.sink)
        

    def get_all_attribute(self):
        return self.__dict__

    # after set_ready, everything created in the pipeline before is ready to run
    # except source
    def set_ready(self):
        print("Creating nvdsanalytics \n ")
        self.nvanalytics = Gst.ElementFactory.make("nvdsanalytics", "analytics")
        if not self.nvanalytics:
            sys.stderr.write(" Unable to create nvanalytics \n")
        self.nvanalytics.set_property("config-file", "config/config_nvdsanalytics.txt")
        self.pipeline.add(self.nvanalytics)

        self._create_body()
        self.streammux.link(self.pgie)
        if len([s for s in self.sgie if s is not None]) != 0:
            self.queue_pgie.link(self.sgie[0])
            for i in range(self.sgie_index - 1):
                self.queue_sgie[i].link(self.sgie[i + 1])
            self.queue_sgie[self.sgie_index-1].link(self.tracker)
        else:
            self.queue_pgie.link(self.tracker)
        self.tracker.link(self.nvanalytics)
        self.nvanalytics.link(self.tiler)
        self.tiler.link(self.nvvideoconvert)
        self.nvvideoconvert.link(self.nvosd)
        self.nvosd.link(self.sink)

        print("****** Link Done. Waiting for Sources ****** \n")
   

    def add_source(self, uri, framerate):
        self.nvanalytics.set_property("config-file", "config/config_nvdsanalytics.txt")
        # source_number是一个递增的数，代表总共有多少个source添加过
        # source_index会尝试先等于source_number
        # self.source_index = self.source_number
        self.space_to_add = True
        
        # If the last source_index is used
        # Check if there is a blank spot
        # select an un-enabled source to add
        #if self.source_index >= self.max_source_number:
         #   self.space_to_add = False
         #   self.source_index = 0
        # print("before:", self.source_index)
        for index in range(self.max_source_number):
            if self.source_enabled[index] == False:
                # print(index)
                self.source_index = index
                self.space_to_add = True
                break
        # 如果遍历后无空闲播放位, 返回
        if self.space_to_add == False:
            print("reach the max source number!")
            return False

        print("Calling Start %d " % self.source_index)

        #Create a uridecode bin with the chosen source id
        source_bin = self._create_uridecode_bin(self.source_index, uri)

        if (not source_bin):
            sys.stderr.write("Failed to create source bin. Exiting.")
            exit(1)
        
        #Add source bin to our list and to pipeline
        self.source_bin_list[self.source_index] = source_bin
        self.pipeline.add(self.source_bin_list[self.source_index])

        #Enable the source
        self.source_enabled[self.source_index] = True
        self.source_number += 1

        #Set state of source bin to playing
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

    def delete_source(self, index):
        if self.source_bin_list[index] is None:
            print("No match for this index, please check.")
            return False
        if str(self.source_bin_list[index].get_state(Gst.CLOCK_TIME_NONE)[1]) != "<enum GST_STATE_PLAYING of type Gst.State>":
            print("State error, current state is {}".format(str(self.source_bin_list[index].get_state(Gst.CLOCK_TIME_NONE)[1])))
            return False
        #Disable the source
        self.source_enabled[index] = False
        #Release the source
        print("Calling Stop %d " % index)
        self._stop_release_source(index)

        #Quit if no sources remaining
        if (len([x for x in self.source_enabled if x is True]) == 0):
            self.loop.quit()
            print("All sources stopped quitting")
            return False
        return True

    def _stop_release_source(self, index):
        state_return = self.source_bin_list[index].set_state(Gst.State.NULL)

        if state_return == Gst.StateChangeReturn.SUCCESS:
            print("STATE CHANGE SUCCESS\n")
            pad_name = "sink_%u" % index
            print(pad_name)
            #Retrieve sink pad to be released
            sinkpad = self.streammux.get_static_pad(pad_name)
            #Send flush stop event to the sink pad, then release from the streammux
            sinkpad.send_event(Gst.Event.new_flush_stop(False))
            self.streammux.release_request_pad(sinkpad)
            print("STATE CHANGE SUCCESS\n")
            #Remove the source bin from the pipeline
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

    def _create_uridecode_bin(self, index,filename):
        print("Creating uridecodebin for [%s]" % filename) 

        # Create a source GstBin to abstract this bin's content from the rest of the
        # pipeline
        self.source_index_list[index] = index
        bin_name="source-bin-%02d" % index
        print(bin_name)

        # Source element for reading from the uri.
        # We will use decodebin and let it figure out the container format of the
        # stream and the codec and plug the appropriate demux and decode plugins.
        bin=Gst.ElementFactory.make("uridecodebin", bin_name)
        if not bin:
            sys.stderr.write(" Unable to create uri decode bin \n")
        # We set the input uri to the source element
        bin.set_property("uri",filename)
        # Connect to the "pad-added" signal of the decodebin which generates a
        # callback once a new pad for raw data has been created by the decodebin
        bin.connect("pad-added",self._cb_newpad,self.source_index_list[index])

        bin.connect("child-added",self._decodebin_child_added,self.source_index_list[index])

        # Set status of the source to enabled
        # g_source_enabled[index] = True

        return bin

    def _cb_newpad(self, decodebin,pad,data):
        print("In cb_newpad\n")
        caps=pad.get_current_caps()
        gststruct=caps.get_structure(0)
        gstname=gststruct.get_name()

        # Need to check if the pad created by the decodebin is for video and not
        # audio.
        print("gstname=",gstname)
        if(gstname.find("video")!=-1):
            source_id = data
            pad_name = "sink_%u" % source_id
            print("pad name:", pad_name)
            #Get a sink pad from the streammux, link to decodebin
            sinkpad = self.streammux.get_request_pad(pad_name)
            if pad.link(sinkpad) == Gst.PadLinkReturn.OK:
                print("Decodebin linked to pipeline")
            else:
                sys.stderr.write("Failed to link decodebin to pipeline\n")

    def _decodebin_child_added(self, child_proxy,Object,name,user_data):
        print("Decodebin child added:", name, "\n")
        if(name.find("decodebin") != -1):
            Object.connect("child-added",self._decodebin_child_added,user_data)   
        if(name.find("nvv4l2decoder") != -1):
            if (is_aarch64()):
                Object.set_property("enable-max-performance", True)
                Object.set_property("drop-frame-interval", 0)
                Object.set_property("num-extra-surfaces", 0)
            else:
                Object.set_property("gpu_id", 0)

    def start_pipeline(self):
        self.loop = GObject.MainLoop()
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect ("message", bus_call, self.loop)

        # Lets add probe to get informed of the meta data generated, we add probe to
        # the sink pad of the osd element, since by that time, the buffer would have
        # had got all the metadata.
        """osdsinkpad = nvosd.get_static_pad("sink")
        if not osdsinkpad:
            sys.stderr.write(" Unable to get sink pad of nvosd \n")

        osdsinkpad.add_probe(Gst.PadProbeType.BUFFER, osd_sink_pad_buffer_probe, 0)"""

        
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
        if self.source_bin_list[index] is not None:
        # print("source_bin_list[{}] state is {}".format(index, self.source_bin_list[index].get_state(Gst.CLOCK_TIME_NONE)))
            print(type(self.source_bin_list[index].get_state(Gst.CLOCK_TIME_NONE)[1]))
            return str(self.source_bin_list[index].get_state(Gst.CLOCK_TIME_NONE)[1])
        else:
            return "no match"

    
