# coding=utf-8

import re
import subprocess
import threading as th
import time
import tkinter as tk
from tkinter import filedialog, ttk, messagebox


class ReadOnlyEntry(tk.Entry):
    def __init__(self, master, name=None, set_cb=None
            , text=None, width=150, **kw):
        super().__init__(master, **kw)
        self.__name = name
        self.__set_cb = set_cb
        self["state"] = "readonly"
        self["relief"] = tk.FLAT
        self["width"] = width
        if text is not None:
            self.set_text(text)
    
    def get_text(self):
        return self.get()

    def set_text(self, content):
        self["state"] = "normal"
        self.delete(0, tk.END)
        self.insert(tk.END, content)
        self["state"] = "readonly"
        if self.__set_cb is not None:
            self.__set_cb(self.__name)


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.__master = master
        self.__master.protocol("WM_DELETE_WINDOW", self.__on_closing)
        self.__main = self.winfo_toplevel()
        self.__input = ["input", False]
        self.__output = ["output", False]
        self.__config = "config.ini"
        self.__width = 1000
        self.__height = 400
        self.__progress_thread = None
        self.__converter_lock = th.Lock()
        self.__converter = None 
        self.__saveb = None
        self.__setup_window()
        self.__create_widgets()
        self.__read_cfg()
        self.pack(fill=tk.BOTH, padx=5, pady=5)

    def __on_closing(self):
        if messagebox.askokcancel("A program bezárása", "Biztos, hogy ki akarsz lépni?"):
            self.__stop()
            self.__master.destroy()

    def __read_cfg(self):
        try:
            with open(self.__config) as config:
                for line in config:
                    if line.startswith("dir="):
                        self.__dire.set_text(line.split('=')[1])
        except IOError:
            pass

    def __create_widgets(self):
        self.__dirl = tk.Label(self, text="Az alapértelmezett könyvtár:")
        self.__dire = ReadOnlyEntry(self
                , text="Még nem adtál meg alapértelmezett könyvárat.")
        self.__dirb = tk.Button(self, text="Választás", command=self.__select_dir)

        self.__openl = tk.Label(self, text="Az eredeti file, amit át szeretnél konvertálni:")
        self.__opene = ReadOnlyEntry(self
                , text="Itt jelenik majd meg az eredeti file elérési útvonala."
                , name=self.__input[0], set_cb=self.__io_set)
        self.__openb = tk.Button(self, text="Megnyitás", command=self.__open_input)
        
        self.__savel = tk.Label(self, text="Az új file, amire konvertálni fogunk:")
        self.__savee = ReadOnlyEntry(self
                , text="Itt jelenik majd meg az új file elérési útvonala."
                , name=self.__output[0], set_cb=self.__io_set)
        self.__saveb = tk.Button(self, text="Mentés", command=self.__save_output, state=tk.DISABLED)
        
        self.__startb = tk.Button(self, text="Start", command=self.__start, state=tk.DISABLED)
        self.__stopb = tk.Button(self, text="Stop", command=self.__stop, state=tk.DISABLED)
        
        self.__elapsedl = tk.Label(self, text="Az eltelt idő:")
        self.__elapsede = ReadOnlyEntry(self)
        
        self.__leftl = tk.Label(self, text="A becsült hátralévő idő:")
        self.__lefte = ReadOnlyEntry(self)

        self.__progressbar = tk.ttk.Progressbar(self, orient="horizontal"
                , length=self.__width, mode="determinate")

        s = tk.W
        self.__dirl.grid(sticky=s)
        self.__dire.grid(sticky=s)
        self.__dirb.grid(sticky=s)
        self.__openl.grid(sticky=s)
        self.__opene.grid(sticky=s)
        self.__openb.grid(sticky=s)
        self.__savel.grid(sticky=s)
        self.__savee.grid(sticky=s)
        self.__saveb.grid(sticky=s)
        self.__startb.grid(sticky=s)
        self.__stopb.grid(sticky=s)
        self.__elapsedl.grid(sticky=s)
        self.__elapsede.grid(sticky=s)
        self.__leftl.grid(sticky=s)
        self.__lefte.grid(sticky=s)
        self.__progressbar.grid(sticky=s)
        
        ### TEST ONLY ###
