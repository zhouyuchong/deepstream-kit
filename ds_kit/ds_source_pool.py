import threading

class Source_Property():
    def __init__(self, uri, user_id, name, index, framerate=30):
        self._uri = uri 
        self._user_id = user_id      # 用户指定视频ID
        self._framerate = framerate  # 用户指定视频帧率
        self._name = name            # 用户指定视频名称
        self._source_state = None
        self._source_index = index   # pipeline内部source_bin_list对视频的编号, 用于检索视频状态时的检索

    def set_source_index(self, index):
        self._source_index = index

    def set_source_state(self, state):
        self._source_state = state
    
    def get_source_state(self):
        return self._source_state

    def get_user_id(self):
        return self._user_id
    
    def get_uri(self):
        return self._uri

    def get_framerate(self):
        return self._framerate

    def get_source_index(self):
        return self._source_index

    def get_all_member(self):
        return self._source_index, self._user_id, self._name, self._uri, self._source_state


class Source_Pool(threading.Thread):
    def __init__(self, pipeline, max_source_number, timeout=None):
        threading.Thread.__init__(self)
        self._lock = threading.Lock()
        self.pipeline = pipeline
        self.max_source_number = max_source_number
        self._timeout = timeout
        self.pool_index = 0
        self._create_pool()
    
    def _create_pool(self):
        self.pool = [None] * self.max_source_number

    def add_source_to_pool(self, uri, user_id, framerate, name, analytics_enable, inverse_roi_enable, class_id, **kwargs):
        '''
        This function adds a single source to the source_pool.
        At least one source should be added before the pipeline starts.
        + Args:
            uri(string):uri
            userid:uid
            framerate(int):framerate
            name:source name
            analytics_enable(boolean):analytics_enable
            inverse_roi_enable(boolean):inverse_roi_enable
            class_id(string):class_id
            **kwargs(dict):
                format:{ROI-name:1;1;1;1;1;1}
                ROI-name(string):name of ROI
                anchors:at least 3 pairs of int, shoul be valid number.
            
        '''
        if user_id in [x.get_user_id() for x in self.pool if x is not None]:
            print("already exists")
            return False

        if not self._lock.acquire(timeout=self._timeout):
            print("Fail to acquire lock, maybe busy")
            return False
        self.pipeline.add_source(uri, framerate, analytics_enable, inverse_roi_enable, class_id, **kwargs)
        self.pool_index = self.pipeline.source_index
        # print(self.pipeline.source_index)
        self.pool[self.pool_index] = Source_Property(uri=uri, user_id=user_id, framerate=framerate, name=name, index=self.pool_index)

        #self.pool[self.pool_index].set_source_index(self.pool_index)
        # print(self.pool[self.pool_index].get_source_index())
        

        self.pool_index += 1

        self._lock.release()
        return True

    def delete_source_from_pool_by_id(self, uid):
        if not self._lock.acquire(timeout=self._timeout):
            print("Fail to acquire lock, maybe busy")
            return False
        self.d_index = self.get_index_by_uid(uid)
        # print(self.d_index, type(self.d_index))
        self.pipeline.delete_source(self.d_index)
        self.pool[self.d_index] = None

        self._lock.release()
         
    def get_source_from_pool_by_id(self, uid): 
        for s in self.pool:
            if s is not None and s.get_user_id() == uid:
                s.set_source_state(self.pipeline.get_source_bin_state(s.get_source_index()))
                return s
        print("No result for {}".format(uid))
        return "No result"

    def get_source_state_by_id(self, uid):
        for s in self.pool:
            if s is not None and s.user_id == uid:
                return True, self.pipeline.get_source_bin_state(s.get_source_index())

        return False, "No match, please check if user_id is correct!"
    
    def get_index_by_uid(self, uid):
        for s in self.pool:
            if (s is not None) and s.get_user_id() == uid:
                return s.get_source_index()
        print("No match")
        return False

    def end_pipeline(self):
        self.pipeline.end_pipeline()
        print("end pipeline")