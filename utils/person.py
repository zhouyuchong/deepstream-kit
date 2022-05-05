import threading
import numpy as np
import cv2

from utils.functions import crop_object

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
        self.frame_id = 0
        self.source_id = 0
        self.gender = "male" 
        self.clothes = "black"
        self.age = 30
        self.gesture = "walk"
        self.face_feature = None
        self.roi = []
        self.timestamp = None
        self.background_image = None
        self.body_image = None
        self.face_image = None
        self.msg_flag = False
        self.save_bg_flag = None
        self.save_face_flag = None
        self.save_body_flag = None
        self.save_face_feature_flag = None
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

    def set_timestamp(self, ts):
        self.timestamp = ts

    def set_back_image(self, array):
        self.background_image = array

    def set_body_image(self, array):
        self.body_image = array

    def set_face_image(self, array):
        self.face_image = array

    def set_msg_flag(self, flag):
        self.msg_flag = flag
    def set_save_bg_flag(self, flag):
        self.save_bg_flag = flag
    def set_save_body_flag(self, flag):
        self.save_body_flag = flag
    def set_save_face_flag(self, flag):
        self.save_face_flag = flag
    def set_save_face_feature_flag(self, flag):
        self.save_face_feature_flag = flag
#################################################################
    def get_person_id(self):
        return self.person_id_coor[0]
    def get_frame_id(self):
        return self.frame_id
    def get_source_id(self):
        return self.source_id

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
    def get_save_bg_flag(self):
        return self.save_bg_flag
    def get_save_body_flag(self):
        return self.save_body_flag
    def get_save_face_flag(self):
        return self.save_face_flag
    def get_save_face_feature_flag(self):
        return self.save_face_feature_flag

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

    def save_bg_to_local(self):
        if not self._lock.acquire(timeout=self._timeout):
            print("Fail to acquire lock, maybe busy")
            return False
        bg = np.array(self.background_image, copy=True, order='C')
        bg = cv2.cvtColor(bg, cv2.COLOR_RGBA2BGRA)
        img_path = "save_img/background/{0}-{1}-{2}.jpg".format(self.person_id_coor[0], self.source_id, self.timestamp)
        cv2.imwrite(img_path, bg)
        self._lock.release()

    def save_body_to_local(self):
        if not self._lock.acquire(timeout=self._timeout):
            print("Fail to acquire lock, maybe busy")
            return False
        body = crop_object(self.background_image, self.person_id_coor[1:])
        body = np.array(body, copy=True, order='C')
        body = cv2.cvtColor(body, cv2.COLOR_RGBA2BGRA)
        img_path = "save_img/body/{0}-{1}-{2}.jpg".format(self.person_id_coor[0], self.source_id, self.timestamp)
        cv2.imwrite(img_path, body)
        self._lock.release()

    def save_face_to_local(self):
        if not self._lock.acquire(timeout=self._timeout):
            print("Fail to acquire lock, maybe busy")
            return False
        face = crop_object(self.background_image, self.face_id_coor[1:])
        face = np.array(face, copy=True, order='C')
        face = cv2.cvtColor(face, cv2.COLOR_RGBA2BGRA)
        img_path = "save_img/face/{0}-{1}-{2}.jpg".format(self.person_id_coor[0], self.source_id, self.timestamp)
        cv2.imwrite(img_path, face)
        self._lock.release()

    def save_face_feature_to_local(self):
        if not self._lock.acquire(timeout=self._timeout):
            print("Fail to acquire lock, maybe busy")
            return False
        ff = self.face_feature
        img_path = "save_img/face_feature/{0}-{1}-{2}.npy".format(self.person_id_coor[0], self.source_id, self.timestamp)
        np.save(img_path, ff)
        self._lock.release()
    # def print_info(self):
        # print(self.)

    def print_info_all(self):
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
            for per in people:
                per.print_info_all()
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

    def check_save(self):
        if not self._lock.acquire(timeout=self._timeout):
            print("Fail to acquire lock, maybe busy")
            return False
        for per in people:
            if per.get_save_bg_flag() == True:
                print("save background image to local.")
                per.save_bg_to_local()
                per.set_save_bg_flag(False)
                if per.get_save_body_flag() == True:
                    print("save body to local.")
                    per.save_body_to_local()
                    per.set_save_body_flag(False)
                if per.get_save_face_flag() == True:
                    print("save face to local.")
                    per.save_face_to_local()
                    per.set_save_face_flag(False)
                    if per.get_save_face_feature_flag() == True:
                        print("save feature to local.")
                        per.save_face_feature_to_local()
                        per.set_save_face_feature_flag(False)
            
        self._lock.release()

    def run(self):
        while True:
            self.check_full()
            # self.check_new()
            self.check_save()