#        self.__opene.set_text(
#                "/media/steve/Data/UsersData/Zs&S/Videos/Movies/Dunkirk.2017.RETAiL.BDRip.x264.HuN-No1/sample/!sample.mkv"
#                "/media/steve/Data/UsersData/Zs&S/Videos/Movies/Dunkirk.2017.RETAiL.BDRip.x264.HuN-No1/dunkirk.bdrip-no1.mkv"
#                )
#        self.__savee.set_text(
#                "/media/steve/Data/UsersData/Zs&S/Videos/Movies/Dunkirk.2017.RETAiL.BDRip.x264.HuN-No1/test.avi")
        #################

    def __io_set(self, *args):
        if self.__saveb is None:
            return
        
        if self.__input[0] == args[0]:
            self.__input[1] = True
        if self.__output[0] == args[0]:
            self.__output[1] = True

        if self.__input[1]:
            self.__saveb["state"] = tk.NORMAL
        else:
            self.__saveb["state"] = tk.DISABLED

        if self.__input[1] and self.__output[1]:
            self.__startb["state"] = tk.NORMAL
        else:
            self.__startb["state"] = tk.DISABLED

    def __setup_window(self):
        self.__main.title("Konvertálás XviD formátumra")
        self.__main.resizable(0,0)
        w = self.__width
        h = self.__height
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        self.__main.geometry("%dx%d+%d+%d" % (w, h, x, y))

    def __select_dir(self):
        d = tk.filedialog.askdirectory()
        if d:
            self.__dire.set_text(d)
            with open(self.__config, 'w') as config:
                config.write("dir=" + d)

    def __open_input(self):
        d = self.__dire.get_text()
        if d is not None:
            inp = tk.filedialog.askopenfilename(initialdir=d)
        else:
            inp = tk.filedialog.askopenfilename()
        if inp:
            self.__opene.set_text(inp)

    def __save_output(self):
        out = tk.filedialog.asksaveasfile(defaultextension=".avi", filetypes=[("avi file-ok", "*.avi")])
        if out:
            self.__savee.set_text(out.name)

    def __started(self):
        self.__dirb["state"] = tk.DISABLED
        self.__openb["state"] = tk.DISABLED
        self.__saveb["state"] = tk.DISABLED
        self.__startb["state"] = tk.DISABLED
        self.__stopb["state"] = tk.NORMAL
    
    def __stopped(self):
        self.__progressbar.step(amount=(-1 * self.__progressbar["value"]))
        self.__dirb["state"] = tk.NORMAL
        self.__openb["state"] = tk.NORMAL
        self.__saveb["state"] = tk.NORMAL
        self.__startb["state"] = tk.NORMAL
        self.__stopb["state"] = tk.DISABLED

    def __start(self):
        with self.__converter_lock:
            self.__converter = subprocess.Popen(["ffmpeg"
                # input file options:
                # input file:
                , "-i", self.__opene.get_text()
                # output file options:
                , "-threads", "1"
                , "-vcodec", "libxvid", "-q:v", "0"
                , "-q:a", "0", "-acodec", "libmp3lame", "-b:a", "128k", "-ac", "2", "-y"
                # output file:
                , self.__savee.get_text()]
                , stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        self.__started()
        if self.__progress_thread is None:
            self.__progress_thread = th.Thread(target = self.__progress)
            self.__progress_thread.start()

    def __progress(self):
        #print("### progress thread was started")
        frames = None
        one_percent = None
        percent = 0
        frame = 0
        t = th.currentThread()
        start = time.time()
        while getattr(t, "do_run", True) and ((frames is None) or (frame < frames)):
            with self.__converter_lock:
                converting = (self.__converter is not None)
                if converting:
                    l = self.__converter.stdout.readline().rstrip()
                else:
                    t.do_run = False
                    continue

                if not frames:
                    match = re.search("NUMBER_OF_FRAMES:\s*(\d+)", l)
                    if match:
                        frames = int(match.group(1))
                        one_percent = frames / 100
                else:
                    match = re.search("frame=\s*(\d+)", l)
                    if match:
                        now = time.time()
                        frame = int(match.group(1))
                        if frame >= percent:
                            if getattr(t, "do_run", True):
                                percent = (frame / one_percent)
                                incr = percent - self.__progressbar["value"]
                                #print(incr, percent, self.__progressbar["value"])
                                self.__progressbar.step(incr)
                                percent = frame + one_percent

                #print(l)
                #print(one_percent, percent, frame, frames)
                if getattr(t, "do_run", True):
                    elapsed = time.time() - start
                    
                    self.__elapsede.set_text(self.__sec2time(elapsed))
                   
                    if frame and frames:
                        needed_per_frame = elapsed / frame
                        left = frames - frame
                        estimate = left * needed_per_frame
                        self.__lefte.set_text(self.__sec2time(estimate))


        if getattr(t, "do_run", True):
            self.__stopped()
        self.__progress_thread = None
        #print("### progress thread was stopped")

    def __stop(self):
        if self.__progress_thread is not None:
            self.__progress_thread.do_run = False
            self.__stopped()

        with self.__converter_lock:
            if self.__converter is not None:
                self.__converter.terminate()
                try:
                    self.__converter.wait(timeout=15)
                except TimeoutExpired:
                    self.__converter.kill()
                self.__converter = None

    def __sec2time(self, seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return "%d:%02d:%02d" % (h, m, s)


if __name__ == "__main__":
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()

