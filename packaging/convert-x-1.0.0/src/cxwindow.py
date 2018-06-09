# -*- coding: utf-8 -*-
from abc import ABC
from cxlang import Lang, UniversalText
from cxmsg import Msg, Type
from cxpassword import Password
from cxstream import StreamType
from cxutils import eprint, AutoNumber
import os
from PIL import Image, ImageTk
from queue import Empty, Queue
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading as th

###############################################################################
    
def setup_window(window, title, cfg, close_cb):
    window.title(title)
    window.bind("<<Close>>", close_cb)
    window.protocol("WM_DELETE_WINDOW", close_cb)
    window.resizable(0, 0)
    set_window_icon(window, cfg)

###############################################################################

def set_window_icon(window, cfg):
    icon_path = cfg.get("icon")
    if icon_path is not None and os.path.isfile(icon_path):
        try:
            img = ImageTk.PhotoImage(file=icon_path)
            # window._w is where the image is stored! It is freed up otherwise
            window.tk.call('wm', 'iconphoto', window._w, img)
        except tk.TclError as e:
            eprint(e)
    else:
        eprint("ERROR: Cannot open icon file: '{}'!".format(icon_path))

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

class AbstractDialog(ABC):
    """ Abstract dialog window base class """

    ### Public Methods ###

    def __init__(self, parent, width, height, cfg, colors, lang
            , title, ok_button_text=UniversalText(text="OK", single=True), parent_waits=False):
        self._parent = parent
        self._cfg = cfg
        self._colors = colors
        self._lang = lang
        self.cancelled = False
        
        if parent is None:
            self._window = tk.Tk()
        else:
            self._window = tk.Toplevel(parent)
            self._window.transient(parent)
            self._window.grab_set()
        
        setup_window(self._window, self._lang.universal_text(title)
                , self._cfg, self.__cancel)
        
        height += 32 # for the button line
        if self._parent is None:
            ws = self._window.winfo_screenwidth()
            hs = self._window.winfo_screenheight()
            x = (ws/2) - (width/2)
            y = (hs/2) - (height/2)
        else:
            x = self._parent.winfo_rootx() + self._parent.winfo_width()/2 - width/2
            y = self._parent.winfo_rooty() + self._parent.winfo_height()/2 - height/2
        self._window.geometry("%dx%d+%d+%d" % (width, height, x, y))

        ####################
        self._init_body()
        ####################
       
        self._okb_text = tk.StringVar()
        self._okb = tk.Button(self._window, textvariable=self._okb_text, command=self.__ok)
        self._okb_text.set(self._lang.universal_text(ok_button_text))
        self._okb.pack()
        
        self._colors.set_widget(self._window)

        if parent is None:
            self._window.mainloop()
        elif parent_waits: # the parent window stops until the dialog closed
            self._parent.wait_window(self._window)

    ### Protected Methods ###

    def _init_body(self):
        """ Override me to define your window elements. """
        pass

    def _ok(self):
        """ Override me to define your OK-logic. """
        return True

    def _cancel(self):
        """ Override me to define your cancel-logic. """
        return True
    
    ### Private Methods ###

    def __close_window(self):
        self._window.withdraw()
        self._window.destroy()

    def __ok(self):
        if self._ok():
            self.__close_window()

    def __cancel(self):
        self.cancelled = self._cancel()
        if self.cancelled:
            self.__close_window()

###############################################################################

class LanguageSelector(AbstractDialog):
    """ Language selector dialog window """
    
    ### Public Methods ###

    def __init__(self, parent, cfg, colors, lang):
        super().__init__(parent, 200, (len(lang.supp_langs) * 12), cfg, colors, lang
                , UniversalText(text="lang-title", single=True), parent_waits=True)

    ### Protected Methods ###

    def _init_body(self):
        self.__radio_buttons = []
        self.__selected = tk.IntVar()
        self.__selected.set(0)
        for i, l in enumerate(self._lang.supp_langs):
            rb = tk.Radiobutton(self._window, text=l
                    , variable=self.__selected, value=i
                    , indicatoron=0)
            rb.pack()
            if self._lang.selected is None:
                if not self.__radio_buttons:
                    rb.select()
            elif self._lang.selected == i:
                rb.select()
            self.__radio_buttons.append(rb)
    
    def _ok(self):
        self.__accept()
        return True

    def _cancel(self):
        self.__accept()
        return True

    ### Private Methods ###

    def __accept(self):
        self._lang.selected = self.__selected.get()

