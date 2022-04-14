import sys
sys.path.append('../')
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
from common.is_aarch_64 import is_aarch64
from common.bus_call import bus_call
from common.FPS import GETFPS
from common.utils import long_to_uint64


import pyds
import numpy as np
import base64
import json


from utils.fps import Timer
from utils.counter import Counter
from utils.functions import crop_object
from ds_kit.ds_message import *
# from torch import tensor

PGIE_ID = 1
SGIE_ID = 2
TGIE_ID = 3

PGIE_CLASS_ID_PERSON = 0
SGIE_CLASS_ID_FACE = 0

SGIE_THRESHOLD = 0.97


def analytics_src_pad_buffer_probe(pad,info, u_data):
    gst_buffer = info.get_buffer()
    if not gst_buffer:
        print("Unable to get GstBuffer ")
        return

    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))

    l_frame = batch_meta.frame_meta_list
    while l_frame is not None:
        try:
            # Note that l_frame.data needs a cast to pyds.NvDsFrameMeta
            # The casting is done by pyds.glist_get_nvds_frame_meta()
            # The casting also keeps ownership of the underlying memory
            # in the C code, so the Python garbage collector will leave
            # it alone.
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        except StopIteration:
            break

        l_obj = frame_meta.obj_meta_list
        while l_obj is not None:
            try:
                # Casting l_obj.data to pyds.NvDsObjectMeta
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
            except StopIteration:
                break

            l_user_meta = obj_meta.obj_user_meta_list
            while l_user_meta:
                try:
                    user_meta = pyds.NvDsUserMeta.cast(l_user_meta.data) #Must cast glist data to NvDsUserMeta object
                    if user_meta.base_meta.meta_type == pyds.nvds_get_user_meta_type("NVIDIA.DSANALYTICSOBJ.USER_META"):    
                        #Must cast user metadata to NvDsAnalyticsObjInfo         
                        user_meta_data = pyds.NvDsAnalyticsObjInfo.cast(user_meta.user_meta_data) 
                        #Access NvDsAnalyticsObjInfo attributes with user_meta_data.{attribute name}
                        if user_meta_data.roiStatus and obj_meta.unique_component_id == PGIE_ID: 
                            if Counter.new_obj(id=obj_meta.object_id):
                                print("Object {0} roi status: {1}".format(obj_meta.object_id, user_meta_data.roiStatus))
                                # n_frame = pyds.get_nvds_buf_surface(hash(gst_buffer), frame_meta.batch_id)
                                # if n_frame is not None:
                                    # print("get surface")
                except StopIteration:
                    break

                try:
                    l_user_meta = l_user_meta.next
                except StopIteration:
                    break
            # if (obj_meta.unique_component_id == PGIE_ID) and (obj_meta.class_id == PGIE_CLASS_ID_PERSON) and ():

            try:
                l_obj = l_obj.next
            except StopIteration:
                break
        l_obj = frame_meta.obj_meta_list
        while l_obj is not None:
            try:
                # Casting l_obj.data to pyds.NvDsObjectMeta
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
            except StopIteration:
                break
            
            if obj_meta.parent is not None:
                # print(obj_meta.object_id, obj_meta.parent.object_id)
                if (obj_meta.unique_component_id == SGIE_ID) and (obj_meta.parent.unique_component_id == PGIE_ID) \
                    and (Counter.new_obj(obj_meta.parent.object_id) == False) and (obj_meta.confidence > SGIE_THRESHOLD)\
                    and (Counter.new_face(obj_meta.object_id)):
                    print("There is a new face {0} of person {1} be detected in ROI".format(obj_meta.object_id, obj_meta.parent.object_id))
                    print("detected people:", Counter.get_all_person())
                    print("detected faces:", Counter.get_all_face())

            try:
                l_obj = l_obj.next
            except StopIteration:
                break 
        Timer.get_stream_fps(index=frame_meta.pad_index).get_fps()
        # fps_streams["stream{0}".format(frame_meta.pad_index)].get_fps()
        try:
            l_frame=l_frame.next
        except StopIteration:
            break
    return Gst.PadProbeReturn.OK


