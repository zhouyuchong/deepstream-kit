import tkinter as tk
import sys
from ds_kit.ds_pipeline import *
from ds_kit.ds_source_pool import *
from ds_kit.ds_controller import *
from utils.person import Person_thread
# import piptest

class GUI_window():
    def __init__(self) -> None:
        self.root = tk.Tk() 
        self.root.title('Deepstream GUI test')
        self.root.geometry("1000x800")
        self.l1 = tk.Label(self.root,text="Mode Choose",font=("Courier", 16, "italic")).grid(row=0, column=0, columnspan=2)
        self.OsdB = tk.Button(self.root, text="OSD", width=10, height=3, state='normal', command=self.osd_b_callback)
        self.OsdB.grid(row=1, column=0)

        self.RecordB = tk.Button(self.root, text="Record", width=10, height=3, state='normal', command=self.record_b_callback)
        self.RecordB.grid(row=1,column=1)
        self.PlayB = tk.Button(self.root, text="Play", width=10, height=3, command=self.play_b_callback).grid(row=1, column=3)
        self.StopB = tk.Button(self.root, text="Stop", width=10, height=3, state='disabled', command=self.stop_b_callback)
        self.StopB.grid(row=1, column=4)
        self.unablemsgB = tk.Button(self.root, text="unable msg", width=10, height=3, command=self.unable_msg_b_cb)
        self.unablemsgB.grid(row=2, column=4)
        self.enablemsgB = tk.Button(self.root, text="enable msg", width=10, height=3, command=self.enable_msg_b_cb)
        self.enablemsgB.grid(row=3, column=4)
        
        self.OutputText = tk.Text(self.root)
        self.OutputText.grid(row=2, column=0, rowspan=2, columnspan=4)

        self.AddB = tk.Button(self.root, text="Add Source", width=10, height=2, command=self.add_b_callback).grid(row=4, column=0)
        self.QuitB = tk.Button(self.root, text="Quit", width=10, height=2, command=self.quit).grid(row=4, column=5)

        self.uri_label = tk.Label(self.root, text="URI", height=1,width=10).grid(row=5, column=0)
        self.u_n_f_label = tk.Label(self.root, text="UID/name/framerate", height=1,width=20).grid(row=6, column=0)
        self.ROI_label = tk.Label(self.root, text="enable/inROI/class-id/area", height=1,width=20).grid(row=7, column=0)
        # self.name_label = tk.Label(self.root, text="name=", height=1,width=10).grid(row=8, column=0)

        self.uri_input = tk.Text(self.root, height=1,width=30)
        self.uri_input.grid(row=5, column=1)
        self.u_n_f_input = tk.Text(self.root, height=1, width=30)
        self.u_n_f_input.grid(row=6, column=1)
        self.e_i_c_a_input = tk.Text(self.root, height=1,width=30)
        self.e_i_c_a_input.grid(row=7, column=1)
        # self.name_input = tk.Text(self.root, height=1,width=10)
        # self.name_input.grid(row=8, column=1)

        self.ds_slist = tk.Listbox(self.root, height=6, width=50, selectmode = tk.EXTENDED)
        self.ds_slist.grid(row=5, column=2, rowspan=3, columnspan=3)
        self.ds_slist.bind('<Double-Button-1>',lambda e: self.display_info())
        
        self.delete_label = tk.Label(self.root, text="delete uid", height=1,width=10).grid(row=5, column=5)
        self.delete_input = tk.Text(self.root, height=1,width=10)
        self.delete_input.grid(row=6, column=5)
        self.DeleteB = tk.Button(self.root, text="delete", width=10, height=2, command=self.delete_b_callback)
        self.DeleteB.grid(row=7, column=5)

        self.root.grid_rowconfigure((0,1,2,3,4,5,6,7,8), weight=1)
        self.root.grid_columnconfigure((0,1,2,3,4,5), weight=1)

        self.root.mainloop()
        

    def play_b_callback(self):
        self.OutputText.insert(tk.INSERT, "pipeline start \n")
        self.StopB['state'] = 'normal'
        self.person_thread.start()
        self.pipeline_thread.start()


    def add_b_callback(self):
        '''self.uri = self.uri_input.get(1.0, "end-1c")
        s_information = self.u_n_f_input.get(1.0, "end-1c")
        s_information = s_information.split(",")

        self.uid = s_information[0]
        self.name = s_information[1]
        self.framerate = int(s_information[2])

        roi_information = self.e_i_c_a_input.get(1.0, "end-1c")
        roi_information = roi_information.split(",")
        area =  dict()
        for i in range(3, len(roi_information), 2):
            area[roi_information[i]] = roi_information[i+1]
        # area = {roi_information[3]:roi_information[4]}
        
        # signale = self.ds_pool.add_source_to_pool(self.uri, self.uid, self.framerate, self.name, \
            # int(roi_information[0]), int(roi_information[1]), int(roi_information[2]), **area)
        if signale:
            self.OutputText.insert(tk.INSERT, "add source frome {}\n".format(self.uri))
            self.ds_slist.insert("end", self.ds_pool.get_source_from_pool_by_id(self.uid).get_all_member())
        else:
            self.OutputText.insert(tk.INSERT, "uid already exists, fail")
        self.uri_input.delete(1.0,tk.END)
        self.u_n_f_input.delete(1.0,tk.END)
        self.e_i_c_a_input.delete(1.0, tk.END)
        # self.name_input.delete(1.0, tk.END)'''

        a1 = {'area':'0;0;1400;0;1400;900;0;900'}
        signale = self.ds_pool.add_source_to_pool('rtsp://admin:sh123456@192.168.1.235:554/h264/ch1/main/av_stream', 1, 20, '001', 1, 0, 0, **a1)
        self.ds_pool.add_source_to_pool('rtsp://admin:sh242@192.168.1.239:554/h264/ch1/main/av_stream', 2, 20, '002', 1, 0, 0, **a1)
        self.ds_pool.add_source_to_pool('rtsp://admin:sh123456@192.168.1.233:554/h264/ch1/main/av_stream', 3, 20, '003', 1, 0, 0, **a1)
        self.ds_pool.add_source_to_pool('rtsp://admin:sh123456@192.168.1.234:554/h264/ch1/main/av_stream', 4, 20, '004', 1, 0, 0, **a1)

    def delete_b_callback(self):
        self.d_uid = self.delete_input.get(1.0, "end-1c")
        print("text get uid is:", self.d_uid)
        self.ds_pool.delete_source_from_pool_by_id(self.d_uid)
        self.OutputText.insert(tk.INSERT, "delete source : {}\n".format(self.d_uid))
        self.delete_input.delete(1.0, tk.END)


    def stop_b_callback(self):
        self.ds_pool.end_pipeline()
        self.OsdB['state'] = 'normal'
        self.RecordB['state'] = 'normal'
        self.temp_list_size = self.ds_slist.size()
        for i in range(self.temp_list_size):
            self.ds_slist.delete(self.temp_list_size - 1 - i)
        self.StopB['state'] = 'disabled'

    def quit(self):
        self.root.destroy()

    def record_b_callback(self):
        self.pipeline_thread = Pipeline_T(source_number=4, pgie_name='yolov5', sgie_name=['retinaface', 'arcface'], sinkt="FAKE")
        self.controller = Pipeline_Controller(pipeline=self.pipeline_thread.get_pipeline())
        self.person_thread = Person_thread()
        self.OutputText.insert(tk.INSERT, "pipeline set to ready \n")
        self.ds_pool = Source_Pool(self.pipeline_thread.get_pipeline(), 4, 1)
        self.ds_pool.start()
        self.RecordB['state'] = 'disabled'
        self.OsdB['state'] = 'disabled'

    def osd_b_callback(self):
        self.pipeline_thread = Pipeline_T(source_number=4, pgie_name='yolov5', sgie_name=['retinaface', 'arcface'], sinkt="OSD")
        self.person_thread = Person_thread()

        self.OutputText.insert(tk.INSERT, "pipeline set to ready \n")

        self.ds_pool = Source_Pool(self.pipeline_thread.get_pipeline(), 4, 1)
        self.ds_pool.start()
        self.OsdB['state'] = 'disabled'
        self.RecordB['state'] = 'disabled'


    def display_info(self):
        uid = self.ds_slist.get(self.ds_slist.curselection())[1]
        self.show_s = self.ds_pool.get_source_from_pool_by_id(uid)
        self.OutputText.insert(tk.INSERT, self.show_s.get_all_member())
        self.OutputText.insert(tk.INSERT, "\n")

    def unable_msg_b_cb(self):
        self.controller.change_msg_state(state="unable")

    def enable_msg_b_cb(self):
        self.controller.change_msg_state(state="enable")
    




if __name__ == '__main__':
    GUI_window()