###############################################################################

class Update(AbstractDialog):
    """ A window to help updating the application """

    ### Public Methods ###

    def __init__(self, parent, cfg, colors, lang, app_q):
        self.__app_q = app_q
        self.__password = tk.StringVar()
        self.__remember_pass = tk.IntVar()
        self.__installed_version = tk.StringVar()
        self.__candidate_version = tk.StringVar()
        self.__status = tk.StringVar()
        self.__install = False
        self.__installation_started = False
        self.__installed = False
        super().__init__(parent, 300, 140, cfg, colors, lang, UniversalText("update-title")
                , UniversalText("update-ok-search"))
    
    def latest(self, installed_version):
        if self.cancelled:
            return
        self.__installed_version.set(installed_version)
        self.__candidate_version.set(installed_version)
        self.__status.set(self._lang.text("update-latest"))
        self.__enable()

    def availabe(self, installed_version, candidate_version):
        if self.cancelled:
            return
        self.__installed_version.set(installed_version)
        self.__candidate_version.set(candidate_version)
        self.__status.set(self._lang.text("update-available"))
        self.__install = True
        self._okb_text.set(self._lang.text("update-ok-available"))
        self.__enable()

    def failed(self, last_line):
        if self.cancelled:
            return
        self.__status.set(self._lang.text("update-failed").format(last_line))
        self.__enable()

    def finished(self, installed_version):
        if self.cancelled:
            return
        self.__installed_version.set(installed_version)
        self.__candidate_version.set(installed_version)
        self.__status.set(self._lang.text("update-finished"))
        self._okb_text.set(self._lang.text("OK", single=True))
        self.__installation_started = False
        self.__install = False
        self.__installed = True
        self.__enable()

    ### Protected Methods ###

    def _init_body(self):
        tk.Label(self._window, text=self._lang.text("update-pass")).pack()
        self.__pass_entry = tk.Entry(self._window, show='*', textvariable=self.__password
            , width=15)
        self.__pass_entry.pack()
        tk.Label(self._window, text=self._lang.text("update-installed")).pack()
        tk.Label(self._window, textvariable=self.__installed_version).pack()
        tk.Label(self._window, text=self._lang.text("update-candidate")).pack()
        tk.Label(self._window, textvariable=self.__candidate_version).pack()
        tk.Label(self._window, textvariable=self.__status).pack()

        self.__pass_entry.focus()
        self.__bind_enter_key()

    def _ok(self, *args):
        if self.__installed:
            return True
            
        if not self.__password.get():
            self.__status.set(self._lang.text("update-pass-empty"))
            self.__enable()
        elif not self.__install:
            self.__disable()
            self.__status.set(self._lang.text("update-search"))
            th.Thread(target=self.__encrypted_sender
                    , args=(Type.UPDATE_CHECK, self.__password.get())).start()
        elif self.__install:
            self.__disable()
            self.__installation_started = True
            self.__status.set(self._lang.text("update-install"))
            th.Thread(target=self.__encrypted_sender
                    , args=(Type.UPDATE_START, self.__password.get())).start()

        return False

    def _cancel(self):
        if self.__installation_started:
            if not messagebox.askyesno(self._lang.text("update-cancel-install-title")
                    , self._lang.text("update-cancel-install")):
                return False
        elif self.__install:
            if not messagebox.askyesno(self._lang.text("update-cancel-title")
                    , self._lang.text("update-cancel")):
                return False
        self.__app_q.put(Msg(Type.UPDATE_STOP))
        return True

    ### Private Methods ###

    def __bind_enter_key(self):
        self.__pass_entry.bind('<Return>', self._ok)

    def __disable(self):
        self._okb["state"] = tk.DISABLED
        self.__pass_entry["state"] = tk.DISABLED
        self.__pass_entry.unbind('<Return>')

    def __enable(self):
        self._okb["state"] = tk.NORMAL
        self.__pass_entry["state"] = tk.NORMAL
        self.__bind_enter_key()
    
    def __encrypted_sender(self, msg_type, raw_password):
        encrypted_password = Password(raw_password)
        self.__app_q.put(Msg(msg_type, encrypted_password))

