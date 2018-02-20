#!/usr/bin/python3
# -*- coding: utf-8 -*-

###############################################################################

class Lang:
    def text(self, key, single=False):
        if key not in self.__texts:
            raise RuntimeError("INTERNAL ERROR: Unknown key: '{}'".format(key))
        if not single and self.selected is None:
            raise RuntimeError("INTERNAL ERROR: Key '{}' was used, before "
                    "language selection".format(key))
        return self.__texts[key] if single else self.__texts[key][self.selected]

    def __init__(self, cfg):
        self.selected = None
        lidx = cfg.get("lang")
        if lidx is not None:
            self.selected = int(lidx)

        self.supp_langs = ["Magyar", "English"]
        self.__texts = {
            "version" : "v1.0.0",
            "title" : ["Conv2XviD - Konvertálás XviD formátumra ({})"
                , "Conv2XviD - Conversion to XviD format ({})"],
            "conv" : ["Konvertálás...", "Conversion..."],
            "stop-title" : ["A konvertálás megszakítása"
                , "Cancelling the conversion"],
            "stop-msg" : ["Biztos, hogy le akarod állítani a konvertálást?"
                , "Are you sure you want to cancel the conversion?"],
            "stopped" : ["Megszakítva", "Cancelled"],
            "finished" : ["Kész!", "Done!"],
            "exit-title" : ["A program bezárása", "Closing the application"],
            "exit-msg" : ["Biztos, hogy ki akarsz lépni?"
                , "Are you sure you want to quit?"],
            "del-target-title" : ["Az új file törlése"
                , "The new file's delition"],
            "del-target-msg" : ["Biztos, hogy törölni szeretnéd?"
                , "Are you sure you want to delete?"],
            "opening" : ["Megnyitás...", "Opening..."],
            "file-types" : ["avi file-ok", "avi files"],
            "dirl" : [
                "Az alapértelmezett mappa (ha a megadott elérési út elérhető):"
                , "The default directory (if the specified path is reachable):"
                ],
            "dire" : ["Még nem választottál alapértelmezett mappát."
                , "You haven't yet chosen a default directory."],
            "dirb" : ["Választás", "Choose"],
            "openl" : ["Az eredeti file, amit át szeretnél konvertálni:"
                , "The original file to be converted:"],
            "opene" : ["Itt jelenik majd meg az eredeti file elérési útvonala."
                , "The original file's path is going to be displayed here."],
            "openb" : ["Megnyitás", "Open"],
            "open_settingsb" : ["Beállítások", "Settings"],
            "savel" : ["Az új file, amire konvertálni fogunk:"
                , "The new file, the target of our conversion:"],
            "savee" : ["Itt jelenik majd meg az új file elérési útvonala."
                , "The target file's path is going to be displayed here."],
            "saveb" : ["Mentés", "Save"],
            "save-delb" : ["Törlés", "Delete"],
            "startb" : ["Start", "Start"],
            "stopb" : ["Stop", "Stop"],
            "elapsedl" : ["Az eltelt idő:", "The elapsed time:"],
            "leftl" : ["A becsült hátralévő idő:"
                , "The estimated remaining time:"],
            "menu-lang" : ["Nyelv", "Language"],
            "menu-update" : ["Frissítés", "Update"],
            "warn-unknown-remaining-time" : ["A hátralévő idő ismeretlen!"
                , "The remaining time is unknown!"]
        }