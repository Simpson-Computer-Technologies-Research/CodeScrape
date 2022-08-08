import cv2, pytesseract, time, re, asyncio, threading, queue, pytube, os, sys
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# https://www.youtube.com/watch?v=WxHRKCgCtDM
class Main:
    def __init__(self):
        self.codes = []
        self.start_time = time.time()
        self.frame_queue = queue.Queue()
        self.delete_youtube_video("default.mp4")
        self.download_youtube_video(input(" >> Video URL: "))
        self.capture = cv2.VideoCapture("default.mp4")
        self.regex = re.compile('[^a-zA-Z]')

    # // Delete the youtube video from pc
    def delete_youtube_video(self, name: str):
        if os.path.exists(name):
            return os.remove(name)
    
    # // Download the youtube video
    def download_youtube_video(self, url: str):
        return pytube.YouTube(url).streams.filter(
            res="480p", fps=30).first().download(filename="default.mp4")
    
    # // Release the capture and destroy windows
    def clear(self):
        self.capture.release()
        cv2.destroyAllWindows()
    
    # // Clean the code of any special characters
    def clean_code(self, code: str):
        for char in '\/=[]{)(}*|><.,?!@#$%^&*“':
            if char in code:
                code = code[:code.index(char)-1]+code[code.index(char)+1:]
        return code
    
    # // Check if valid code
    def check_code(self, _text:str):
        text = _text.replace(" ", "")
        if len(self.regex.sub('', _text)) > 10:
            # // If there's no - in the code return false
            if "-" not in text:
                return False
            
            # // If any letters are lower return false
            if any(l.islower() for l in text):
                return False
            
            # // Check the length for each part of the code
            for l in text.split("-"):
                if len(l.strip()) > 8:
                    return False
            return text not in self.codes
        return False
    
    # // Get the amount of frames in the video
    def get_video_frame_count(self):
        return int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))

    # // Read the frame
    def read_image(self, iteration: int):
        status, _image = self.capture.read()
        image = cv2.cvtColor(_image, cv2.COLOR_BGR2GRAY)
        if iteration % 20 == 0:
            if status:
                return image
        return None

    # // Start the code claimer
    async def start_program(self, iteration_num:int, status:bool, image):
        iterations = self.get_video_frame_count()//10
        for i in range(iterations):
            image = self.read_image(i)
            if image is not None:
                self.frame_queue.put(image)
            sys.stdout.write(f"{i}: {time.time()-self.start_time}\n")
            
            # // Start threads to search frame using pytesseract
            if i > iterations-2:
                await start_threads(100, target=self.get_code_from_image)
                if iteration_num < 10:
                    await self.start_program(iteration_num+1, status, image)
                    
    # // Gets the code from the image
    def get_code_from_image(self):
        while not self.frame_queue.empty():
            frame = self.frame_queue.get()
            _text:str = pytesseract.image_to_string(frame)
            text = _text.replace("\n", "")
            for c in text.split(" "):
                code = self.clean_code(c)
                if self.check_code(code):
                    self.codes.append(code)
            sys.stdout.write(f"{self.frame_queue.qsize()}: {time.time()-self.start_time}: {self.codes}\n")

# // Starts the threads
async def start_threads(amount:int, target=None):
    threads = [threading.Thread(target=target) for _ in range(amount)]
    [t.start() for t in threads]
    
# // Start
if __name__ == "__main__":
    main_class = Main()

    # Start the beginning loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main_class.start_program(1, None, None))
        
        
    # After the program has finished
    main_class.clear()
    final_time = round(((time.time()-main_class.start_time)/60), 2)
    sys.stdout.write(f"\n >> Done!\n >> Total Time: {final_time}m\n >> Scraped Codes: {main_class.codes}\n")