###############################################################################

class Config(AbstractDialog):
    """ Configuration dialog window """
    
    ### Public Methods ###
    
    def __init__(self, parent, cfg, colors, lang, streams):
        self.__streams = streams
        width = 200 if self.__streams.streams else 600
        height = (len(self.__streams.streams) * 20) if self.__streams.streams else 24
        super().__init__(parent, width, height, cfg, colors, lang
                , UniversalText("config-title"))

    ### Protected Methods ###

    def _init_body(self):
        self.__check_boxes = []
        if not self.__streams.streams:
            tk.Label(self._window, text=self._lang.text("no-streams")).pack()
        else:
            for i, s in enumerate(self.__streams.streams):
                var = tk.IntVar()
                cb = tk.Checkbutton(self._window, anchor="w"
                        , text="{} {} {}".format(s.id, self._lang.text(s.type.name), s.lang)
                        , variable=var, state=tk.DISABLED if s.type == StreamType.VIDEO else tk.NORMAL)
                cb.selected = var
                cb.selected.set(1 if s.enabled else 0)
                cb.pack()
                self.__check_boxes.append(cb)

    def _ok(self):
        for i, cs in enumerate(self.__check_boxes):
            self.__streams.streams[i].enabled = True if cs.selected.get() else False
        return True

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

class WindowEvent(AutoNumber):
    RESET = ()
    INPUT_PARSING = ()
    INPUT_PARSED = ()
    INPUT_PERMISSION_ERROR = ()
    OUTPUT_AVAIL = ()
    OUTPUT_PERMISSION_ERROR = ()
    OUTPUT_DELETE = ()
    START = ()
    STOP = ()
    ERROR = ()
    FINISH = ()

class DisabledState:
    def __init__(self):
        self.clear_error_msg = True
        self.reset_progress = False
        self.menu = tk.DISABLED
        self.dir = tk.DISABLED
        self.openb = tk.DISABLED
        self.open_settingsb = tk.DISABLED
        self.saveb = tk.DISABLED
        self.save_delb = tk.DISABLED
        self.startb = tk.DISABLED
        self.stopb = tk.DISABLED

    def __eq__(self, other):
        return type(self).__name__ == type(other).__name__

class InitState(DisabledState):
    def __init__(self):
        super().__init__()
        self.menu = tk.NORMAL
        self.dir = tk.NORMAL
        self.openb = tk.NORMAL

class ProgressState(DisabledState, ABC):
    def __init__(self):
        super().__init__()
        self.stopb = tk.NORMAL

class OpeningState(ProgressState):
    def __init__(self):
        super().__init__()

class InputAvailableState(InitState):
    def __init__(self):
        super().__init__()
        self.open_settingsb = tk.NORMAL
        self.saveb = tk.NORMAL

class ReadyState(InputAvailableState):
    def __init__(self):
        super().__init__()
        self.startb = tk.NORMAL
        self.save_delb = tk.NORMAL

class ConversionState(ProgressState):
    def __init__(self):
        super().__init__()
        self.reset_progress = True

class OutputDeletedState(ReadyState):
    def __init__(self):
        super().__init__()
        self.save_delb = tk.DISABLED

class FinishedState(ReadyState):
    def __init__(self):
        super().__init__()

class ConversionFailedState(ReadyState):
    def __init__(self):
        super().__init__()
        self.clear_error_msg = False

