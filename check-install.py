__author__ = 'Lucien'

import tkMessageBox

try:
    import kwaras
    tkMessageBox.showinfo(title="Package is installed.",
                          message="The 'kwaras' package has been installed. Yay!")
except ImportError as e:
    tkMessageBox.showerror(title="Package not installed.",
                           message="The 'kwaras' package has not been installed yet. "
                                   "Run 'setup.py' or 'kwaras.win32.exe' to install it.")
    raise e
