
obj_ROI = []
face_deteced = []

class Counter:
    def new_obj(id):
        if id in obj_ROI:
            return False
        else:
            obj_ROI.append(id)
            return True 
    
    def new_face(id):
        if id in face_deteced:
            return False
        else:
            face_deteced.append(id)
            return True