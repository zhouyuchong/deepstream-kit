# title
## Pipeline
### 成员变量
+ **max_source_number**: *Int* 最大资源数, 用于play_list与tiler osd显示布局
+ **sink_type**: *String* 输出模式: 后台(FAKE)/屏幕(OSD)/文件(FILE)
+ sgie: *List* 次级推理引擎列表, 最大数量为MAX_SGIE_NUMBER
+ queue_sgie: *List* 次级推理引擎缓冲, 每个sgie后连接一个
+ sgie_index: *Int* 次级推理引擎编号
+ source_bin_list: *List*  *gst-source-bin*对象列表
+ source_index_list: *List* 对应source_bin_list存在的索引, 使得查询，连接，删除等操作可能
+ source_enabled: *Boolean List*
+ source_index: *Int* 
+ source_number: *Int* 总共的资源计数

### 成员函数
+ 私有
  + _create_pipeline:创建gst-pipeline
  + _create_streammux:
  + _create_body:
  + _create_uridecode_bin:
  + _cb_newpad:
  + _decodebin_child_added
  + _stop_release_source

+ 公有
  + get_all_attribute: 返回所有成员变量
  + add_pgie(pgie_name):
  + add_sgie(sgie_name):
  + add_tracker(tracker_type):
  + add_source(uri, framerate):
  + delete_source(index):
  + set_ready: 连接所有组件，等待输入
  + start_pipeline: 开始pipeline
  + end_pipeline: 停止pipeline
  + get_source_bin_state(index): 获取指定index的资源状态
  




## Source Pool
### 成员变量
+ _lock: 线程锁
+ pipeline: ds_pipeline库Pipeline类
+ **max_source_number**: *Int* 池中最大资源数量
+ **timeout**: 最大等待时间, 添加资源时使用
+ pool_index: *Int* [0, max_source_number), 池中存在的资源编号, 与*Pipeline*中的source_index同步
+ pool: *List*  *Source_Property*列表，保存source相关信息，与*Pipeline*中的source_bin_list保存同步
### 成员函数
+ 私有
  + create_pool:*List* 根据max_source_number创建池 成员变量pool
+ 公有
  + add_source_to_pool(uri, uid, framerate, name): MT safe
  + get_source_from_pool(uid):获取指定uid的Source Property
  + get_source_state(uid):获取指定uid的Source的index, 再根据index调用Pipeline方法获取source状态


## Source Property
### 成员变量
+ **_uri**: *String* uri
+ **_user_id**: *String* 外部传入视频ID
+ **_name**: *String* 外部指定视频名称
+ **_source_index**: *Int* 内部参数, 用于使用调用pipeline方法检索source状态
+ _framerate: *Int* 外部指定视频最大帧率, 默认为30
+ 
### 成员函数
+ 公有
  + 所有成员变量的set & get方法
  + get_all_member:返回所有成员变量


## 使用方法
1. 基本概念
   应用程序应该包含两个基本线程
   + ***ds_pipeline.Pipeline_T***, Gst pipeline的相关方法实现
   + ***ds_source_pool***,  资源池， 对资源的增删查改接口
2. 