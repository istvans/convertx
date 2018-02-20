# -*- coding: utf-8 -*-
import sys
sys.path.append("/lib/convert-x")

from cxlang import Lang
from cxmsg import Msg, Type
from cxutils import eprint
from PIL import Image, ImageTk
from queue import Empty
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading as th

###############################################################################

def set_window_icon(win, cfg):
    icon_path = cfg.get("icon")
    if icon_path is not None:
        try:
            img = ImageTk.PhotoImage(file=icon_path)
            # win._w is where the image is stored! It is freed up otherwise
            win.tk.call('wm', 'iconphoto', win._w, img)
        except tk.TclError as e:
            eprint(e)
    else:
        eprint("no icon")

###############################################################################

def setup_window(win, title, closing_cb, cfg):
    win.title(title)
    win.protocol("WM_DELETE_WINDOW", closing_cb)
    win.resizable(0, 0)
    set_window_icon(win, cfg)

###############################################################################
###############################################################################

class Colors:
    ### Public Methods ###
    def __init__(self, bg, fg, pbg, sbg, tbg):
        self.__bg = bg
        self.__fg = fg
        self.__pbg = pbg
        self.__sbg = sbg
        self.__tbg = tbg

    def set_widget(self, w):
        """ Pass a widget and I set its and its child widgets' color """
        if w is None:
            return
        
        if "style" in w.keys():
            s = tk.ttk.Style()
            s.theme_use('clam')
            style_class = w.winfo_class()
            if style_class == "TProgressbar":
                s.configure(style_class
                        , background=self.__pbg
                        , foreground=self.__pbg)
            elif style_class == "TSeparator":
                s.configure(style_class, background=self.__sbg)
            else:
                s.configure(style_class, background=self.__bg
                        , foreground=self.__fg)
            w["style"] = style_class
        else:
            self.__set(w, "bg", self.__bg)
            self.__set(w, "fg", self.__fg)
            self.__set(w, "readonlybackground", self.__tbg)
        
        for c in w.children.values():
            self.set_widget(c)
    
    ### Private Methods ###
    
    def __set(self, w, key, value):
        """ If the key tkinter attribute exists, set it to value """
        if key in w.keys():
            w[key] = value

###############################################################################

class LanguageSelector:
    """ Language selector dialog window """
    ### Public Methods ###
    def __init__(self, cfg, lang, colors, parent=None):
        self.__lang = lang
        
        if parent is None:
            self.__w = tk.Tk()
        else:
            self.__w = tk.Toplevel(parent)
            self.__w.transient(parent)
            self.__w.grab_set()
        
        setup_window(self.__w, "Select Language", self.__ok, cfg)
        
        ws = self.__w.winfo_screenwidth()
        w = int(ws * 0.2)
        h = (len(self.__lang.supp_langs) * 12) + 32
        if parent is None:
            hs = self.__w.winfo_screenheight()
            x = (ws/2) - (w/2)
            y = (hs/2) - (h/2)
        else:
            x = parent.winfo_rootx() + parent.winfo_width()/2 - w/2
            y = parent.winfo_rooty() + parent.winfo_height()/2 - h/2
        self.__w.geometry("%dx%d+%d+%d" % (w, h, x, y))
        
        self.__radio_buttons = []
        self.__selected = tk.IntVar()
        self.__selected.set(0)
        for i, l in enumerate(self.__lang.supp_langs):
            rb = tk.Radiobutton(self.__w, text=l
                    , variable=self.__selected, value=i
                    , indicatoron=0)
            rb.pack()
            if self.__lang.selected is None:
                if not self.__radio_buttons:
                    rb.select()
            elif self.__lang.selected == i:
                rb.select()
            self.__radio_buttons.append(rb)
            
        self.__button = tk.Button(self.__w, text="OK", command=self.__ok)
        self.__button.pack()

        colors.set_widget(self.__w)

        if parent is None:
            self.__w.mainloop()
        else:
            parent.wait_window(self.__w)
    
    ### Private Methods ###

    def __ok(self):
        self.__lang.selected = self.__selected.get()
        self.__w.withdraw()
        self.__w.destroy()

###############################################################################

class ReadOnlyEntry(tk.Entry):
    ### Public Methods ###
    def __init__(self, master, name=None, translate=True, change_cb=None
            , text=None, **kw):
        super().__init__(master, **kw)
        self.name = name
        self.translate = translate
        self.__change_cb = change_cb
        self["state"] = "readonly"
        self["relief"] = tk.FLAT
        if text is not None:
            self.set_text(text)
    
    def get_text(self):
        return self.get()

    def set_text(self, content=None):
        self["state"] = "normal"
        self.delete(0, tk.END)
        if content is not None:
            self.insert(tk.END, content)
        self["state"] = "readonly"
        if self.__change_cb is not None:
            self.__change_cb(self.name)

    def set_path(self, path=None):
        self.set_text(path)
        self.translate = False