def tiler_sink_pad_buffer_probe(pad,info, u_data):
    gst_buffer = info.get_buffer()
    if not gst_buffer:
        print("Unable to get GstBuffer ")
        return

    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))

    l_frame = batch_meta.frame_meta_list
    while l_frame is not None:
        try:
            # Note that l_frame.data needs a cast to pyds.NvDsFrameMeta
            # The casting is done by pyds.glist_get_nvds_frame_meta()
            # The casting also keeps ownership of the underlying memory
            # in the C code, so the Python garbage collector will leave
            # it alone.
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        except StopIteration:
            break

        l_obj = frame_meta.obj_meta_list
        frame_number=frame_meta.frame_num
        while l_obj is not None:
            try:
                # Casting l_obj.data to pyds.NvDsObjectMeta
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
            except StopIteration:
                break

            if (obj_meta.unique_component_id ==SGIE_ID) and (Counter.is_face_finished(obj_meta.object_id) == True) \
                and (Counter.new_face(obj_meta.object_id) == False):
                # print(obj_meta.object_id)
                n_frame = pyds.get_nvds_buf_surface(hash(gst_buffer), frame_meta.batch_id)
                # print(n_frame)
                n_frame = crop_object(n_frame, obj_meta)
                frame_copy = np.array(n_frame, copy=True, order='C')
                l_user = obj_meta.obj_user_meta_list
                while l_user is not None:
                    try:
                        # Note that l_user.data needs a cast to pyds.NvDsUserMeta
                        # The casting is done by pyds.NvDsUserMeta.cast()
                        # The casting also keeps ownership of the underlying memory
                        # in the C code, so the Python garbage collector will leave
                        # it alone
                        user_meta=pyds.NvDsUserMeta.cast(l_user.data) 
                    except StopIteration:
                        break
                    
                    # Check data type of user_meta 
                    if(user_meta and user_meta.base_meta.meta_type==pyds.NvDsMetaType.NVDSINFER_TENSOR_OUTPUT_META): 
                        try:
                            tensor_meta = pyds.NvDsInferTensorMeta.cast(user_meta.user_meta_data)
                        except StopIteration:
                            break
                        
                        layer = pyds.get_nvds_LayerInfo(tensor_meta, 0)
                        output = []
                        for i in range(512):
                            output.append(pyds.get_detections(layer.buffer, i))
                        
                        res = np.reshape(output,(512,-1))
                        norm=np.linalg.norm(res)
                    
                        normal_array = res / norm
                        break
                    
                    try:
                        l_user=l_user.next
                    except StopIteration:
                        break            
                
                print("get surface: ", frame_copy, "  facial feature: ", normal_array)
                msg_meta = pyds.alloc_nvds_event_msg_meta()
                msg_meta.bbox.top = obj_meta.rect_params.top
                msg_meta.bbox.left = obj_meta.rect_params.left
                msg_meta.bbox.width = obj_meta.rect_params.width
                msg_meta.bbox.height = obj_meta.rect_params.height
                msg_meta.frameId = frame_number
                msg_meta.trackingId = long_to_uint64(obj_meta.object_id)
                msg_meta.confidence = obj_meta.confidence
                lists = frame_copy.tolist()
                json_str = json.dumps(lists)
                base64array = str(base64.b64encode(json_str.encode('utf-8')),"utf-8")
                # pickle_str = pickle.dumps(frame_copy)
                msg_meta = generate_event_msg_meta(msg_meta, base64array)
                user_event_meta = pyds.nvds_acquire_user_meta_from_pool(
                    batch_meta)
                if user_event_meta:
                    user_event_meta.user_meta_data = msg_meta
                    user_event_meta.base_meta.meta_type = pyds.NvDsMetaType.NVDS_EVENT_MSG_META
                    # Setting callbacks in the event msg meta. The bindings
                    # layer will wrap these callables in C functions.
                    # Currently only one set of callbacks is supported.
                    pyds.user_copyfunc(user_event_meta, meta_copy_func)
                    pyds.user_releasefunc(user_event_meta, meta_free_func)
                    pyds.nvds_add_user_meta_to_frame(frame_meta,
                                                     user_event_meta)
                else:
                    print("Error in attaching event meta to buffer\n")
            try:
                l_obj = l_obj.next
            except StopIteration:
                break 
        # Timer.get_stream_fps(index=frame_meta.pad_index).get_fps()
        # fps_streams["stream{0}".format(frame_meta.pad_index)].get_fps()
        try:
            l_frame=l_frame.next
        except StopIteration:
            break
    return Gst.PadProbeReturn.OK