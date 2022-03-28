import tkinter as tk
import ds_pipeline
import source_pool
import piptest

class GUI_window():
    def __init__(self) -> None:
        self.root = tk.Tk() 
        self.root.title('Deepstream GUI test')
        # root.geometry("400x240")
        self.l1 = tk.Label(self.root,text="Mode Choose",font=("Courier", 16, "italic")).grid(row=0, column=1, columnspan=4)
        self.ReadyB = tk.Button(self.root, text="Ready", width=10, height=3, state='normal', command=self.ready_b_callback)
        self.ReadyB.grid(row=1, column=1)

        self.RecordB = tk.Button(self.root, text="Record", width=10, height=3).grid(row=1,column=2)
        self.PlayB = tk.Button(self.root, text="Play", width=10, height=3, command=self.play_b_callback).grid(row=1, column=3)
        self.StopB = tk.Button(self.root, text="Stop", width=10, height=3, state='disabled', command=self.stop_b_callback)
        self.StopB.grid(row=1, column=4)
        
        self.OutputText = tk.Text(self.root)
        self.OutputText.grid(row=2, column=1, rowspan=2, columnspan=4)

        self.AddB = tk.Button(self.root, text="Add Source", width=10, height=2, command=self.add_b_callback).grid(row=4, column=0)
        self.QuitB = tk.Button(self.root, text="Quit", width=10, height=2, command=self.quit).grid(row=4, column=5)

        self.uri_label = tk.Label(self.root, text="URI=", height=1,width=10).grid(row=5, column=0)
        self.uid_label = tk.Label(self.root, text="UID=", height=1,width=10).grid(row=6, column=0)
        self.framerate_label = tk.Label(self.root, text="framerate=", height=1,width=10).grid(row=7, column=0)
        self.name_label = tk.Label(self.root, text="name=", height=1,width=10).grid(row=8, column=0)

        self.uri_input = tk.Text(self.root, height=1,width=10)
        self.uri_input.grid(row=5, column=1)
        self.uid_input = tk.Text(self.root, height=1, width=10)
        self.uid_input.grid(row=6, column=1)
        self.framerate_input = tk.Text(self.root, height=1,width=10)
        self.framerate_input.grid(row=7, column=1)
        self.name_input = tk.Text(self.root, height=1,width=10)
        self.name_input.grid(row=8, column=1)

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
        self.mypipeline.start()

   #  def record_b_callback(self):


    def add_b_callback(self):
        #self.ds_pool.add_source_to_pool("rtsp://admin:sh123456@192.168.1.237:554/h264/ch1/main/av_stream", 1, 30, "first")
        
        self.uri = self.uri_input.get(1.0, "end-1c")
        self.uid = self.uid_input.get(1.0, "end-1c")
        self.framerate = self.framerate_input.get(1.0, "end-1c")
        self.name = self.name_input.get(1.0, "end-1c")
        signale = self.ds_pool.add_source_to_pool(self.uri, self.uid, self.framerate, self.name)
        if signale:
            self.OutputText.insert(tk.INSERT, "add source frome {}\n".format(self.uri))
            self.ds_slist.insert("end", self.ds_pool.get_source_from_pool_by_id(self.uid).get_all_member())
        else:
            self.OutputText.insert(tk.INSERT, "uid already exists, fail")
        self.uri_input.delete(1.0,tk.END)
        self.uid_input.delete(1.0,tk.END)
        self.framerate_input.delete(1.0, tk.END)
        self.name_input.delete(1.0, tk.END)

    def delete_b_callback(self):
        self.d_uid = self.delete_input.get(1.0, "end-1c")
        print("text get uid is:", self.d_uid)
        self.ds_pool.delete_source_from_pool_by_id(self.d_uid)
        self.OutputText.insert(tk.INSERT, "delete source : {}\n".format(self.d_uid))
        self.delete_input.delete(1.0, tk.END)

    def stop_b_callback(self):
        self.ds_pool.end_pipeline()
        self.ReadyB['state'] = 'normal'
        self.temp_list_size = self.ds_slist.size()
        for i in range(self.temp_list_size):
            self.ds_slist.delete(self.temp_list_size - 1 - i)
        self.StopB['state'] = 'disabled'

    def quit(self):
        self.root.destroy()

    def ready_b_callback(self):
        self.mypipeline = piptest.Mypipeline(4)

        self.OutputText.insert(tk.INSERT, "pipeline set to ready \n")

        self.ds_pool = source_pool.Source_Pool(self.mypipeline.pipeline, 4, 1)
        self.ds_pool.start()
        self.ReadyB['state'] = 'disabled'

    def display_info(self):
        uid = self.ds_slist.get(self.ds_slist.curselection())[0]
        self.show_s = self.ds_pool.get_source_from_pool_by_id(uid)
        self.OutputText.insert(tk.INSERT, self.show_s.get_all_member())
        # print("chosen uid is:", uid)
        '''for s in self.ds_pool.pool:
            if s is not None and uid == s.get_user_id():
                print("source_index:",s.get_source_index())
                self.state = self.ds_pool.pipeline.get_source_bin_state(s.get_source_index())
                
                print(self.state)
                self.OutputText.insert(tk.INSERT, str(self.ds_slist.get(self.ds_slist.curselection())) + self.state + '\n')'''
        '''for s in self.ds_pool.pool:
            if s is not None:
                print(s.get_all_member())'''



if __name__ == '__main__':
    GUI_window()