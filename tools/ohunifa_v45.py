#!/usr/bin/env python3

import cmd

class OhunIFAShell(cmd.Cmd):
    intro = """
==========================================================
             OHÙN IFÁ Processor V4.5
==========================================================

Type help or ? to list commands.
"""
    prompt = "OHUNIFA> "

    def __init__(self):
        super().__init__()
        self.backend = "rtl"
        self.current_yara = None
        self.rooms = {}

    def do_backend(self, arg):
        arg = arg.strip().lower()
        if arg in ("rtl", "python", "qiskit"):
            self.backend = arg
            print(f"Backend = {arg}")
        else:
            print("Usage: backend rtl|python|qiskit")

    def do_status(self, arg):
        print(f"Backend : {self.backend}")
        print(f"Current : {self.current_yara}")

    def do_onile(self, arg):
        OnileShell(self).cmdloop()

    def do_exit(self, arg):
        return True

    do_quit = do_exit


class OnileShell(cmd.Cmd):

    prompt = "ONILE> "

    def __init__(self,parent):
        super().__init__()
        self.parent = parent

    def do_da(self,arg):
        words = arg.upper().split()

        if len(words)!=2 or words[0]!="ODU":
            print("Usage: DA ODU <NAME>")
            return

        name = words[1]

        if name in self.parent.rooms:
            print("Already exists.")
            return

        idx=len(self.parent.rooms)
        self.parent.rooms[name]=idx

        print(f"Created YARA {idx}")

    def do_list(self,arg):
        for k,v in self.parent.rooms.items():
            print(v,k)

    def do_yara(self,arg):
        name=arg.upper().strip()

        if name not in self.parent.rooms:
            print("Unknown YARA")
            return

        self.parent.current_yara=name
        YaraShell(self.parent,name).cmdloop()

    def do_exit(self,arg):
        return True

    do_quit=do_exit


class YaraShell(cmd.Cmd):

    def __init__(self,parent,name):
        super().__init__()
        self.parent=parent
        self.prompt=f"{name}> "

    def do_papo(self,arg):
        print("RTL backend not connected yet.")
        print("This will execute PAPO using the V4.5 PE bank.")

    def do_exit(self,arg):
        return True

    do_quit=do_exit


if __name__=="__main__":
    OhunIFAShell().cmdloop()
