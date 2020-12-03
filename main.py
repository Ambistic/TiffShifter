#!/usr/bin/python

from Interface import *

if __name__ == '__main__':
    app = QApplication(sys.argv)
    interface = Interface()
    sys.exit(app.exec_())

