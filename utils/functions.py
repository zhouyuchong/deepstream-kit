
def cal_squre(obj_meta):
    rect_params = obj_meta.rect_params
    top = int(rect_params.top)
    left = int(rect_params.left)
    width = int(rect_params.width)
    height = int(rect_params.height)

def crop_object(image, list):
    # rect_params = obj_meta.rect_params
    top = int(list[0])
    left = int(list[1])
    width = int(list[2])
    height = int(list[3])
    # obj_name = pgie_classes_str[obj_meta.class_id]

    crop_img = image[top:top+height, left:left+width]
	
    return crop_img
