#! env python2.7

import tkinter.messagebox

try:
    import kwaras
    tkinter.messagebox.showinfo(title="Package is installed.",
                          message="The 'kwaras' package has been installed. Yay!")
except ImportError as e:
    tkinter.messagebox.showerror(title="Package not installed.",
                           message="The 'kwaras' package has not been installed yet. "
                                   "Run 'setup.py' or 'kwaras.win32.exe' to install it.")
    raise e
