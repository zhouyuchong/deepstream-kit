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
import time


from utils.fps import Timer
from utils.functions import crop_object
from utils.person import Person_pool, Person_Feature
from ds_kit.ds_message import *
# from torch import tensor

PGIE_ID = 1
SGIE_ID = 2
TGIE_ID = 3

PGIE_CLASS_ID_PERSON = 0
SGIE_CLASS_ID_FACE = 0

SGIE_THRESHOLD = 0.97


def analytics_src_pad_buffer_probe(pad,info, u_data):
    # 初始化一个person pool对象
    person_pool = Person_pool()
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
        # get frame number and souce id
        frame_num = frame_meta.frame_num
        source_id = frame_meta.source_id
        l_obj = frame_meta.obj_meta_list
        while l_obj is not None:
            try:
                # Casting l_obj.data to pyds.NvDsObjectMeta
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
            except StopIteration:
                break
            
            # 如果满足：为yolo检测对象 & 类别为人 & 宽度大于100 & 高度大于300 & tracker-id第一次在场景中出现
            if (obj_meta.unique_component_id==PGIE_ID) and (obj_meta.class_id==PGIE_CLASS_ID_PERSON) and (obj_meta.rect_params.width >= 100) \
                and (obj_meta.rect_params.height >= 300) and (person_pool.id_exist(obj_meta.object_id)==False):
                # 初始化一个person feature对象
                person = Person_Feature()
                # 生成当前时间戳
                ts = time.strftime("%Y%m%d%H:%M:%S", time.localtime())
                # 设置属性
                person.set_frame_id(frame_num)
                person.set_source_id(source_id)
                person.set_timestamp(ts)
                person.set_person_id_coor([obj_meta.object_id, obj_meta.rect_params.top, obj_meta.rect_params.left, \
                    obj_meta.rect_params.width, obj_meta.rect_params.height])
                # should set send-message flag to true
                person.set_msg_flag(flag=True)
                person.set_save_body_flag(True)
                # person.set_save_flag(flag=True)
                # 将新检测到的人员添加到池中
                person_pool.add(person)

            try:
                l_obj = l_obj.next
            except StopIteration:
                break

        # 第一次循环后，帧中所有的人员应该都在池中了，此时判断人员的其他信息
        l_obj = frame_meta.obj_meta_list
        while l_obj is not None:
            try:
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
            except StopIteration:
                break
            
            # 如果该检测物为retinaface推理结果 & 父辈为yolo & 宽度大于64 & 高度大于64 & 置信度大于阈值
            if (obj_meta.unique_component_id==SGIE_ID) and (obj_meta.parent.unique_component_id == PGIE_ID) \
                    and (obj_meta.rect_params.width >= 50) and (obj_meta.rect_params.height >= 50) \
                    and (obj_meta.confidence > SGIE_THRESHOLD):
                
                # 因为有脸一定是添加过的人了，所以这里不判断id_exist应该也可行
                temp_person = person_pool.get_person_by_id(obj_meta.parent.object_id)
                # 检查该人员是否已经有脸
                if(temp_person.check_face_finished()==False):
                    temp_person.set_face_id_coor([obj_meta.object_id, obj_meta.rect_params.top, obj_meta.rect_params.left, obj_meta.rect_params.width, obj_meta.rect_params.height])
                    temp_person.set_save_face_flag(True)
                    # 获取该脸的arcface推理结果
                    l_user_meta = obj_meta.obj_user_meta_list
                    while l_user_meta:
                        try:
                            user_meta = pyds.NvDsUserMeta.cast(l_user_meta.data) #Must cast glist data to NvDsUserMeta object
                        except StopIteration:
                            break
                        if user_meta and user_meta.base_meta.meta_type==pyds.NvDsMetaType.NVDSINFER_TENSOR_OUTPUT_META: 
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
                            temp_person.set_face_feature(normal_array)
                            temp_person.set_save_face_feature_flag(True)
                            # break

                        try:
                            l_user_meta = l_user_meta.next
                        except StopIteration:
                            break
                    # because there is a new face being detected, should set the send-message flag to true
                    temp_person.set_msg_flag(True)

            # 获取当前object的ROI信息
            # 尝试获取对应id的person对象
            if person_pool.id_exist(obj_meta.object_id):
                person = person_pool.get_person_by_id(obj_meta.object_id)
                l_user_meta = obj_meta.obj_user_meta_list
                while l_user_meta:
                    try:
                        user_meta = pyds.NvDsUserMeta.cast(l_user_meta.data) #Must cast glist data to NvDsUserMeta object
                    except StopIteration:
                        break
                    if user_meta.base_meta.meta_type == pyds.nvds_get_user_meta_type("NVIDIA.DSANALYTICSOBJ.USER_META"):    
                        #Must cast user metadata to NvDsAnalyticsObjInfo         
                        user_meta_data = pyds.NvDsAnalyticsObjInfo.cast(user_meta.user_meta_data) 
                        #Access NvDsAnalyticsObjInfo attributes with user_meta_data.{attribute name}
                        # 如果roi中出现了人员，进行判断roi信息是否有变化
                        if (obj_meta.unique_component_id == PGIE_ID):
                            if person.check_roi(user_meta_data.roiStatus):
                                person.set_roi(roi=user_meta_data.roiStatus)
                                # print(user_meta_data.roiStatus)
                                # because there is a roi-state change, should be reported
                                person.set_msg_flag(flag=True)
                    

                    try:
                        l_user_meta = l_user_meta.next
                    except StopIteration:
                        break
            try:
                l_obj = l_obj.next
            except StopIteration:
                break
        
        # 打印fps
        Timer.get_stream_fps(index=frame_meta.pad_index).get_fps()
        try:
            l_frame=l_frame.next
        except StopIteration:
            break
    return Gst.PadProbeReturn.OK


