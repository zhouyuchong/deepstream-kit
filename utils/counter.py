import threading  
import logging

MAX_NUMBER = 10
person_new = []
person_new_ROI = []
face_deteced = []
face_finished = []

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(module)s:%(funcName)s - %(message)s"
logging.basicConfig(filename='log/ds_kit.log', level=logging.DEBUG, format=LOG_FORMAT)

class Counter(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._lock = threading.Lock()
        self._timeout = 30

    def new_person_scene(id):
        if id in person_new:
            return False
        else:
            person_new.append(id)
            return True

    def new_person_roi(id):
        if id in person_new_ROI:
            return False
        else:
            person_new_ROI.append(id)
            return True 
    
    def new_face(id):
        if id in face_deteced:
            return False
        else:
            face_deteced.append(id)
            return True
    def is_face_finished(id):
        if id in face_finished:
            return False
        else:
            face_finished.append(id)
            return True
    
    def get_all_face():
        return face_deteced

    def get_all_person():
        return person_new_ROI


    def is_full(self):
        if not self._lock.acquire(timeout=self._timeout):
            print("Fail to acquire lock, maybe busy")
            logging.warning("Fail to acquire lock")
            return False
        if len(person_new) >= MAX_NUMBER:
            person_new.clear()
            logging.debug("clear person new list")
        if len(person_new_ROI) >= MAX_NUMBER:
            person_new_ROI.clear()
            logging.debug("clear person new ROI list")
        if len(face_deteced) >= MAX_NUMBER:
            face_deteced.clear()
            logging.debug("class clear face detected list")
        if len(face_finished) >= MAX_NUMBER:
            face_finished.clear()
            logging.debug("clear face finished list")
        self._lock.release()
