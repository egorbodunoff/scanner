class VideoCamera:
    def __init__(self, camera):
        self.camera = camera


    def get_frame(self):
        with self.camera as camera:
            path = 'app/static/temp_image.bmp'
            ret = self.camera.capture_frame(path)
            if ret == 0:
                with open(path, 'rb') as f:
                    frame = f.read()
                return frame
            else:
                return None
                

    def get_frame_bytes(self):
        with self.camera as camera:
            frame = camera.capture_frame_bytes()
            return frame