###############################################################################

class Update:
    """ A window to help updating the application """
    def __init__(self, parent, cfg, colors, lidx):
        self.__parent = parent
        self.__w = tk.Toplevel(self.__parent)
        self.__w.transient(self.__parent)
        self.__w.grab_set()
        
        setup_window(self.__w, "Select Language", self.__cancel, cfg)

###############################################################################

class Window:
    """ A GUI window running on its own-thread """
    ### Public Methods ###
    def __init__(self, window_queue, app_queue, cfg):
        self.__window_q = window_queue
        self.__app_q = app_queue
        self.__cfg = cfg

        self.__colors = Colors(bg="white", fg="black"
                , pbg="blue", sbg="black", tbg="white")
        
        self.__window = None
        
        self.__lang = Lang(self.__cfg)
        if self.__lang.selected is None:
            self.__select_language()
        
        self.__gui_thread = th.Thread(target=self.__loop)
        self.__gui_thread.start()

    def __del__(self):
        if self.__window:
            self.__window.destroy()

    def get_input(self):
        if self.__opene is not None:
            return self.__opene.get_text()
        return None
    
    ### Private Methods ###

    def __loop(self):
        self.__window = tk.Tk()
        self.__close_event = "<<Close>>"
        self.__window.bind(self.__close_event, self.__on_closing)
        self.__main = tk.Frame(self.__window)

        setup_window(self.__window, self.__gen_title(), self.__on_closing
                , self.__cfg)
        self.__set_geometry()
        
        self.__input = ["opene", False]
        self.__output = ["savee", False]
        self.__saveb = None

        self.__create_widgets()
        self.__order_widgets()
        self.__colors.set_widget(self.__window)
        
        while self.__window_q_processor():
            self.__window.update_idletasks()
            self.__window.update()

    def __window_q_processor(self):
        """ Process one message from the queue """
        run = True
        try:
            msg = self.__window_q.get(block=False)
            if msg.type == Type.PREP:
                self.__set_state("prep")
            elif msg.type == Type.CONV:
                self.__set_state("conv")
            elif msg.type == Type.STEP:
                self.__progressbar.step(msg.data[0])
            elif msg.type == Type.ELAPSED:
                self.__elapsede.set_text(msg.data[0])
            elif msg.type == Type.LEFT:
                self.__lefte.set_text(msg.data[0])
            elif msg.type == Type.STOP_ACK:
                self.__stopped(forced=True)
            elif msg.type == Type.CLOSE_ACK:
                run = False
            elif msg.type == Type.FINISHED:
                self.__stopped()
            elif msg.type == Type.WARN_UNKNOWN_REMAINING_TIME:
                self.__set_state("warn-unknown-remaining-time")
        except Empty:
            pass
        return run
    
    def __select_language(self):
        prev_selected = self.__lang.selected
        ls = LanguageSelector(self.__cfg, self.__lang, self.__colors
                , self.__window)
        if self.__lang.selected is None:
            raise RuntimeError("INTERNAL ERROR: lidx is None!")
        self.__app_q.put(Msg(Type.SET_CFG, "lang", self.__lang.selected))

        if prev_selected != self.__lang.selected:
            self.__rephrase(self.__window)
        
    def __set_geometry(self):
        ws = self.__window.winfo_screenwidth()
        hs = self.__window.winfo_screenheight()
        w = int(ws * 0.92)
        h = 420
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        self.__window.geometry("%dx%d+%d+%d" % (w, h, x, y))
        self.__entry_width = int(w * (90/736))
    
    def __set_state(self, key):
        if self.__statee is not None:
            self.__statee.set_text(self.__lang.text(key))
            self.__statee.name = key

    def __close(self):
        self.__window.event_generate(self.__close_event, when="tail")
    
    def __on_closing(self, *args):
        if messagebox.askyesno(self.__lang.text("exit-title")
                , self.__lang.text("exit-msg")):
            self.__stop(stay_alive=False)

    def __create_menu(self):
        self.__menu_items = [
                ["menu-lang", self.__select_language]
                , ["menu-update", self.__update]]

        self.__menu = tk.Menu(self.__main)
        for i, mi in enumerate(self.__menu_items):
            self.__menu.add_command(label=self.__lang.text(mi[0]), command=mi[1])
        self.__window.config(menu=self.__menu)

    def __create_widgets(self):
        self.__load_logo()
        
        self.__create_menu()

        self.__dirl = tk.Label(self.__main, text=self.__lang.text("dirl"))
        self.__dirl.name = "dirl"
        self.__dire = ReadOnlyEntry(self.__main
                , text=self.__lang.text("dire"), name="dire"
                , width=self.__entry_width)
        d = self.__cfg.get("dir")
        if d is not None:
            self.__dire.set_path(d)
        self.__dirb = tk.Button(self.__main
                , text=self.__lang.text("dirb"), command=self.__select_dir)
        self.__dirb.name = "dirb"

        self.__openl = tk.Label(self.__main, text=self.__lang.text("openl"))
        self.__openl.name = "openl"
        self.__opene = ReadOnlyEntry(self.__main
                , text=self.__lang.text(self.__input[0])
                , name=self.__input[0], change_cb=self.__io_set)
        self.__open_buttons = tk.Frame(self.__main)
        self.__openb = tk.Button(self.__open_buttons
                , text=self.__lang.text("openb"), command=self.__open_input)
        self.__openb.name = "openb"
        self.__open_settingsb = tk.Button(self.__open_buttons
                , text=self.__lang.text("open_settingsb")
                , command=self.__open_settings, state=tk.DISABLED)
        self.__open_settingsb.name = "open_settingsb"
        
        self.__savel = tk.Label(self.__main, text=self.__lang.text("savel"))
        self.__savel.name = "savel"
        self.__savee = ReadOnlyEntry(self.__main
                , text=self.__lang.text(self.__output[0])
                , name=self.__output[0], change_cb=self.__io_set)
        self.__save_buttons = tk.Frame(self.__main)
        self.__saveb = tk.Button(self.__save_buttons
                , text=self.__lang.text("saveb"), command=self.__save_output
                , state=tk.DISABLED)
        self.__saveb.name = "saveb"
        self.__save_delb = tk.Button(self.__save_buttons
                , text=self.__lang.text("save-delb"), command=self.__save_delete
                , state=tk.DISABLED)
        self.__save_delb.name = "save-delb"

        self.__command_separator_north = tk.ttk.Separator(self.__main
                , orient="horizontal")

        self.__command_buttons = tk.Frame(self.__main)
        self.__startb = tk.Button(self.__command_buttons
                , text=self.__lang.text("startb"), command=self.__start
                , state=tk.DISABLED)
        self.__startb.name = "startb"
        self.__stopb = tk.Button(self.__command_buttons
                , text=self.__lang.text("stopb"), command=self.__stop
                , state=tk.DISABLED)
        self.__stopb.name = "stopb"
        
        self.__command_separator_south = tk.ttk.Separator(self.__main
                , orient="horizontal")

        self.__statee = ReadOnlyEntry(self.__main)
        
        self.__elapsedl = tk.Label(self.__main, text=self.__lang.text("elapsedl"))
        self.__elapsedl.name = "elapsedl"
        self.__elapsede = ReadOnlyEntry(self.__main, translate=False)
        
        self.__leftl = tk.Label(self.__main, text=self.__lang.text("leftl"))
        self.__leftl.name = "leftl"
        self.__lefte = ReadOnlyEntry(self.__main, translate=False)

        self.__progressbar = tk.ttk.Progressbar(self.__main
                , orient="horizontal", mode="determinate", maximum=100.00000001)

    def __order_widgets(self):
        if self.__logo_canvas:
            self.__logo_canvas.place(relx=0.9, rely=0.9, anchor=tk.SE)
        self.__dirl.grid(sticky="w")
        self.__dire.grid(sticky="ew")
        self.__dirb.grid(sticky="w")
        self.__openl.grid(sticky="w")
        self.__opene.grid(sticky="ew")
        self.__open_buttons.grid(sticky="w")
        self.__openb.grid(sticky="w", row=0, column=0)
        self.__open_settingsb.grid(sticky="w", row=0, column=1, padx=(5, 0))
        self.__savel.grid(sticky="w")
        self.__savee.grid(sticky="ew")
        self.__save_buttons.grid(sticky="w")
        self.__saveb.grid(sticky="w", row=0, column=0)
        self.__save_delb.grid(sticky="w", row=0, column=1, padx=(5, 0))

        self.__command_separator_north.grid(sticky="ew", pady=5)

        self.__command_buttons.grid(sticky="w", pady=5)
        self.__startb.grid(sticky="w", row=0, column=0)
        self.__stopb.grid(sticky="w", row=0, column=1, padx=(5, 0))
        
        self.__command_separator_south.grid(sticky="ew", pady=5)
        
        self.__statee.grid(sticky="ew")
        self.__elapsedl.grid(sticky="w", pady=(30, 0))
        self.__elapsede.grid(sticky="w")
        self.__leftl.grid(sticky="w")
        self.__lefte.grid(sticky="w")
        self.__progressbar.grid(sticky="ew")

        self.__main.grid_columnconfigure(0, weight=3)
        self.__main.grid_columnconfigure(1, weight=1)
        self.__main.grid(sticky="nsew", padx=5, pady=5)
    
    def __rephrase(self, w):
        if w is None:
            return

        if "text" in w.keys() and hasattr(w, "name"):
            w["text"] = self.__lang.text(w.name)
        elif hasattr(w, "title"):
            w.title(self.__gen_title())
        elif w.winfo_class() == "Entry" and w.name is not None \
                and w.translate:
            w.set_text(self.__lang.text(w.name))
        elif w.winfo_class() == "Menu":
            for i, mi in enumerate(self.__menu_items):
                self.__menu.entryconfigure((i+1)
                        , label=self.__lang.text(mi[0]))

        for c in w.children.values():
            self.__rephrase(c)

    def __io_set(self, name, *args):
        if self.__saveb is None:
            return
        
        if self.__input[0] == name:
            self.__input[1] = True
        #if self.__output[0] == name:
        #    self.__output[1] = True

        if self.__input[1]:
            self.__saveb["state"] = tk.NORMAL
        else:
            self.__saveb["state"] = tk.DISABLED

        #if self.__input[1] and self.__output[1]:
        #    self.__startb["state"] = tk.NORMAL
        #else:
        #    self.__startb["state"] = tk.DISABLED
    
    def __load_logo(self):
        logo_path = self.__cfg.get("logo")
        try:
            logo_image = Image.open(logo_path)
        except tk.TclError as e:
            eprint(e)
            return

        lh = 64
        lw = int(lh * (logo_image.size[0] / logo_image.size[1]))
        logo_image = logo_image.resize((lw, lh), Image.ANTIALIAS)
        logo = ImageTk.PhotoImage(logo_image)
        self.__logo_canvas = tk.Label(self.__main, image=logo)
        self.__logo_canvas.image = logo
    
    def __select_dir(self):
        saved = self.__dire.get_text()
        if saved is not None:
            d = tk.filedialog.askdirectory(initialdir=saved)
        else:
            d = tk.filedialog.askdirectory()
        if d:
            self.__dire.set_path(d)
            self.__app_q.put(Msg(Type.SET_CFG, "dir", d))

    def __open_input(self):
        d = self.__dire.get_text()
        if d is not None:
            inp = tk.filedialog.askopenfilename(initialdir=d)
        else:
            inp = tk.filedialog.askopenfilename()
        if inp:
            self.__opene.set_path(inp)
            self.__app_q.put(Msg(Type.INPUT_FILE, inp))

    def __open_settings(self):
        pass

    def __save_output(self):
        out = tk.filedialog.asksaveasfile(defaultextension=".avi"
                , filetypes=[(self.__lang.text("file-types"), "*.avi")])
        if out:
            self.__savee.set_path(out.name)
            self.__app_q.put(Msg(Type.OUTPUT_FILE, out.name))
    
    def __save_delete(self):
        save_file = self.__savee.get_text()
        if save_file is not None and messagebox.askyesno(
                self.__lang.text("del-target-title")
                , self.__lang.text("del-target-msg")):
            self.__app_q.put(Msg(Type.DELETE, save_file))
            self.__save_delb["state"] = tk.DISABLED
    
    def __start(self):
        self.__started()
        self.__app_q.put(Msg(Type.START))
    
    def __stop(self, stay_alive=True):
        if stay_alive and not messagebox.askyesno(self.__lang.text("stop-title")
                , self.__lang.text("stop-msg")):
            return
        if stay_alive:
            self.__app_q.put(Msg(Type.STOP))
        else:
            self.__app_q.put(Msg(Type.CLOSE))

    def __started(self):
        pb_value = self.__progressbar["value"]
        if pb_value > 0:
            self.__progressbar.step(amount=(-1 * pb_value))
            self.__elapsede.set_text()
            self.__lefte.set_text()
        for i in range(len(self.__menu_items)):
            self.__menu.entryconfigure((i+1), state=tk.DISABLED)
        self.__dirb["state"] = tk.DISABLED
        self.__openb["state"] = tk.DISABLED
        self.__saveb["state"] = tk.DISABLED
        self.__save_delb["state"] = tk.DISABLED
        self.__startb["state"] = tk.DISABLED
        self.__stopb["state"] = tk.NORMAL
    
    def __stopped(self, forced=False):
        if forced:
            self.__set_state("stopped")
        else:
            self.__set_state("finished")
        for i in range(len(self.__menu_items)):
            self.__menu.entryconfigure((i+1), state=tk.NORMAL)
        self.__dirb["state"] = tk.NORMAL
        self.__openb["state"] = tk.NORMAL
        self.__saveb["state"] = tk.NORMAL
        self.__save_delb["state"] = tk.NORMAL
        self.__startb["state"] = tk.NORMAL
        self.__stopb["state"] = tk.DISABLED
    
    def __gen_title(self):
        return self.__lang.text("title").format(
                self.__lang.text("version", single=True))

    def __update(self):
        print("TODO: update")