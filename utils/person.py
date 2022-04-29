import threading


people = []
count = 0
MAX_NUMBER_PERSON = 40

class Person_Feature(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._lock = threading.Lock()
        self._timeout = 30

        self.person_id_coor = []
        self.face_id_coor = []
        self.frame = 0
        self.source_id = 0
        self.gender = "male" 
        self.clothes = "black"
        self.age = 30
        self.gesture = "walk"
        self.face_feature = None
        self.roi = []
        self.background_image = None
        self.body_image = None
        self.face_image = None
        self.msg_flag = False
        self.save_flag = False
        # self.change

    def set_person_id_coor(self, id_coor):
        self.person_id_coor = id_coor

    def set_face_id_coor(self, id_coor):
        self.face_id_coor = id_coor

    def set_frame_id(self, id):
        self.frame_id = id

    def set_source_id(self, id):
        self.source_id = id

    def set_face_image(self, array):
        self.face_image = array

    def set_gender(self, gender):
        self.gender = gender

    def set_clothes(self, clothes):
        self.clothes = clothes

    def set_age(self, age):
        self.age = age
    
    def set_gesture(self, gest):
        self.gesture = gest

    def set_face_feature(self, array):
        self.face_feature = array

    def set_roi(self, roi):
        self.roi = roi

    def set_back_image(self, array):
        self.background_image = array

    def set_body_image(self, array):
        self.body_image = array

    def set_face_image(self, array):
        self.face_image = array

    def set_msg_flag(self, flag):
        self.msg_flag = flag

    def set_save_flag(self, flag):
        self.save_flag = flag
#################################################################
    def get_person_id(self):
        return self.person_id_coor[0]

    def get_msg_flag(self):
        return self.flag

    def get_back_image(self):
        return self.background_image

    def get_body_image(self):
        return self.body_image

    def get_face_image(self):
        return self.face_image

    def get_body_coor(self):
        return self.person_id_coor[1:]

    def get_face_coor(self):
        return self.face_id_coor[1:]

    def get_msg_flag(self):
        return self.msg_flag

    def get_save_flag(self):
        return self.save_flag

    def get_roi(self):
        return self.roi



#################################################################
    def check_roi(self, roi):
        if set(self.roi) == set(roi):
            return False
        else:
            return True

    def check_face_finished(self):
        if len(self.face_id_coor)==0:
            return False
        else:
            return True

    def save_to_local(self):
        if not self._lock.acquire(timeout=self._timeout):
            print("Fail to acquire lock, maybe busy")
            return False

        self._lock.release()

    def print_info(self):
        print(self.__dict__)

class Person_pool(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._lock = threading.Lock()
        self._timeout = 30

    def add(self, person):
        if not self._lock.acquire(timeout=self._timeout):
            print("Fail to acquire lock, maybe busy")
            return False
        people.append(person)
        self._lock.release()
        return True

    def id_exist(self, id):
        for per in people:
            if per.get_person_id() == id:
                return True
        return False

    def get_person_by_id(self, id):
        for per in people:
            if per.get_person_id() == id:
                return per


class Person_thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self._lock = threading.Lock()
        self._timeout = 30
        self.count = len(people)

    def check_new(self):
        if not self._lock.acquire(timeout=self._timeout):
            print("Fail to acquire lock, maybe busy")
            return False
        if self.count != len(people):
            self.count = len(people)
            #for per in people:
                # per.print_info()
            print("person pool number:", self.count)
            print("###################################################################################")

        self._lock.release()

    def check_full(self):
        if self.count >= MAX_NUMBER_PERSON:
            if not self._lock.acquire(timeout=self._timeout):
                print("Fail to acquire lock, maybe busy")
                return False
            people.clear()
            self.count = 0
            self._lock.release()

    def run(self):
        while True:
            self.check_full()
            self.check_new()
