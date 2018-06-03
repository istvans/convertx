#!/usr/bin/python3
# -*- coding: utf-8 -*-
###############################################################################

class UniversalText:
    def __init__(self, text, single=False):
        self.text = text
        self.single = single

class Lang:
    def universal_text(self, universal_text):
        return self.text(universal_text.text, universal_text.single)

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
            "config-title" : ["Konfiguráció", "Configuration"],
            "conv" : ["Konvertálás...", "Conversion..."],
            "elapsedl" : ["Az eltelt idő:", "The elapsed time:"],
            "err-msg" : ["Hiba: '{}'", "Error: '{}'"],
            "err-space-in-path": ["Az útvonal nem tartalmazhat szóközt!", "The path cannot contain space!"],
            "extract-subs" : ["Feliratok kinyerése", "Extracting subtitles"],
            "exit-msg" : ["Biztos, hogy ki akarsz lépni?"
                , "Are you sure you want to quit?"],
            "exit-title" : ["A program bezárása", "Closing the application"],
            "del-target-msg" : ["Biztos, hogy törölni szeretnéd?"
                , "Are you sure you want to delete?"],
            "del-target-title" : ["Az új file törlése"
                , "The new file's delition"],
            "dirb" : ["Választás", "Choose"],
            "dire" : ["Még nem választottál alapértelmezett mappát."
                , "You haven't yet chosen a default directory."],
            "dirl" : [
                "Az alapértelmezett mappa (ha a megadott elérési út elérhető):"
                , "The default directory (if the specified path is reachable):"
                ],
            "file-types" : ["avi file-ok", "avi files"],
            "finished" : ["Kész!", "Done!"],
            "lang-title" : "Select Language",
            "leftl" : ["A becsült hátralévő idő:"
                , "The estimated remaining time:"],
            "menu-lang" : ["Nyelv", "Language"],
            "menu-update" : ["Frissítés", "Update"],
            "no-streams" : ["Az adatfolyamok beolvasása nem sikerült."
                    " Minden adatfolyam ki lesz választva!"
                    , "Failed to read data streams. All streams are selected!"],
            "open_settingsb" : ["Beállítások", "Settings"],
            "openb" : ["Megnyitás", "Open"],
            "opene" : ["Itt jelenik majd meg az eredeti file elérési útvonala."
                , "The original file's path is going to be displayed here."],
            "opening" : ["Megnyitás...", "Opening..."],
            "openl" : ["Az eredeti file, amit át szeretnél konvertálni:"
                , "The original file to be converted:"],
            "save-delb" : ["Törlés", "Delete"],
            "saveb" : ["Mentés", "Save"],
            "savee" : ["Itt jelenik majd meg az új file elérési útvonala."
                , "The target file's path is going to be displayed here."],
            "savel" : ["Az új file, amire konvertálni fogunk:"
                , "The new file, the target of our conversion:"],
            "startb" : ["Start", "Start"],
            "stop-msg" : ["Biztos, hogy le akarod állítani a konvertálást?"
                , "Are you sure you want to cancel the conversion?"],
            "stop-title" : ["A konvertálás megszakítása"
                , "Cancelling the conversion"],
            "stopb" : ["Stop", "Stop"],
            "stopped" : ["Megszakítva", "Cancelled"],
            "title" : ["Conv2XviD - Konvertálás XviD formátumra ({})"
                , "Conv2XviD - Conversion to XviD format ({})"],
            "unknown" : ["Ismeretlen", "Unknown"],
            "update-available" : ["Frissítés érhető el", "Update is available"],
            "update-cancel-title" : ["A frissítő bezárása", "Closing the updater"],
            "update-cancel" : ["Biztos, hogy be akarod zárni az ablakot?"
                , "Are you sure you want to close this window?"],
            "update-cancel-install-title" : ["Telepítés folyamatban...", "The installation is in progress..."],
            "update-cancel-install" : ["Biztos, hogy be akarod zárni az ablakot?"
                " A telepítés folytatódni fog a háttérben."
                , "Are you sure you want to close this window? The installation is going to continue."],
            "update-candidate" : ["Elérhető verzió:", "Candidate version:"],
            "update-failed" : ["Hiba: {}", "Error: {}"],
            "update-finished" : ["A frissítés sikeresen befejeződött.", "The update has successfully finished"],
            "update-install" : ["Az új verzió telepítése...", "Installing the new version..."],
            "update-installed" : ["Jelenlegi verzió:", "Installed version:"],
            "update-latest" : ["A legfrissebb verzió már telepítve van", "You have the latest version installed"],
            "update-ok-available" : ["Telepítés", "Install"],
            "update-ok-search" : ["Frissítések keresése", "Search"],
            "update-pass-empty" : ["Kérlek először add meg a jelszavad", "Please provide your password first"],
            "update-pass" : ["Jelszó:", "Password:"],
            "update-search" : ["Új verzió keresése...", "Looking for new version..."],
            "update-title" : ["A program frissítése", "Application update"],
            "version" : "v1.0.0",
            "warn-permission" : ["Hozzáférés megtagadva!", "Permission error!"],
            "warn-unknown-remaining-time" : ["A hátralévő idő ismeretlen!"
                , "The remaining time is unknown!"],
            "AUDIO" : ["Hang", "Audio"],
            "OK" : "OK",
            "SUBTITLE" : ["Felirat", "Subtitle"],
            "VIDEO" : ["Videó", "Video"],
        }