class WindowStateMachine:
    
    ### Public Methods ###
    
    def __init__(self, menu_items, menu, dirb, openb, open_settingsb, saveb
            , save_delb, startb, stopb, progressbar, elapsede, lefte, set_state):
        self.__menu_items = menu_items
        self.__menu = menu
        self.__dirb = dirb
        self.__openb = openb
        self.__open_settingsb = open_settingsb
        self.__saveb = saveb
        self.__save_delb = save_delb
        self.__startb = startb
        self.__stopb = stopb
        self.__progressbar = progressbar
        self.__elapsede = elapsede
        self.__lefte = lefte
        self.__set_state = set_state
        
        self.error_msg = None

        self.__event_q = Queue()
        self.__prev_state = DisabledState()
        self.__state = DisabledState()
        self.notify(WindowEvent.RESET)
        
    def notify(self, event):
        self.__event_q.put(event)
    
    def step(self):
        """ Set window items according to the current state, if there was a state change """
        if self.__state_changed():
            if self.__state.clear_error_msg:
                self.error_msg = None
            if self.__state.reset_progress:
                pb_value = self.__progressbar["value"]
                if pb_value > 0:
                    self.__progressbar.step(amount=(-1 * pb_value))
                self.__elapsede.set_text()
                self.__lefte.set_text()
                self.__state.reset_progress = False
            for i in range(len(self.__menu_items)):
                self.__menu.entryconfigure((i+1), state=self.__state.menu)
            self.__dirb["state"] = self.__state.dir
            self.__openb["state"] = self.__state.openb
            self.__open_settingsb["state"] = self.__state.open_settingsb
            self.__saveb["state"] = self.__state.saveb
            self.__save_delb["state"] = self.__state.save_delb
            self.__startb["state"] = self.__state.startb
            self.__stopb["state"] = self.__state.stopb
    
    ### Private Methods ###
    
    def __state_changed(self):
        try:
            event = self.__event_q.get(block=False)
            self.__prev_state = self.__state
            self.__evaluate(event)
            return self.__prev_state != self.__state
        except Empty:
            return False

    def __evaluate(self, event):
        if event == WindowEvent.RESET:
            self.__state = InitState()
            self.__set_state()
        elif event == WindowEvent.INPUT_PARSING:
            self.__state = OpeningState()
            if isinstance(self.__prev_state, ReadyState):
                self.__state.was_ready = True
            self.__set_state("opening")
        elif event == WindowEvent.INPUT_PERMISSION_ERROR:
            self.__state = InitState()
            self.__set_state("warn-permission")
        elif event == WindowEvent.INPUT_PARSED:
            if hasattr(self.__prev_state, "was_ready"):
                self.__state = ReadyState()
            else:
                self.__state = InputAvailableState()
            self.__set_state()
        elif event == WindowEvent.OUTPUT_PERMISSION_ERROR:
            self.__state = InputAvailableState()
            self.__set_state("warn-permission")
        elif event == WindowEvent.OUTPUT_AVAIL:
            self.__state = ReadyState()
            self.__set_state()
        elif event == WindowEvent.START:
            self.__state = ConversionState()
            self.__set_state("conv")
        elif event == WindowEvent.STOP:
            if self.__prev_state == OpeningState():
                self.__state = InitState()
            elif self.__prev_state == ConversionState():
                self.__state = FinishedState()
            else:
                raise RuntimeError("Unexpected event!")
            self.__set_state("stopped")
        elif event == WindowEvent.ERROR:
            self.__state = ConversionFailedState()
            self.__set_state("err-msg")
        elif event == WindowEvent.FINISH:
            self.__state = FinishedState()
            self.__set_state("finished")
        elif event == WindowEvent.OUTPUT_DELETE:
            self.__state = OutputDeletedState()
            self.__set_state()
        else:
            raise RuntimeError("Unknown event!")

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
        self.__logo_canvas = None
        self.__updater = None
        
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
        try:
            self.__window = tk.Tk()
            self.__main = tk.Frame(self.__window)
        except tk.TclError as e:
            eprint(e)
            self.__app_q.put(Msg(Type.CLOSE))
            return        

        setup_window(self.__window, self.__gen_title(), self.__cfg
                , self.__on_closing)
        self.__set_geometry()
        
        self.__create_widgets()
        self.__order_widgets()
        self.__colors.set_widget(self.__window)

        self.__state_machine = WindowStateMachine(self.__menu_items, self.__menu
                , self.__dirb, self.__openb, self.__open_settingsb
                , self.__saveb, self.__save_delb, self.__startb, self.__stopb
                , self.__progressbar, self.__elapsede, self.__lefte
                , self.__set_state)
        
        while self.__window_q_processor():
            self.__state_machine.step()
            self.__window.update_idletasks()
            self.__window.update()

    def __window_q_processor(self):
        """ Process one message from the window queue """
        run = True
        try:
            msg = self.__window_q.get(block=False)
            if msg.type == Type.CLOSE_ACK:
                run = False
            elif msg.type == Type.ELAPSED:
                self.__elapsede.set_text(self.__sec2time(msg.data[0]))
            elif msg.type == Type.EXTRACTING_SUBTITLES:
                self.__set_state("extract-subs")
            elif msg.type == Type.FAILED:
                self.__state_machine.notify(WindowEvent.ERROR)
                self.__state_machine.error_msg = msg.data[0]
            elif msg.type == Type.FINISHED:
                self.__state_machine.notify(WindowEvent.FINISH)
            elif msg.type == Type.LEFT:
                self.__lefte.set_text(self.__sec2time(msg.data[0]))
            elif msg.type == Type.OPENED:
                self.__streams = msg.data[0]
                self.__state_machine.notify(WindowEvent.INPUT_PARSED)
            elif msg.type == Type.STEP:
                self.__progressbar.step(msg.data[0])
            elif msg.type == Type.STOP_ACK:
                self.__state_machine.notify(WindowEvent.STOP)
            elif msg.type == Type.UPDATE_FAILED:
                if self.__updater is not None:
                    self.__updater.failed(msg.data[0])
            elif msg.type == Type.UPDATE_AVAIL:
                if self.__updater is not None:
                    self.__updater.availabe(msg.data[0], msg.data[1])
            elif msg.type == Type.UPDATE_LATEST:
                if self.__updater is not None:
                    self.__updater.latest(msg.data[0])
            elif msg.type == Type.UPDATE_FINISHED:
                if self.__updater is not None:
                    self.__updater.finished(msg.data[0])
            elif msg.type == Type.WARN_PERMISSION_ERROR:
                self.__state_machine.notify(WindowEvent.INPUT_PERMISSION_ERROR)
            elif msg.type == Type.WARN_UNKNOWN_REMAINING_TIME:
                self.__set_state("warn-unknown-remaining-time")
            else:
                raise RuntimeError("Unexpected message: {}!".format(msg.type))
        except Empty:
            pass
        return run
    
    def __sec2time(self, seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return "%d:%02d:%02d" % (h, m, s)
    
    def __select_language(self):
        prev_selected = self.__lang.selected
        LanguageSelector(self.__window, self.__cfg, self.__colors
                , self.__lang)
        if self.__lang.selected is None:
            raise RuntimeError("INTERNAL ERROR: There is no selected language!")
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
    
    def __set_state(self, key=None):
        if self.__statee is not None:
            if key is None:
                self.__statee.set_text()
                self.__statee.name = None
            else:
                if key == "err-msg":
                    self.__statee.set_text(self.__gen_error_text())
                else:
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
                , text=self.__lang.text("opene")
                , name="opene")
        self.__open_buttons = tk.Frame(self.__main)
        self.__openb = tk.Button(self.__open_buttons
                , text=self.__lang.text("openb"), command=self.__open_input)
        self.__openb.name = "openb"
        self.__open_settingsb = tk.Button(self.__open_buttons
                , text=self.__lang.text("open_settingsb")
                , command=self.__open_settings)
        self.__open_settingsb.name = "open_settingsb"
        
        self.__savel = tk.Label(self.__main, text=self.__lang.text("savel"))
        self.__savel.name = "savel"
        self.__savee = ReadOnlyEntry(self.__main
                , text=self.__lang.text("savee")
                , name="savee")
        self.__save_buttons = tk.Frame(self.__main)
        self.__saveb = tk.Button(self.__save_buttons
                , text=self.__lang.text("saveb"), command=self.__save_output)
        self.__saveb.name = "saveb"
        self.__save_delb = tk.Button(self.__save_buttons
                , text=self.__lang.text("save-delb"), command=self.__save_delete)
        self.__save_delb.name = "save-delb"

        self.__command_separator_north = tk.ttk.Separator(self.__main
                , orient="horizontal")

        self.__command_buttons = tk.Frame(self.__main)
        self.__startb = tk.Button(self.__command_buttons
                , text=self.__lang.text("startb"), command=self.__start)
        self.__startb.name = "startb"
        self.__stopb = tk.Button(self.__command_buttons
                , text=self.__lang.text("stopb"), command=self.__stop)
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
            if w.name == "err-msg":
                self.__set_state("err-msg")
            else:
                w.set_text(self.__lang.text(w.name))
        elif w.winfo_class() == "Menu":
            for i, mi in enumerate(self.__menu_items):
                self.__menu.entryconfigure((i+1)
                        , label=self.__lang.text(mi[0]))

        for c in w.children.values():
            self.__rephrase(c)

    def __load_logo(self):
        logo_path = self.__cfg.get("logo")
        if logo_path is not None and os.path.isfile(logo_path):
            try:
                logo_image = Image.open(logo_path)
            except tk.TclError as e:
                eprint(e)
                return
        else:
            eprint("ERROR: Cannot open logo file: '{}'!".format(logo_path))
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
            if ' ' in d:
                self.__set_state("err-space-in-path")
            else:
                self.__set_state()
                self.__dire.set_path(d)
                self.__app_q.put(Msg(Type.SET_CFG, "dir", d))

    def __open_input(self):
        d = self.__dire.get_text()
        if d is not None:
            inp = tk.filedialog.askopenfilename(initialdir=d)
        else:
            inp = tk.filedialog.askopenfilename()
        if inp:
            if ' ' in inp:
                self.__set_state("err-space-in-path")
            else:
                self.__set_state()
                self.__opene.set_path(inp)
                self.__app_q.put(Msg(Type.INPUT_FILE, inp))
                self.__state_machine.notify(WindowEvent.INPUT_PARSING)

    def __open_settings(self):
        Config(self.__window, self.__cfg, self.__colors, self.__lang
                , self.__streams)

    def __save_output(self):
        try:
            out = tk.filedialog.asksaveasfile(defaultextension=".avi"
                    , filetypes=[(self.__lang.text("file-types"), "*.avi")])
            if out:
                if ' ' in out.name:
                    self.__set_state("err-space-in-path")
                else:
                    self.__set_state()
                    self.__savee.set_path(out.name)
                    self.__app_q.put(Msg(Type.OUTPUT_FILE, out.name))
                    self.__state_machine.notify(WindowEvent.OUTPUT_AVAIL)
        except IOError as err:
            eprint(err)
            self.__savee.set_path()
            self.__state_machine.notify(WindowEvent.OUTPUT_PERMISSION_ERROR)
    
    def __save_delete(self):
        save_file = self.__savee.get_text()
        if save_file is not None and messagebox.askyesno(
                self.__lang.text("del-target-title")
                , self.__lang.text("del-target-msg")):
            self.__app_q.put(Msg(Type.DELETE, save_file))
            self.__state_machine.notify(WindowEvent.OUTPUT_DELETE)
    
    def __start(self):
        self.__app_q.put(Msg(Type.START, self.__streams))
        self.__state_machine.notify(WindowEvent.START)
    
    def __stop(self, stay_alive=True):
        if stay_alive and not messagebox.askyesno(self.__lang.text("stop-title")
                , self.__lang.text("stop-msg")):
            return
        if stay_alive:
            self.__app_q.put(Msg(Type.STOP))
        else:
            self.__app_q.put(Msg(Type.CLOSE))

    def __gen_title(self):
        return self.__lang.text("title").format(
                self.__lang.text("version", single=True))

    def __gen_error_text(self):
        error_template = self.__lang.text("err-msg")
        error_text = None
        if self.__state_machine.error_msg is not None:
            error_text = error_template.format(self.__state_machine.error_msg)
        else:
            error_text = error_template.format(self.__lang.text("unknown"))
        return error_text

    def __update(self):
        self.__updater = Update(self.__window, self.__cfg, self.__colors, self.__lang
            , self.__app_q)
    