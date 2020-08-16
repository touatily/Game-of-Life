import tkinter as tk
from tkinter import filedialog
import csv
import sim
import time
import threading as th
from tkinter import messagebox as mb
from tkinter.colorchooser import askcolor
import subprocess
import os
#from PIL import Image, ImageDraw

class window(tk.Tk):

    def __init__(self):
        super().__init__()

        self.inited = False
        self.simStarted = False

        self.colorGrid = "blue"
        self.colorCells = "black"

        # window configuration
        ## solve incompatibility problem of wm_state("zoomed") with Linux
        try:
            self.wm_state("zoomed")
        except:
            pad=3
            self.geometry("{0}x{1}+0+0".format( self.winfo_screenwidth()-pad,
                                                self.winfo_screenheight()-pad))
        self.title("Conway's game for life")

        w, h = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry("%dx%d+0+0" % (w, h))
        self.resizable(False, False)

        self.plan = tk.Frame(self, bg="grey")
        self.plan.pack(fill="both", padx=20, pady=20, expand=True)

        self.plan.grid_columnconfigure(0, weight=1)

        # menu configuration
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open", command=self.loadConfig, accelerator="Ctrl+O")
        filemenu.add_command(label="Save", command=self.saveConfig, accelerator="Ctrl+S")
        filemenu.add_command(label="Save as PDF", command=self.savePDF, accelerator="Ctrl+P")
        filemenu.add_command(label="Save as JPG", accelerator="Ctrl+J")
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.exit, accelerator="Ctrl+Q")
        menubar.add_cascade(label="File", menu=filemenu)

        editmenu = tk.Menu(menubar, tearoff=0)
        editmenu.add_command(label="Clean Grid", command = self.cleanGrid, accelerator="Ctrl+C")
        editmenu.add_command(label="Fill Grid", command = self.fillGrid, accelerator="Ctrl+F")
        menubar.add_cascade(label="Edit", menu=editmenu)

        optionmenu = tk.Menu(menubar, tearoff=0)
        optionmenu.add_command(label="Grid Color", command = self.chooseColorGrid, accelerator="F1")
        optionmenu.add_command(label="Cells Color", command = self.chooseColorCells, accelerator="F2")
        menubar.add_cascade(label="Options", menu=optionmenu)
        
        simmenu = tk.Menu(menubar, tearoff=0)
        simmenu.add_command(label="Start/Stop Simulation", command = self.start, accelerator="Enter")
        #simmenu.add_command(label="Stop Simulation" + " "*20 + "Enter", command = self.stop)
        simmenu.add_command(label="Next generation", command = self.step, accelerator="N/n/Right")
        menubar.add_cascade(label="Simulation", menu=simmenu)

        menubar.add_command(label="About", command=self.about, accelerator="Ctrl+A")
        self.config(menu=menubar)

        # canvas configuration
        self.canvas = tk.Canvas(self.plan, bg = "white",
                                height=h-91, bd=2, highlightbackground="black")
        
        self.canvas.grid(row = 0, column = 0, sticky="NEWS", ipadx=0, ipady=0)

        
        self.canvas.bind('<Button-1>', self.click1_canvas)
        self.canvas.bind('<Button-3>', self.click2_canvas)
        self.canvas.bind('<B1-Motion>', self.click1_canvas)
        self.canvas.bind('<B3-Motion>', self.click2_canvas)
        self.canvas.bind('<Motion>', self.mouseMotion)
        
        
        # control buttons
        self.plan2 = tk.Frame(self.plan)
        self.plan2.grid(row=0, column=1, sticky="SN")

        self.clean = tk.Button(self.plan2, text="Clean", command=self.cleanGrid)
        self.clean.pack(ipadx=15, padx=10, ipady=5, pady=5)
        
        self.startStop = tk.Button(self.plan2, text="Start", command=self.start)
        self.startStop.pack(ipadx=15, padx=10, ipady=5, pady=5)

        self.btnStep = tk.Button(self.plan2, text="Step", command=self.step)
        self.btnStep.pack(ipadx=15, padx=10, ipady=5, pady=5)

        self.load = tk.Button(self.plan2, text="Load", command=self.loadConfig)
        self.load.pack(ipadx=15, padx=10, ipady=5, pady=5)

        self.save = tk.Button(self.plan2, text="Save", command=self.saveConfig)
        self.save.pack(ipadx=15, padx=10, ipady=5, pady=5)


        self.lspeed = tk.Label(self.plan2, text="Speed")
        self.lspeed.pack(ipadx=15, padx=10)
        
        self.speed = tk.Scale(self.plan2, from_=100, to=1)
        self.speed.pack(ipadx=15, padx=10)

        self.bind('<Control-s>', self.saveConfig)
        self.bind('<Control-c>', self.cleanGrid)
        self.bind('<Control-f>', self.fillGrid)
        self.bind('<Control-o>', self.loadConfig)
        self.bind('<Control-q>', self.exit)
        self.bind('<Control-p>', self.savePDF)

        self.bind('<Key>', self.keyPressed)
        self.bind('<Return>', self.start)
        self.bind('<F1>', self.chooseColorGrid)
        self.bind('<F2>', self.chooseColorCells)

        self.bind('<Up>', self.increaseSpeed)
        self.bind('<Down>', self.decreaseSpeed)
        self.bind('<Right>', self.step)
        #self.bind("<Tab>", lambda e: print("ddd"))

        ## label showing mouse coordinate
        self.tv = tk.StringVar()
        self.coordinate = tk.Label(self.plan2, textvariable=self.tv, anchor='e')
        self.coordinate.pack(side="bottom", fill="x", pady=25)

    def increaseSpeed(self, e=None):
        if self.speed.get() < 100:
            self.speed.set(self.speed.get()+1)

    def decreaseSpeed(self, e=None):
        if self.speed.get() > 1:
            self.speed.set(self.speed.get()-1)

    def init(self, e = None):
        if not self.inited:
            height = self.canvas.winfo_height()
            width = self.canvas.winfo_width()
            if height > 10: self.inited=True       
            for i in range(1, height//10):
                self.canvas.create_line(0, i*10, width, i*10, fill=self.colorGrid, tag="grid")
            for i in range(1, width//10):
                self.canvas.create_line(i*10, 0, i*10, height, fill=self.colorGrid, tag="grid")

            self.nbRows = height//10
            self.nbCols = width//10

            self.gridContent = [[0 for j in range(self.nbCols)]
                                 for i in range(self.nbRows)]


    def mouseMotion(self, event):
        x = event.x // 10
        y = event.y // 10
        if (x < self.nbCols and x >= 0 and y < self.nbRows and y >=0):
            self.tv.set("x = " + str(x) + ", y = " + str(y))

        
    def cleanGrid(self, e=None):
        self.canvas.delete("cells")
        self.gridContent = [[0 for j in range(self.nbCols)]
                                 for i in range(self.nbRows)]

    def fillGrid(self, e=None):
        height = self.canvas.winfo_height()
        width = self.canvas.winfo_width()
        for i in range(0, width//10):
            x = i*10
            xx = x+10
            for j in range(0, height//10):
                y = j*10
                yy = y+10
                tagg = str(x) + "-" + str(y)
                self.canvas.create_rectangle(x+1, y+1, xx-1, yy-1, outline=self.colorCells,
                                             fill=self.colorCells, tag="cells " + tagg)

        self.gridContent = [[1 for j in range(self.nbCols)]
                                 for i in range(self.nbRows)]



    def savePDF(self, e=None):
        self.canvas.update()
        ftypes = [('PDF files', '.pdf')]
        fname = filedialog.asksaveasfilename(filetypes=ftypes, defaultextension=".pdf",
                                             title="Save as PDF file")

        if fname == "":
            return

        try:
            self.canvas.postscript(file="tmp.ps", colormode='color', rotate=True,
                                   pageheight=600, pagewidth=700)
            process = subprocess.Popen(["ps2pdf", "tmp.ps", fname])
            process.wait()
            #os.remove("tmp.ps")
            mb.showinfo('OK', 'The PDF file has been generated successfully!')
        except Exception:
            print("error")
        

    def saveJPG(self, e=None):
        """
        image1 = Image.new("RGB", (width, height), white)
        draw = ImageDraw.Draw(image1)
        draw.line([0, 100, 3, 190], green)
        filename = "my_drawing.jpg"
        image1.save(filename)
        """

    def saveConfig(self, e=None):
        fname = filedialog.asksaveasfilename(filetypes=[('CSV files', '.csv')], defaultextension=".csv",
                                             title="Save configuration as CSV file")
        if fname =="" or not fname:
            return

        print(fname)
        with open(fname, "w", newline="") as f:
            writer = csv.writer(f, delimiter=",")
            writer.writerows(self.gridContent)


    def loadConfig(self, e=None):
        fname = filedialog.askopenfilename(filetypes=[('CSV files', '.csv')], defaultextension=".csv",
                                             title="Save configuration as CSV file")
        if fname=="" or not fname:
            return
        with open(fname, "r") as f:
            reader = csv.reader(f, delimiter=",")
            l = list(reader)
            self.gridContent = [[int(ee) for ee in e] for e in l]

        self.canvas.delete("cells")
        for i in range(len(self.gridContent)):
            for j in range(len(self.gridContent[0])):
                if self.gridContent[i][j] == 1:
                    tagg = str(j*10) + "-" + str(i*10)
                    self.canvas.create_rectangle(j*10+1, i*10+1, (j+1)*10-1, (i+1)*10-1,
                                outline=self.colorCells, fill=self.colorCells, tag="cells " + tagg)
            

    def click1_canvas(self, e):
        x = e.x - e.x%10
        y = e.y - e.y%10
        if (x//10 < self.nbCols and x//10 >= 0 and y//10 < self.nbRows and y//10 >=0):
            xx = x+10
            yy = y+10
            tagg = str(x) + "-" + str(y)
            self.canvas.create_rectangle(x+1, y+1, xx-1, yy-1, fill=self.colorCells,
                                         outline=self.colorCells, tag="cells " + tagg)
            self.mouseMotion(e)
            self.gridContent[y//10][x//10] = 1

    def click2_canvas(self, e):
        x = e.x - e.x%10
        y = e.y - e.y%10
        if (x//10 < self.nbCols and x//10 >= 0 and y//10 < self.nbRows and y//10 >=0):
            tagg = str(x) + "-" + str(y)
            self.canvas.delete(tagg)
            self.mouseMotion(e)
            self.gridContent[y//10][x//10] = 0


    def start(self, e=None):
        with th.Lock():
            if not self.simStarted:
                self.simStarted = True
                self.startStop['text'] = "Stop"
                self.after(100 - self.speed.get() + 1, self.task)
            else:
                self.simStarted = False
                self.startStop['text'] = "Start"
        
        

    def stop(self):
        with th.Lock():
            if self.simStarted:
                self.simStarted = False
                self.startStop['text'] = "Start"


    def keyPressed(self, e=None):
        if e.char == "n" or e.char == "N":
            self.step()

    def step(self, e=None):
        self.gridContent = sim.nextGen(self.gridContent)
        self.canvas.delete("cells")
        for i in range(len(self.gridContent)):
            for j in range(len(self.gridContent[0])):
                if self.gridContent[i][j] == 1:
                    tagg = str(j*10) + "-" + str(i*10)
                    self.canvas.create_rectangle(j*10+1, i*10+1, (j+1)*10-1, (i+1)*10-1,
                                outline=self.colorCells, fill=self.colorCells, tag="cells " + tagg)


    def exit(self, e=None):
        self.stop()
        self.destroy()

    def task(self):
        self.step()
        with th.Lock():
            if self.simStarted:
                self.after(100 - self.speed.get() + 1, self.task)
        

    def about(self, e=None):
        mb.showinfo('No', 'Quit has been cancelled')

    def chooseColorGrid(self, e=None):
        res = askcolor(color=self.colorGrid, title = "Grid Color Chooser")
        if res[1] != None:
            self.colorGrid = res[1]
            l = self.canvas.find_withtag("grid")
            for e in l:
                self.canvas.itemconfig(e, fill=res[1]) # change color

    def chooseColorCells(self, e=None):
        res = askcolor(color=self.colorCells, title = "Cells Color Chooser")
        if res[1] != None:
            self.colorCells = res[1]
            l = self.canvas.find_withtag("cells")
            for e in l:
                self.canvas.itemconfig(e, fill=res[1], outline=res[1]) # change color

p = window()
p.bind("<Visibility>", p.init)
p.mainloop()