def tiler_sink_pad_buffer_probe(pad,info, u_data):
    person_pool = Person_pool()
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
        source_id = frame_meta.source_id
        while l_obj is not None:
            try:
                # Casting l_obj.data to pyds.NvDsObjectMeta
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
            except StopIteration:
                break
            
            if person_pool.id_exist(obj_meta.object_id):
                person = person_pool.get_person_by_id(obj_meta.object_id)
                if (person.get_back_image() is None) and (person.get_frame_id()==frame_number) and (person.get_source_id()==source_id):
                    n_frame = pyds.get_nvds_buf_surface(hash(gst_buffer), frame_meta.batch_id)

                    # lists = frame_copy.tolist()
                    # json_str = json.dumps(lists)
                    # base64array = str(base64.b64encode(json_str.encode('utf-8')),"utf-8")
                    person.set_back_image(n_frame)
                    if person.get_save_bg_flag() is None:
                        person.set_save_bg_flag(True)

                if person.get_msg_flag() == True:
                    msg_meta = pyds.alloc_nvds_event_msg_meta()
                    msg_meta.bbox.top = obj_meta.rect_params.top
                    msg_meta.bbox.left = obj_meta.rect_params.left
                    msg_meta.bbox.width = obj_meta.rect_params.width
                    msg_meta.bbox.height = obj_meta.rect_params.height
                    msg_meta.frameId = frame_number
                    msg_meta.trackingId = long_to_uint64(obj_meta.object_id)
                    msg_meta.confidence = obj_meta.confidence
                    msg_meta = generate_event_msg_meta(msg_meta, person.get_roi())
                    user_event_meta = pyds.nvds_acquire_user_meta_from_pool(batch_meta)
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
                # 发送过后要记得设置发送信号为假
                person.set_msg_flag(False)
            try:
                l_obj = l_obj.next
            except StopIteration:
                break 

        try:
            l_frame=l_frame.next
        except StopIteration:
            break
    return Gst.PadProbeReturn.OK



def msg_sink_pad_block_probe(pad, info, u_data):
    return Gst.PadProbeReturn.DROP 