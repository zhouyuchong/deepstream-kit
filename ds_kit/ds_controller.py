import threading

class Pipeline_Controller(threading.Thread):
    def __init__(self, pipeline):
        threading.Thread.__init__(self)
        self.pipeline = pipeline

    def change_msg_state(self, state):
        if state == "unable":
            self.pipeline.unable_msg_broker()
        if state == "enable":
            self.pipeline.enable_msg_broker()


