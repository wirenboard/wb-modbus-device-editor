# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# repo: https://gist.github.com/mp035/9f2027c3ef9172264532fcd6262f3b01
import platform
import tkinter

# ************************
# Scrollable Frame Class
# ************************


class ScrollFrame(tkinter.Frame):
    def __init__(self, parent):
        super().__init__(parent)  # create a frame (self)

        # place canvas on self
        self.canvas = tkinter.Canvas(self, borderwidth=0)
        # place a frame on the canvas, this frame will hold the child widgets
        self.viewPort = tkinter.Frame(self.canvas)
        # place a scrollbar on self
        self.vsb = tkinter.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        # attach scrollbar action to scroll of canvas
        self.canvas.configure(yscrollcommand=self.vsb.set)

        # pack scrollbar to right of self
        self.vsb.pack(side="right", fill="y")
        # pack canvas to left of self and expand to fil
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas_window = self.canvas.create_window(
            (4, 4), window=self.viewPort, anchor="nw", tags="self.viewPort"  # add view port frame to canvas
        )

        # bind an event whenever the size of the viewPort frame changes.
        self.viewPort.bind("<Configure>", self.onFrameConfigure)
        # bind an event whenever the size of the canvas frame changes.
        self.canvas.bind("<Configure>", self.onCanvasConfigure)

        # bind wheel events when the cursor enters the control
        self.viewPort.bind("<Enter>", self.onEnter)
        # unbind wheel events when the cursorl leaves the control
        self.viewPort.bind("<Leave>", self.onLeave)

        # perform an initial stretch on render, otherwise the scroll region has a tiny border until the first resize
        self.onFrameConfigure(None)

    def onFrameConfigure(self, event):
        """Reset the scroll region to encompass the inner frame"""
        self.canvas.configure(
            scrollregion=self.canvas.bbox("all")
        )  # whenever the size of the frame changes, alter the scroll region respectively.

    def onCanvasConfigure(self, event):
        """Reset the canvas window to encompass inner frame when required"""
        canvas_width = event.width
        # whenever the size of the canvas changes alter the window region respectively.
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    # cross platform scroll wheel event
    def onMouseWheel(self, event):
        if platform.system() == "Windows":
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif platform.system() == "Darwin":
            self.canvas.yview_scroll(int(-1 * event.delta), "units")
        else:
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")

    # bind wheel events when the cursor enters the control
    def onEnter(self, event):
        if platform.system() == "Linux":
            self.canvas.bind_all("<Button-4>", self.onMouseWheel)
            self.canvas.bind_all("<Button-5>", self.onMouseWheel)
        else:
            self.canvas.bind_all("<MouseWheel>", self.onMouseWheel)

    # unbind wheel events when the cursorl leaves the control
    def onLeave(self, event):
        if platform.system() == "Linux":
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")
        else:
            self.canvas.unbind_all("<MouseWheel>")
