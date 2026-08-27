import tkinter as tk

from plc_monitor.ui.main_window import PLCMonitorApp


def main():
    root = tk.Tk()
    PLCMonitorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
