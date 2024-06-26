import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
import os
from tkinter import *
from tkinter import filedialog
from scipy import optimize
import pandas as pd
import matplotlib.figure 
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)

np.set_printoptions(suppress=True)

window=tk.Tk()
window.title("Collinearaity Analyzer")

isPoint0 = True
isPoint1 = True
isPoint2 = True
isPoint3 = True
isPoint4 = True
isPoint5 = True
isPoint6 = True
isPoint7 = True

def browseFolder():
    global folder_selected
    folder_selected = filedialog.askdirectory(initialdir=r"C:\Users\maxwe\OneDrive\Desktop")
    if folder_selected:
        files = [os.path.join(folder_selected,file) for file in os.listdir(folder_selected)]
        sortedFiles = sorted(files)
        global file0
        global file1
        global file2
        for file in files:
            if file.split("_")[-1]=="7-13.txt":
                file0=file
            if file.split("_")[-1]=="3-8.txt":
                file1=file
            if file.split("_")[-1]=="0-5.txt":
                file2=file
        file0_lbl.config(text=f"{folder_selected}")
        global staveType
        fileName = os.path.basename(folder_selected)
        if not fileName[0]=="O":
            staveType = fileName.split('_')[0]+"_"+ fileName.split('_')[-1]
        else:
            staveType = fileName.split('_')[-1]
fileFrame = tk.Frame(master=window, relief=tk.SUNKEN, borderwidth=2)
fileFrame.pack()

file713_btn = tk.Button(master=fileFrame, text="Select Measurement Folder",command=browseFolder)
file713_btn.grid(row=0, column=0, pady=10)
file0_lbl = tk.Label(master = fileFrame, text="No File Selected")
file0_lbl.grid(row=0, column=1, pady=10)

def passFail(array):
    if (np.max(array)<0.1 and np.min(array) > -0.1):
        test_lbl.config(text="The Stave Core has PASSED", bg="green")
    else:
        test_lbl.config(text="The Stave Core has FAILED", bg="red")



def runScript():

    if not os.path.exists(folder_selected + "\\Stave" +staveType +"_Test Results"):
        resultFolder = folder_selected + "\\Stave" +staveType +"_Test Results"
        os.mkdir(resultFolder)

    f0 = np.loadtxt(file0, skiprows=7, usecols=(2,3))
    f0 = np.concatenate([[[0,0]],f0], axis=0)

    f1 = np.loadtxt(file1, skiprows=7, usecols=(2,3))
    f1 = np.concatenate([[[0,0]],f1], axis=0)

    f2 = np.loadtxt(file2, skiprows=7, usecols=(2,3))
    f2 = np.concatenate([[[0,0]],f2], axis=0)

    near_fiducial_idxs0 = np.array([0,2,4,6,8,10,12])
    near_fiducial_idxs1 = np.array([0,2,4,6,8,10])
    near_fiducial_idxs2 = np.array([0,2,4,6,8,10])

    common_fiducials01 = np.array([
    [10,   0],
    [12,   2],
    [30, 30],
    ])

    common_lockpoints01 = np.array([
    [15, 25],
    [18, 28],
    ])

    common_fiducials12 = np.array([
    [6,   0],
    [8,   2],
    [10,   4],    
    [34, 30],
    [36, 32],
    ])

    common_lockpoints12 = np.array([
    [13,  19],
    [16,  22],
    [19,  25],
    [22,  28],
    ])
    fiducials00 = f0[common_fiducials01[:,0]]
    fiducials01 = f1[common_fiducials01[:,1]]

    lockpoints00 = f0[common_lockpoints01[:,0]]
    lockpoints01 = f1[common_lockpoints01[:,1]]

    allpoints00 = np.concatenate([fiducials00, lockpoints00])
    allpoints01 = np.concatenate([fiducials01, lockpoints01])

    fiducials11 = f1[common_fiducials12[:,0]]
    fiducials12 = f2[common_fiducials12[:,1]]

    lockpoints11 = f1[common_lockpoints12[:,0]]
    lockpoints12 = f2[common_lockpoints12[:,1]]

    allpoints11 = np.concatenate([fiducials11, lockpoints11])
    allpoints12 = np.concatenate([fiducials12, lockpoints12])
    def rigid(points, params):
        theta, *d = params
        d = np.array(d)
    
        R = np.array([[np.cos(theta), -np.sin(theta)],[np.sin(theta), np.cos(theta)]])
    
        return np.einsum('ij,nj->ni', R, points) - d
    
    def cost_fn(points0, points1):
        def fn(inputs):
            return np.mean( (points1 - rigid(points0, inputs))**2 )
        return fn
    
    correction01 = optimize.minimize(cost_fn(allpoints00, allpoints01), (0,0,0)).x
    correction12 = optimize.minimize(cost_fn(allpoints12, allpoints11), (0,0,0)).x
    f0_corrected = rigid(f0, correction01)
    f2_corrected = rigid(f2, correction12)

    ax3.clear()
    ax3.set_title("Reconstruction of Stave " + staveType + " after Stitching")
    ax3.set_xlabel("X position in mm")
    ax3.set_ylabel("Y position in mm")
    ax3.scatter(f0_corrected[:,0], f0_corrected[:,1], s=40, alpha=0.7)
    ax3.scatter(f1[:,0], f1[:,1], s=16, alpha=0.7)
    ax3.scatter(f2_corrected[:,0], f2_corrected[:,1], s=16, alpha=0.7)
    canvas3.draw()
    fig3.savefig(folder_selected + "\\Stave" +staveType +"_Test Results\\"+"Reconstruction After Stitching_"+ staveType+".png")
    

    FiducialsALL= np.concatenate([f0_corrected[near_fiducial_idxs0], f1[near_fiducial_idxs1], f2_corrected[near_fiducial_idxs2]], axis=0)

    weight = np.array([1, 1, 1, 1, 1, 0.5, 0.5, 0.5, 0.5, 1, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 1, 1, 1])
    a, b = np.polyfit(FiducialsALL[:,0], FiducialsALL[:,1], 1, w = weight)

    def ROTATE(points, angle):
        R = np.array([[np.cos(angle), -np.sin(angle)],[np.sin(angle), np.cos(angle)]])
        return np.einsum('ij,nj->ni', R, points)
    
    alpha = -np.arctan(a)

    f0_rotated = ROTATE(f0_corrected, alpha)


    offxD = f0_rotated[0,0]
    offyD = f0_rotated[0,1]

    LPidxs0 = np.array([15, 18, 21, 24])
    LPidxs1 = np.array([13, 16, 19, 22, 25, 28])
    LPidxs2 = np.array([13, 16, 19, 22, 25, 28])

    LpAll= np.concatenate([f0_corrected[LPidxs0], f1[LPidxs1], f2_corrected[LPidxs2]], axis=0)
    RotatedLpAll = ROTATE(LpAll, alpha)

    LpAll_re = RotatedLpAll.reshape(-1,2,2)
    LpAll_ave = np.mean(LpAll_re, axis=1)

    LPweight = np.array([0.5, 1, 0.5, 0.5, 0.5, 1, 0.5, 0.5])
    e, f = np.polyfit(LpAll_ave[:,0], LpAll_ave[:,1], 1, w = LPweight)

    LpAll_ave_1 = LpAll_ave[0:2,:]
    LpAll_ave_2 = LpAll_ave[2:5,:]
    LpAll_ave_3 = LpAll_ave[5:,:]

    ax2.clear()
    ax2.scatter(LpAll_ave_1[:,0]-offxD, LpAll_ave_1[:,1]-offyD);
    ax2.scatter(LpAll_ave_2[:,0]-offxD, LpAll_ave_2[:,1]-offyD);
    ax2.scatter(LpAll_ave_3[:,0]-offxD, LpAll_ave_3[:,1]-offyD);

    ax2.set_ylabel("Y position in mm")
    ax2.set_xlabel("X position in mm")
    ax2.set_title("Lockpoint positions of Stave " + staveType)

    ax2.plot(LpAll_ave[:,0] - offxD, LpAll_ave[:,0]*e + f - offyD, "r-" )
    ax2.grid()
    canvas2.draw()
    fig2.savefig(folder_selected + "\\Stave" +staveType +"_Test Results\\"+"Locking Point Positions_"+ staveType+".png")

    tableLpx = np.array([LpAll_ave[1,0],LpAll_ave[0,0],LpAll_ave[4,0],LpAll_ave[3,0],LpAll_ave[7,0],LpAll_ave[2,0],LpAll_ave[6,0],LpAll_ave[5,0]])
    tableLpy = np.array([LpAll_ave[1,1],LpAll_ave[0,1],LpAll_ave[4,1],LpAll_ave[3,1],LpAll_ave[7,1],LpAll_ave[2,1],LpAll_ave[6,1],LpAll_ave[5,1]])

    x0.config(text=f"{round(tableLpx[0]-offxD,5)}")  
    x1.config(text=f"{round(tableLpx[1]-offxD,5)}") 
    x2.config(text=f"{round(tableLpx[2]-offxD,5)}") 
    x3.config(text=f"{round(tableLpx[3]-offxD,5)}") 
    x4.config(text=f"{round(tableLpx[4]-offxD,5)}") 
    x5.config(text=f"{round(tableLpx[5]-offxD,5)}") 
    x6.config(text=f"{round(tableLpx[6]-offxD,5)}") 
    x7.config(text=f"{round(tableLpx[7]-offxD,5)}") 
    
    y0.config(text=f"{round(tableLpy[0]-offyD,5)}") 
    y1.config(text=f"{round(tableLpy[1]-offyD,5)}") 
    y2.config(text=f"{round(tableLpy[2]-offyD,5)}") 
    y3.config(text=f"{round(tableLpy[3]-offyD,5)}") 
    y4.config(text=f"{round(tableLpy[4]-offyD,5)}") 
    y5.config(text=f"{round(tableLpy[5]-offyD,5)}") 
    y6.config(text=f"{round(tableLpy[6]-offyD,5)}") 
    y7.config(text=f"{round(tableLpy[7]-offyD,5)}") 
    def point0():
        global isPoint0
        if (not isPoint1) or (not isPoint2) or (not isPoint3) or (not isPoint4) or (not isPoint5) or (not isPoint6) or (not isPoint7):
            btn0.config(text="Remove Point?")
        else:
            if isPoint0:
                btn0.config(text="Add Point?")            
                LpAll_ave_1_new = np.delete(LpAll_ave_1, 1, 0)
                LpAll_ave_new= np.delete(LpAll_ave, 1, 0)
                ax2.clear()
                ax2.scatter(LpAll_ave_1_new[:,0]-offxD, LpAll_ave_1_new[:,1]-offyD);
                ax2.scatter(LpAll_ave_2[:,0]-offxD, LpAll_ave_2[:,1]-offyD);
                ax2.scatter(LpAll_ave_3[:,0]-offxD, LpAll_ave_3[:,1]-offyD);
                ax2.plot(LpAll_ave_new[:,0] - offxD, LpAll_ave_new[:,0]*e + f - offyD, "r-" )
                LPweight_new = np.array([0.5, 0.5, 0.5, 0.5, 1, 0.5, 0.5])
                m , b = np.polyfit(LpAll_ave_new[:,0], LpAll_ave_new[:,1], 1, w=LPweight_new)
                ax2.plot(LpAll_ave_new[:,0] - offxD, LpAll_ave_new[:,0]*m + b - offyD, "g-")
                ax2.set_ylabel("Y position in mm")
                ax2.set_xlabel("X position in mm")
                ax2.set_title("Lockpoint positions of Stave " + staveType)
                ax2.grid()
                canvas2.draw()
                passFail(LpAll_ave_new[:,1] - LpAll_ave_new[:,0]*e - f)
                resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave_new[:,1] - LpAll_ave_new[:,0]*e - f),5)}")
                resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave_new[:,1] - LpAll_ave_new[:,0]*e - f),5)}")
                isPoint0 = False
            else:
                btn0.config(text="Remove Point?")
                ax2.clear()
                ax2.scatter(LpAll_ave_1[:,0]-offxD, LpAll_ave_1[:,1]-offyD);
                ax2.scatter(LpAll_ave_2[:,0]-offxD, LpAll_ave_2[:,1]-offyD);
                ax2.scatter(LpAll_ave_3[:,0]-offxD, LpAll_ave_3[:,1]-offyD);
                ax2.plot(LpAll_ave[:,0] - offxD, LpAll_ave[:,0]*e + f - offyD, "r-" )
                ax2.set_ylabel("Y position in mm")
                ax2.set_xlabel("X position in mm")
                ax2.set_title("Lockpoint positions of Stave " + staveType)
                ax2.grid()
                canvas2.draw()
                passFail(LpAll_ave[:,1] - LpAll_ave[:,0]*e - f)
                resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave[:,1] - LpAll_ave[:,0]*e - f),5)}")
                resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave[:,1] - LpAll_ave[:,0]*e - f),5)}")
                isPoint0 = True
    def point1():
        global isPoint1
        if (not isPoint0) or (not isPoint3) or (not isPoint4) or (not isPoint5) or (not isPoint6) or (not isPoint7):
            btn1.config(text="Remove Point?")
        else:
            if isPoint1:
                btn1.config(text="Add Point?")            
                LpAll_ave_1_new = np.delete(LpAll_ave_1, 0, 0)
                LpAll_ave_new= np.delete(LpAll_ave, 0, 0)
                ax2.clear()
                if not isPoint2:
                    LpAll_ave_2_new = np.delete(LpAll_ave_2, 2, 0)
                    LpAll_ave_newer = np.delete(LpAll_ave_new, 3, 0)
                    ax2.scatter(LpAll_ave_1_new[:,0]-offxD, LpAll_ave_1_new[:,1]-offyD);
                    ax2.scatter(LpAll_ave_2_new[:,0]-offxD, LpAll_ave_2_new[:,1]-offyD);
                    ax2.scatter(LpAll_ave_3[:,0]-offxD, LpAll_ave_3[:,1]-offyD);
                    ax2.plot(LpAll_ave_newer[:,0] - offxD, LpAll_ave_newer[:,0]*e + f - offyD, "r-" )
                    LPweight_new = np.array([1, 0.5, 0.5, 1, 0.5, 0.5])
                    m , b = np.polyfit(LpAll_ave_newer[:,0], LpAll_ave_newer[:,1], 1, w=LPweight_new)
                    ax2.plot(LpAll_ave_newer[:,0] - offxD, LpAll_ave_newer[:,0]*m + b - offyD, "g-")
                    passFail(LpAll_ave_newer[:,1] - LpAll_ave_newer[:,0]*e - f)
                    resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave_newer[:,1] - LpAll_ave_newer[:,0]*e - f),5)}")
                    resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave_newer[:,1] - LpAll_ave_newer[:,0]*e - f),5)}")
                else:
                    ax2.scatter(LpAll_ave_1_new[:,0]-offxD, LpAll_ave_1_new[:,1]-offyD);
                    ax2.scatter(LpAll_ave_2[:,0]-offxD, LpAll_ave_2[:,1]-offyD);
                    ax2.scatter(LpAll_ave_3[:,0]-offxD, LpAll_ave_3[:,1]-offyD);
                    ax2.plot(LpAll_ave_new[:,0] - offxD, LpAll_ave_new[:,0]*e + f - offyD, "r-" )
                    LPweight_new = np.array([1, 0.5, 0.5, 0.5, 1, 0.5, 0.5])
                    m1 , b1 = np.polyfit(LpAll_ave_new[:,0], LpAll_ave_new[:,1], 1, w=LPweight_new)
                    ax2.plot(LpAll_ave_new[:,0] - offxD, LpAll_ave_new[:,0]*m1 + b1 - offyD, "g-")
                    passFail(LpAll_ave_new[:,1] - LpAll_ave_new[:,0]*e - f)
                    resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave_new[:,1] - LpAll_ave_new[:,0]*e - f),5)}")
                    resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave_new[:,1] - LpAll_ave_new[:,0]*e - f),5)}")
                ax2.set_ylabel("Y position in mm")
                ax2.set_xlabel("X position in mm")
                ax2.set_title("Lockpoint positions of Stave " + staveType)
                ax2.grid()
                canvas2.draw()
                isPoint1 = False
            else:
                btn1.config(text="Remove Point?")
                ax2.clear()
                if not isPoint2:
                    LpAll_ave_2_new = np.delete(LpAll_ave_2, 2, 0)
                    LpAll_ave_newish = np.delete(LpAll_ave, 4, 0)
                    ax2.scatter(LpAll_ave_1[:,0]-offxD, LpAll_ave_1[:,1]-offyD);
                    ax2.scatter(LpAll_ave_2_new[:,0]-offxD, LpAll_ave_2_new[:,1]-offyD);
                    ax2.scatter(LpAll_ave_3[:,0]-offxD, LpAll_ave_3[:,1]-offyD);
                    ax2.plot(LpAll_ave_newish[:,0] - offxD, LpAll_ave_newish[:,0]*e + f - offyD, "r-" )
                    LPweight_new = np.array([0.5, 1, 0.5, 0.5, 1, 0.5, 0.5])
                    m2 , b2 = np.polyfit(LpAll_ave_newish[:,0], LpAll_ave_newish[:,1], 1, w=LPweight_new)
                    ax2.plot(LpAll_ave_newish[:,0] - offxD, LpAll_ave_newish[:,0]*m2 + b2 - offyD, "g-")
                    passFail(LpAll_ave_newish[:,1] - LpAll_ave_newish[:,0]*e - f)
                    resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave_newish[:,1] - LpAll_ave_newish[:,0]*e - f),5)}")
                    resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave_newish[:,1] - LpAll_ave_newish[:,0]*e - f),5)}")
                else:
                    ax2.scatter(LpAll_ave_1[:,0]-offxD, LpAll_ave_1[:,1]-offyD);
                    ax2.scatter(LpAll_ave_2[:,0]-offxD, LpAll_ave_2[:,1]-offyD);
                    ax2.scatter(LpAll_ave_3[:,0]-offxD, LpAll_ave_3[:,1]-offyD);
                    ax2.plot(LpAll_ave[:,0] - offxD, LpAll_ave[:,0]*e + f - offyD, "r-" )
                    passFail(LpAll_ave[:,1] - LpAll_ave[:,0]*e - f)
                    resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave[:,1] - LpAll_ave[:,0]*e - f),5)}")
                    resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave[:,1] - LpAll_ave[:,0]*e - f),5)}")
                ax2.set_ylabel("Y position in mm")
                ax2.set_xlabel("X position in mm")
                ax2.set_title("Lockpoint positions of Stave " + staveType)
                ax2.grid()
                canvas2.draw()
                isPoint1 = True
    def point2():
        global isPoint2
        if (not isPoint0) or (not isPoint3) or (not isPoint4) or (not isPoint5) or (not isPoint6) or (not isPoint7):
            btn2.config(text="Remove Point?")
        else:
            if isPoint2:
                btn2.config(text="Add Point?")
                LpAll_ave_2_new = np.delete(LpAll_ave_2, 2, 0)
                LpAll_ave_new = np.delete(LpAll_ave, 4, 0)
                ax2.clear()
                if not isPoint1:
                    LpAll_ave_1_new = np.delete(LpAll_ave_1, 0, 0)
                    LpAll_ave_newer = np.delete(LpAll_ave_new, 0, 0)
                    ax2.scatter(LpAll_ave_1_new[:,0]-offxD, LpAll_ave_1_new[:,1]-offyD);
                    ax2.scatter(LpAll_ave_2_new[:,0]-offxD, LpAll_ave_2_new[:,1]-offyD);
                    ax2.scatter(LpAll_ave_3[:,0]-offxD, LpAll_ave_3[:,1]-offyD);
                    ax2.plot(LpAll_ave_newer[:,0] - offxD, LpAll_ave_newer[:,0]*e + f - offyD, "r-" )
                    LPweight_new = np.array([1, 0.5, 0.5, 1, 0.5, 0.5])
                    m , b = np.polyfit(LpAll_ave_newer[:,0], LpAll_ave_newer[:,1], 1, w=LPweight_new)
                    ax2.plot(LpAll_ave_newer[:,0] - offxD, LpAll_ave_newer[:,0]*m + b - offyD, "g-")
                    passFail(LpAll_ave_newer[:,1] - LpAll_ave_newer[:,0]*e - f)  
                    resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave_newer[:,1] - LpAll_ave_newer[:,0]*e - f),5)}")
                    resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave_newer[:,1] - LpAll_ave_newer[:,0]*e - f),5)}")
                else:
                    ax2.scatter(LpAll_ave_1[:,0]-offxD, LpAll_ave_1[:,1]-offyD);
                    ax2.scatter(LpAll_ave_2_new[:,0]-offxD, LpAll_ave_2_new[:,1]-offyD);
                    ax2.scatter(LpAll_ave_3[:,0]-offxD, LpAll_ave_3[:,1]-offyD);
                    ax2.plot(LpAll_ave_new[:,0] - offxD, LpAll_ave_new[:,0]*e + f - offyD, "r-" )
                    LPweight_new = np.array([0.5, 1, 0.5, 0.5, 1, 0.5, 0.5])
                    m1 , b1 = np.polyfit(LpAll_ave_new[:,0], LpAll_ave_new[:,1], 1, w=LPweight_new)
                    ax2.plot(LpAll_ave_new[:,0] - offxD, LpAll_ave_new[:,0]*m1 + b1 - offyD, "g-")
                    passFail(LpAll_ave_new[:,1] - LpAll_ave_new[:,0]*e - f)   
                    resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave_new[:,1] - LpAll_ave_new[:,0]*e - f),5)}")
                    resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave_new[:,1] - LpAll_ave_new[:,0]*e - f),5)}")
                ax2.set_ylabel("Y position in mm")
                ax2.set_xlabel("X position in mm")
                ax2.set_title("Lockpoint positions of Stave " + staveType)
                ax2.grid()
                canvas2.draw()
                isPoint2 = False
            else:
                btn2.config(text="Remove Point?")
                ax2.clear()
                if not isPoint1:
                    LpAll_ave_1_new = np.delete(LpAll_ave_1, 0, 0)
                    LpAll_ave_newish = np.delete(LpAll_ave, 0, 0)
                    ax2.scatter(LpAll_ave_1_new[:,0]-offxD, LpAll_ave_1_new[:,1]-offyD);
                    ax2.scatter(LpAll_ave_2[:,0]-offxD, LpAll_ave_2[:,1]-offyD);
                    ax2.scatter(LpAll_ave_3[:,0]-offxD, LpAll_ave_3[:,1]-offyD);
                    ax2.plot(LpAll_ave_newish[:,0] - offxD, LpAll_ave_newish[:,0]*e + f - offyD, "r-" )
                    LPweight_new = np.array([1, 0.5, 0.5, 0.5, 1, 0.5, 0.5])
                    m2 , b2 = np.polyfit(LpAll_ave_newish[:,0], LpAll_ave_newish[:,1], 1, w=LPweight_new)
                    ax2.plot(LpAll_ave_newish[:,0] - offxD, LpAll_ave_newish[:,0]*m2 + b2 - offyD, "g-")
                    passFail(LpAll_ave_newish[:,1] - LpAll_ave_newish[:,0]*e - f)
                    resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave_newish[:,1] - LpAll_ave_newish[:,0]*e - f),5)}")
                    resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave_newish[:,1] - LpAll_ave_newish[:,0]*e - f),5)}")
                else:
                    ax2.scatter(LpAll_ave_1[:,0]-offxD, LpAll_ave_1[:,1]-offyD);
                    ax2.scatter(LpAll_ave_2[:,0]-offxD, LpAll_ave_2[:,1]-offyD);
                    ax2.scatter(LpAll_ave_3[:,0]-offxD, LpAll_ave_3[:,1]-offyD);
                    ax2.plot(LpAll_ave[:,0] - offxD, LpAll_ave[:,0]*e + f - offyD, "r-" )
                    passFail(LpAll_ave[:,1] - LpAll_ave[:,0]*e - f)
                    resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave[:,1] - LpAll_ave[:,0]*e - f),5)}")
                    resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave[:,1] - LpAll_ave[:,0]*e - f),5)}")
                ax2.set_ylabel("Y position in mm")
                ax2.set_xlabel("X position in mm")
                ax2.set_title("Lockpoint positions of Stave " + staveType)              
                ax2.grid()
                canvas2.draw()
                isPoint2 = True
    def point3():
        global isPoint3
        if (not isPoint0) or (not isPoint1) or (not isPoint2) or (not isPoint5) or (not isPoint6) or (not isPoint7):
            btn3.configure(text="Remove Point?")
        else:
            if isPoint3:
                btn3.config(text="Add Point?")
                ax2.clear()
                LpAll_ave_2_new = np.delete(LpAll_ave_2, 1, 0)
                LpAll_ave_new = np.delete(LpAll_ave, 3, 0)
                if not isPoint4:
                    LpAll_ave_3_new = np.delete(LpAll_ave_3, 2,0)
                    LpAll_ave_newer = np.delete(LpAll_ave_new, 6, 0)
                    ax2.scatter(LpAll_ave_1[:,0]-offxD, LpAll_ave_1[:,1]-offyD);
                    ax2.scatter(LpAll_ave_2_new[:,0]-offxD, LpAll_ave_2_new[:,1]-offyD);
                    ax2.scatter(LpAll_ave_3_new[:,0]-offxD, LpAll_ave_3_new[:,1]-offyD);
                    ax2.plot(LpAll_ave_newer[:,0] - offxD, LpAll_ave_newer[:,0]*e + f - offyD, "r-" )
                    LPweight_new = np.array([0.5, 1, 0.5, 0.5, 1, 0.5])
                    m , b = np.polyfit(LpAll_ave_newer[:,0], LpAll_ave_newer[:,1], 1, w=LPweight_new)
                    ax2.plot(LpAll_ave_newer[:,0] - offxD, LpAll_ave_newer[:,0]*m + b - offyD, "g-")
                    passFail(LpAll_ave_newer[:,1] - LpAll_ave_newer[:,0]*e - f)
                    resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave_newer[:,1] - LpAll_ave_newer[:,0]*e - f),5)}")
                    resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave_newer[:,1] - LpAll_ave_newer[:,0]*e - f),5)}")
                else:
                    ax2.scatter(LpAll_ave_1[:,0]-offxD, LpAll_ave_1[:,1]-offyD);
                    ax2.scatter(LpAll_ave_2_new[:,0]-offxD, LpAll_ave_2_new[:,1]-offyD);
                    ax2.scatter(LpAll_ave_3[:,0]-offxD, LpAll_ave_3[:,1]-offyD);
                    ax2.plot(LpAll_ave_new[:,0] - offxD, LpAll_ave_new[:,0]*e + f - offyD, "r-" )
                    LPweight_new = np.array([0.5, 1, 0.5, 0.5, 1, 0.5, 0.5])
                    m , b = np.polyfit(LpAll_ave_new[:,0], LpAll_ave_new[:,1], 1, w=LPweight_new)
                    ax2.plot(LpAll_ave_new[:,0] - offxD, LpAll_ave_new[:,0]*m + b - offyD, "g-")
                    passFail(LpAll_ave_new[:,1] - LpAll_ave_new[:,0]*e - f)
                    resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave_new[:,1] - LpAll_ave_new[:,0]*e - f),5)}")
                    resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave_new[:,1] - LpAll_ave_new[:,0]*e - f),5)}")
                ax2.set_ylabel("Y position in mm")
                ax2.set_xlabel("X position in mm")
                ax2.set_title("Lockpoint positions of Stave " + staveType)             
                ax2.grid()
                canvas2.draw()
                isPoint3 = False
            else:
                btn3.config(text="Remove Point?")
                ax2.clear()
                if not isPoint4:
                    LpAll_ave_3_new = np.delete(LpAll_ave_3, 2,0)
                    LpAll_ave_newish = np.delete(LpAll_ave, 7, 0)
                    ax2.scatter(LpAll_ave_1[:,0]-offxD, LpAll_ave_1[:,1]-offyD);
                    ax2.scatter(LpAll_ave_2[:,0]-offxD, LpAll_ave_2[:,1]-offyD);
                    ax2.scatter(LpAll_ave_3_new[:,0]-offxD, LpAll_ave_3_new[:,1]-offyD);
                    ax2.plot(LpAll_ave_newish[:,0] - offxD, LpAll_ave_newish[:,0]*e + f - offyD, "r-" )
                    LPweight_new = np.array([0.5, 1, 0.5, 0.5, 0.5, 1, 0.5])
                    m , b = np.polyfit(LpAll_ave_newish[:,0], LpAll_ave_newish[:,1], 1, w=LPweight_new)
                    ax2.plot(LpAll_ave_newish[:,0] - offxD, LpAll_ave_newish[:,0]*m + b - offyD, "g-")
                    passFail(LpAll_ave_newish[:,1] - LpAll_ave_newish[:,0]*e - f)
                    resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave_newish[:,1] - LpAll_ave_newish[:,0]*e - f),5)}")
                    resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave_newish[:,1] - LpAll_ave_newish[:,0]*e - f),5)}")
                else:
                    ax2.scatter(LpAll_ave_1[:,0]-offxD, LpAll_ave_1[:,1]-offyD);
                    ax2.scatter(LpAll_ave_2[:,0]-offxD, LpAll_ave_2[:,1]-offyD);
                    ax2.scatter(LpAll_ave_3[:,0]-offxD, LpAll_ave_3[:,1]-offyD);
                    ax2.plot(LpAll_ave[:,0] - offxD, LpAll_ave[:,0]*e + f - offyD, "r-" )
                    passFail(LpAll_ave[:,1] - LpAll_ave[:,0]*e - f)
                    resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave[:,1] - LpAll_ave[:,0]*e - f),5)}")
                    resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave[:,1] - LpAll_ave[:,0]*e - f),5)}")
                ax2.set_ylabel("Y position in mm")
                ax2.set_xlabel("X position in mm")
                ax2.set_title("Lockpoint positions of Stave " + staveType)              
                ax2.grid()
                canvas2.draw()
                isPoint3 = True
    def point4():
        global isPoint4
        if (not isPoint0) or (not isPoint1) or (not isPoint2) or (not isPoint5) or (not isPoint6) or (not isPoint7):
            btn4.config(text="Remove Point?")
        else:
            if isPoint4:
                btn4.config(text="Add Point?")
                ax2.clear()
                LpAll_ave_3_new = np.delete(LpAll_ave_3, 2,0)
                LpAll_ave_new = np.delete(LpAll_ave, 7, 0)
                if not isPoint3:
                    LpAll_ave_2_new = np.delete(LpAll_ave_2, 1,0)
                    LpAll_ave_newer = np.delete(LpAll_ave_new, 3, 0)
                    ax2.scatter(LpAll_ave_1[:,0]-offxD, LpAll_ave_1[:,1]-offyD);
                    ax2.scatter(LpAll_ave_2_new[:,0]-offxD, LpAll_ave_2_new[:,1]-offyD);
                    ax2.scatter(LpAll_ave_3_new[:,0]-offxD, LpAll_ave_3_new[:,1]-offyD);
                    ax2.plot(LpAll_ave_newer[:,0] - offxD, LpAll_ave_newer[:,0]*e + f - offyD, "r-" )
                    LPweight_new = np.array([0.5, 1, 0.5, 0.5, 1, 0.5])
                    m , b = np.polyfit(LpAll_ave_newer[:,0], LpAll_ave_newer[:,1], 1, w=LPweight_new)
                    ax2.plot(LpAll_ave_newer[:,0] - offxD, LpAll_ave_newer[:,0]*m + b - offyD, "g-")
                    passFail(LpAll_ave_newer[:,1] - LpAll_ave_newer[:,0]*e - f)
                    resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave_newer[:,1] - LpAll_ave_newer[:,0]*e - f),5)}")
                    resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave_newer[:,1] - LpAll_ave_newer[:,0]*e - f),5)}")
                else:
                    ax2.scatter(LpAll_ave_1[:,0]-offxD, LpAll_ave_1[:,1]-offyD);
                    ax2.scatter(LpAll_ave_2[:,0]-offxD, LpAll_ave_2[:,1]-offyD);
                    ax2.scatter(LpAll_ave_3_new[:,0]-offxD, LpAll_ave_3_new[:,1]-offyD);
                    ax2.plot(LpAll_ave_new[:,0] - offxD, LpAll_ave_new[:,0]*e + f - offyD, "r-" )
                    LPweight_new = np.array([0.5, 1, 0.5, 0.5, 0.5, 1, 0.5])
                    m , b = np.polyfit(LpAll_ave_new[:,0], LpAll_ave_new[:,1], 1, w=LPweight_new)
                    ax2.plot(LpAll_ave_new[:,0] - offxD, LpAll_ave_new[:,0]*m + b - offyD, "g-")
                    passFail(LpAll_ave_new[:,1] - LpAll_ave_new[:,0]*e - f)
                    resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave_new[:,1] - LpAll_ave_new[:,0]*e - f),5)}")
                    resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave_new[:,1] - LpAll_ave_new[:,0]*e - f),5)}")
                ax2.set_ylabel("Y position in mm")
                ax2.set_xlabel("X position in mm")
                ax2.set_title("Lockpoint positions of Stave " + staveType)              
                ax2.grid()
                canvas2.draw()
                isPoint4 = False
            else:
                btn4.config(text="Remove Point?")
                ax2.clear()
                if not isPoint3:
                    LpAll_ave_2_new = np.delete(LpAll_ave_2, 1,0)
                    LpAll_ave_newish = np.delete(LpAll_ave, 3, 0)
                    ax2.scatter(LpAll_ave_1[:,0]-offxD, LpAll_ave_1[:,1]-offyD);
                    ax2.scatter(LpAll_ave_2_new[:,0]-offxD, LpAll_ave_2_new[:,1]-offyD);
                    ax2.scatter(LpAll_ave_3[:,0]-offxD, LpAll_ave_3[:,1]-offyD);
                    ax2.plot(LpAll_ave_newish[:,0] - offxD, LpAll_ave_newish[:,0]*e + f - offyD, "r-" )
                    LPweight_new = np.array([0.5, 1, 0.5, 0.5, 1, 0.5, 0.5])
                    m , b = np.polyfit(LpAll_ave_newish[:,0], LpAll_ave_newish[:,1], 1, w=LPweight_new)
                    ax2.plot(LpAll_ave_newish[:,0] - offxD, LpAll_ave_newish[:,0]*m + b - offyD, "g-")
                    passFail(LpAll_ave_newish[:,1] - LpAll_ave_newish[:,0]*e - f)
                    resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave_newish[:,1] - LpAll_ave_newish[:,0]*e - f),5)}")
                    resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave_newish[:,1] - LpAll_ave_newish[:,0]*e - f),5)}")
                else:
                    ax2.scatter(LpAll_ave_1[:,0]-offxD, LpAll_ave_1[:,1]-offyD);
                    ax2.scatter(LpAll_ave_2[:,0]-offxD, LpAll_ave_2[:,1]-offyD);
                    ax2.scatter(LpAll_ave_3[:,0]-offxD, LpAll_ave_3[:,1]-offyD);
                    ax2.plot(LpAll_ave[:,0] - offxD, LpAll_ave[:,0]*e + f - offyD, "r-" )
                    passFail(LpAll_ave[:,1] - LpAll_ave[:,0]*e - f)
                    resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave[:,1] - LpAll_ave[:,0]*e - f),5)}")
                    resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave[:,1] - LpAll_ave[:,0]*e - f),5)}")
                ax2.set_ylabel("Y position in mm")
                ax2.set_xlabel("X position in mm")
                ax2.set_title("Lockpoint positions of Stave " + staveType)              
                ax2.grid()
                canvas2.draw()
                isPoint4 = True
    def point5():
        global isPoint5
        if (not isPoint0) or (not isPoint1) or (not isPoint2) or (not isPoint3) or (not isPoint4) or (not isPoint7):
            btn5.config(text="Remove Point?")
        else:
            ax2.clear()
            if isPoint5:
                btn5.config(text="Add Point?")
                LpAll_ave_2_new = np.delete(LpAll_ave_2, 0,0)
                LpAll_ave_new = np.delete(LpAll_ave, 2,0)
                if not isPoint6:
                    LpAll_ave_3_new = np.delete(LpAll_ave_3, 1, 0)
                    LpAll_ave_newer = np.delete(LpAll_ave_new, 5, 0)
                    ax2.scatter(LpAll_ave_1[:,0]-offxD, LpAll_ave_1[:,1]-offyD);
                    ax2.scatter(LpAll_ave_2_new[:,0]-offxD, LpAll_ave_2_new[:,1]-offyD);
                    ax2.scatter(LpAll_ave_3_new[:,0]-offxD, LpAll_ave_3_new[:,1]-offyD);
                    ax2.plot(LpAll_ave_newer[:,0] - offxD, LpAll_ave_newer[:,0]*e + f - offyD, "r-" )
                    LPweight_new = np.array([0.5, 1, 0.5, 0.5, 1, 0.5])
                    m , b = np.polyfit(LpAll_ave_newer[:,0], LpAll_ave_newer[:,1], 1, w=LPweight_new)
                    ax2.plot(LpAll_ave_newer[:,0] - offxD, LpAll_ave_newer[:,0]*m + b - offyD, "g-")
                    passFail(LpAll_ave_newer[:,1] - LpAll_ave_newer[:,0]*e - f)
                    resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave_newer[:,1] - LpAll_ave_newer[:,0]*e - f),5)}")
                    resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave_newer[:,1] - LpAll_ave_newer[:,0]*e - f),5)}")
                else:
                    ax2.scatter(LpAll_ave_1[:,0]-offxD, LpAll_ave_1[:,1]-offyD);
                    ax2.scatter(LpAll_ave_2_new[:,0]-offxD, LpAll_ave_2_new[:,1]-offyD);
                    ax2.scatter(LpAll_ave_3[:,0]-offxD, LpAll_ave_3[:,1]-offyD);
                    ax2.plot(LpAll_ave_new[:,0] - offxD, LpAll_ave_new[:,0]*e + f - offyD, "r-" )
                    LPweight_new = np.array([0.5, 1, 0.5, 0.5, 1, 0.5, 0.5])
                    m , b = np.polyfit(LpAll_ave_new[:,0], LpAll_ave_new[:,1], 1, w=LPweight_new)
                    ax2.plot(LpAll_ave_new[:,0] - offxD, LpAll_ave_new[:,0]*m + b - offyD, "g-")
                    passFail(LpAll_ave_new[:,1] - LpAll_ave_new[:,0]*e - f)
                    resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave_new[:,1] - LpAll_ave_new[:,0]*e - f),5)}")
                    resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave_new[:,1] - LpAll_ave_new[:,0]*e - f),5)}")
                ax2.set_ylabel("Y position in mm")
                ax2.set_xlabel("X position in mm")
                ax2.set_title("Lockpoint positions of Stave " + staveType)              
                ax2.grid()
                canvas2.draw()
                isPoint5 = False
            else:
                btn5.config(text="Remove Point?")
                if not isPoint6:
                    LpAll_ave_3_new = np.delete(LpAll_ave_3, 1, 0)
                    LpAll_ave_newish = np.delete(LpAll_ave, 6, 0)
                    ax2.scatter(LpAll_ave_1[:,0]-offxD, LpAll_ave_1[:,1]-offyD);
                    ax2.scatter(LpAll_ave_2[:,0]-offxD, LpAll_ave_2[:,1]-offyD);
                    ax2.scatter(LpAll_ave_3_new[:,0]-offxD, LpAll_ave_3_new[:,1]-offyD);
                    ax2.plot(LpAll_ave_newish[:,0] - offxD, LpAll_ave_newish[:,0]*e + f - offyD, "r-" )
                    LPweight_new = np.array([0.5, 1, 0.5, 0.5, 0.5, 1, 0.5])
                    m , b = np.polyfit(LpAll_ave_newish[:,0], LpAll_ave_newish[:,1], 1, w=LPweight_new)
                    ax2.plot(LpAll_ave_newish[:,0] - offxD, LpAll_ave_newish[:,0]*m + b - offyD, "g-")
                    passFail(LpAll_ave_newish[:,1] - LpAll_ave_newish[:,0]*e - f)
                    resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave_newish[:,1] - LpAll_ave_newish[:,0]*e - f),5)}")
                    resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave_newish[:,1] - LpAll_ave_newish[:,0]*e - f),5)}")
                else:
                    ax2.scatter(LpAll_ave_1[:,0]-offxD, LpAll_ave_1[:,1]-offyD);
                    ax2.scatter(LpAll_ave_2[:,0]-offxD, LpAll_ave_2[:,1]-offyD);
                    ax2.scatter(LpAll_ave_3[:,0]-offxD, LpAll_ave_3[:,1]-offyD);
                    ax2.plot(LpAll_ave[:,0] - offxD, LpAll_ave[:,0]*e + f - offyD, "r-" )
                    passFail(LpAll_ave[:,1] - LpAll_ave[:,0]*e - f)
                    resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave[:,1] - LpAll_ave[:,0]*e - f),5)}")
                    resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave[:,1] - LpAll_ave[:,0]*e - f),5)}")
                ax2.set_ylabel("Y position in mm")
                ax2.set_xlabel("X position in mm")
                ax2.set_title("Lockpoint positions of Stave " + staveType)              
                ax2.grid()
                canvas2.draw()
                isPoint5 = True
    def point6():
        global isPoint6
        if (not isPoint0) or (not isPoint1) or (not isPoint2) or (not isPoint3) or (not isPoint4) or (not isPoint7):
            btn6.config(text="Remove Point?")
        else:
            ax2.clear()
            if isPoint6:
                btn6.config(text="Add Point?")
                LpAll_ave_3_new = np.delete(LpAll_ave_3, 1, 0)
                LpAll_ave_new = np.delete(LpAll_ave, 6, 0)
                if not isPoint5:
                    LpAll_ave_2_new = np.delete(LpAll_ave_2, 0,0)
                    LpAll_ave_newer = np.delete(LpAll_ave_new, 2, 0)
                    ax2.scatter(LpAll_ave_1[:,0]-offxD, LpAll_ave_1[:,1]-offyD);
                    ax2.scatter(LpAll_ave_2_new[:,0]-offxD, LpAll_ave_2_new[:,1]-offyD);
                    ax2.scatter(LpAll_ave_3_new[:,0]-offxD, LpAll_ave_3_new[:,1]-offyD);
                    ax2.plot(LpAll_ave_newer[:,0] - offxD, LpAll_ave_newer[:,0]*e + f - offyD, "r-" )
                    LPweight_new = np.array([0.5, 1, 0.5, 0.5, 1, 0.5])
                    m , b = np.polyfit(LpAll_ave_newer[:,0], LpAll_ave_newer[:,1], 1, w=LPweight_new)
                    ax2.plot(LpAll_ave_newer[:,0] - offxD, LpAll_ave_newer[:,0]*m + b - offyD, "g-")
                    passFail(LpAll_ave_newer[:,1] - LpAll_ave_newer[:,0]*e - f)
                    resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave_newer[:,1] - LpAll_ave_newer[:,0]*e - f),5)}")
                    resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave_newer[:,1] - LpAll_ave_newer[:,0]*e - f),5)}")
                else:
                    ax2.scatter(LpAll_ave_1[:,0]-offxD, LpAll_ave_1[:,1]-offyD);
                    ax2.scatter(LpAll_ave_2[:,0]-offxD, LpAll_ave_2[:,1]-offyD);
                    ax2.scatter(LpAll_ave_3_new[:,0]-offxD, LpAll_ave_3_new[:,1]-offyD);
                    ax2.plot(LpAll_ave_new[:,0] - offxD, LpAll_ave_new[:,0]*e + f - offyD, "r-" )
                    LPweight_new = np.array([0.5, 1, 0.5, 0.5, 0.5, 1, 0.5])
                    m , b = np.polyfit(LpAll_ave_new[:,0], LpAll_ave_new[:,1], 1, w=LPweight_new)
                    ax2.plot(LpAll_ave_new[:,0] - offxD, LpAll_ave_new[:,0]*m + b - offyD, "g-")
                    passFail(LpAll_ave_new[:,1] - LpAll_ave_new[:,0]*e - f)
                    resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave_new[:,1] - LpAll_ave_new[:,0]*e - f),5)}")
                    resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave_new[:,1] - LpAll_ave_new[:,0]*e - f),5)}")
                ax2.set_ylabel("Y position in mm")
                ax2.set_xlabel("X position in mm")
                ax2.set_title("Lockpoint positions of Stave " + staveType)              
                ax2.grid()
                canvas2.draw()
                isPoint6 = False
            else:
                btn6.config(text="Remove Point?")
                if not isPoint5:
                    LpAll_ave_2_new = np.delete(LpAll_ave_2, 0,0)
                    LpAll_ave_newish = np.delete(LpAll_ave, 2, 0)
                    ax2.scatter(LpAll_ave_1[:,0]-offxD, LpAll_ave_1[:,1]-offyD);
                    ax2.scatter(LpAll_ave_2_new[:,0]-offxD, LpAll_ave_2_new[:,1]-offyD);
                    ax2.scatter(LpAll_ave_3[:,0]-offxD, LpAll_ave_3[:,1]-offyD);
                    ax2.plot(LpAll_ave_newish[:,0] - offxD, LpAll_ave_newish[:,0]*e + f - offyD, "r-" )
                    LPweight_new = np.array([0.5, 1, 0.5, 0.5, 1, 0.5, 0.5])
                    m , b = np.polyfit(LpAll_ave_newish[:,0], LpAll_ave_newish[:,1], 1, w=LPweight_new)
                    ax2.plot(LpAll_ave_newish[:,0] - offxD, LpAll_ave_newish[:,0]*m + b - offyD, "g-")
                    passFail(LpAll_ave_newish[:,1] - LpAll_ave_newish[:,0]*e - f)
                    resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave_newish[:,1] - LpAll_ave_newish[:,0]*e - f),5)}")
                    resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave_newish[:,1] - LpAll_ave_newish[:,0]*e - f),5)}")
                else:
                    ax2.scatter(LpAll_ave_1[:,0]-offxD, LpAll_ave_1[:,1]-offyD);
                    ax2.scatter(LpAll_ave_2[:,0]-offxD, LpAll_ave_2[:,1]-offyD);
                    ax2.scatter(LpAll_ave_3[:,0]-offxD, LpAll_ave_3[:,1]-offyD);
                    ax2.plot(LpAll_ave[:,0] - offxD, LpAll_ave[:,0]*e + f - offyD, "r-" )
                    passFail(LpAll_ave[:,1] - LpAll_ave[:,0]*e - f)
                    resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave[:,1] - LpAll_ave[:,0]*e - f),5)}")
                    resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave[:,1] - LpAll_ave[:,0]*e - f),5)}")
                ax2.set_ylabel("Y position in mm")
                ax2.set_xlabel("X position in mm")
                ax2.set_title("Lockpoint positions of Stave " + staveType)              
                ax2.grid()
                canvas2.draw()
                isPoint6 = True
    def point7():
        global isPoint7
        if (not isPoint1) or (not isPoint2) or (not isPoint3) or (not isPoint4) or (not isPoint5) or (not isPoint6) or (not isPoint0):
            btn7.config(text="Remove Point?")
        else:
            if isPoint7:
                btn7.config(text="Add Point?")            
                LpAll_ave_3_new = np.delete(LpAll_ave_3, 0, 0)
                LpAll_ave_new= np.delete(LpAll_ave, 5, 0)
                ax2.clear()
                ax2.scatter(LpAll_ave_1[:,0]-offxD, LpAll_ave_1[:,1]-offyD);
                ax2.scatter(LpAll_ave_2[:,0]-offxD, LpAll_ave_2[:,1]-offyD);
                ax2.scatter(LpAll_ave_3_new[:,0]-offxD, LpAll_ave_3_new[:,1]-offyD);
                ax2.plot(LpAll_ave_new[:,0] - offxD, LpAll_ave_new[:,0]*e + f - offyD, "r-" )
                LPweight_new = np.array([0.5, 1, 0.5, 0.5, 0.5, 0.5, 0.5])
                m , b = np.polyfit(LpAll_ave_new[:,0], LpAll_ave_new[:,1], 1, w=LPweight_new)
                ax2.plot(LpAll_ave_new[:,0] - offxD, LpAll_ave_new[:,0]*m + b - offyD, "g-")
                ax2.set_ylabel("Y position in mm")
                ax2.set_xlabel("X position in mm")
                ax2.set_title("Lockpoint positions of Stave " + staveType)
                ax2.grid()
                canvas2.draw()
                passFail(LpAll_ave_new[:,1] - LpAll_ave_new[:,0]*e - f)
                resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave_new[:,1] - LpAll_ave_new[:,0]*e - f),5)}")
                resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave_new[:,1] - LpAll_ave_new[:,0]*e - f),5)}")
                isPoint7 = False
            else:
                btn7.config(text="Remove Point?")
                ax2.clear()
                ax2.scatter(LpAll_ave_1[:,0]-offxD, LpAll_ave_1[:,1]-offyD);
                ax2.scatter(LpAll_ave_2[:,0]-offxD, LpAll_ave_2[:,1]-offyD);
                ax2.scatter(LpAll_ave_3[:,0]-offxD, LpAll_ave_3[:,1]-offyD);
                ax2.plot(LpAll_ave[:,0] - offxD, LpAll_ave[:,0]*e + f - offyD, "r-" )
                ax2.set_ylabel("Y position in mm")
                ax2.set_xlabel("X position in mm")
                ax2.set_title("Lockpoint positions of Stave " + staveType)
                ax2.grid()
                canvas2.draw()
                passFail(LpAll_ave[:,1] - LpAll_ave[:,0]*e - f)
                resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave[:,1] - LpAll_ave[:,0]*e - f),5)}")
                resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave[:,1] - LpAll_ave[:,0]*e - f),5)}")
                isPoint7 = True
    
    btn0.config(command=point0)
    btn1.config(command=point1)
    btn2.config(command=point2)
    btn3.config(command=point3)
    btn4.config(command=point4)
    btn5.config(command=point5)
    btn6.config(command=point6)
    btn7.config(command=point7)
    

    resMax_lbl.config(text="Max Residual Value (in mm): " + f"{round(np.max(LpAll_ave[:,1] - LpAll_ave[:,0]*e - f),5)}")
    resMin_lbl.config(text="Min Residual Value (in mm): " + f"{round(np.min(LpAll_ave[:,1] - LpAll_ave[:,0]*e - f),5)}")
    lpFidMax_lbl.config(text="Max distance from LP to Fiducial Regression (in mm): " + f"{round(RotatedLpAll[15,0]*e + f - offyD,5)}")
    lpFidMin_lbl.config(text="Min distance from LP to Fiducial Regression (in mm): " + f"{round(RotatedLpAll[0,0]*e + f - offyD,5)}")
    
    ax.clear()
    ax.scatter(LpAll_ave_1[:,0]-offxD, LpAll_ave_1[:,1] - LpAll_ave_1[:,0]*e - f)
    ax.scatter(LpAll_ave_2[:,0]-offxD, LpAll_ave_2[:,1] - LpAll_ave_2[:,0]*e - f)
    ax.scatter(LpAll_ave_3[:,0]-offxD, LpAll_ave_3[:,1] - LpAll_ave_3[:,0]*e - f)
    ax.set_ylabel("Y position in mm")
    ax.set_xlabel("X position in mm")
    ax.set_title("Residuals in Lockpoint positions of Stave " + staveType)
    ax.axhline(y=0, color = "r", linestyle="-" )
    ax.grid()
    canvas.draw()
    fig.savefig(folder_selected + "\\Stave" +staveType +"_Test Results\\"+"Locking Point Residuals_"+ staveType+".png")

    passFail(LpAll_ave[:,1] - LpAll_ave[:,0]*e - f)
    
    

    xColumn = tableLpx-offxD
    yColumn = tableLpy-offyD

    for i in range(8):
        xColumn[i]=round(xColumn[i],5)
        yColumn[i]=round(yColumn[i],5)

    #saveTable = np.stack((xColumn,yColumn), axis=-1)

    resList = np.array([tableLpy[:]-tableLpx[:]*e - f]).flatten()
    resList1 = np.round(resList, 5)
    df = pd.DataFrame({"Locking Point X (mm)": xColumn, "Locking Point Y (mm)": yColumn, "Residuals for Stave " + staveType: resList1})
    df.to_csv(folder_selected + "\\Stave" +staveType +"_Test Results\\"+"LockingPoints_"+ staveType+".csv", index=False)

btnFrame = tk.Frame(master=window)
btnFrame.pack()
run_btn = tk.Button(master=btnFrame, text="Run Analysis", command=runScript, font=18)
run_btn.grid(row=0,column=0)
test_lbl = tk.Label(master=btnFrame, text="Result", bg="yellow", font=18)
test_lbl.grid(row=0,column=1, padx=40, sticky="nsew")

graphMaster = tk.Frame(master=window)
graphMaster.pack()

graphFrame = tk.Frame(master=graphMaster)
graphFrame.grid(row=0,column=0,sticky="nw")

graphFrame2 = tk.Frame(master=graphMaster)
graphFrame2.grid(row=0,column=1,sticky="ne")


fig = matplotlib.figure.Figure(figsize=(6.5,4))
ax = fig.add_subplot()

canvas = FigureCanvasTkAgg(fig, master=graphFrame)
canvas.get_tk_widget().grid(row=0, column=0,sticky="w", padx=10)
toolbar = NavigationToolbar2Tk(canvas, graphFrame, pack_toolbar = False)
toolbar.update()
toolbar.grid(row=1,column=0, sticky="w")

fig2 = matplotlib.figure.Figure(figsize=(6.5,4))
ax2 = fig2.add_subplot()

canvas2 = FigureCanvasTkAgg(fig2, master=graphFrame)
canvas2.get_tk_widget().grid(row=2, column=0, padx=10)
toolbar2 = NavigationToolbar2Tk(canvas2, graphFrame, pack_toolbar = False)
toolbar2.update()
toolbar2.grid(row=3, column = 0, sticky="w")

fig3 = matplotlib.figure.Figure(figsize=(10,5))
ax3 = fig3.add_subplot()

canvas3 = FigureCanvasTkAgg(fig3, master=graphFrame2)
canvas3.get_tk_widget().grid(row=0, column=0, padx=10)
toolbar3 = NavigationToolbar2Tk(canvas3, graphFrame2, pack_toolbar = False)
toolbar3.update()
toolbar3.grid(row=1,column=0, sticky="w")

tableFrame = tk.Frame(master=graphFrame2)
tableFrame.grid(row=2, column=0,sticky="w")

x_lbl = tk.Label(master=tableFrame, text="X value in mm", font=18)
x_lbl.grid(row=0,column=0)

y_lbl = tk.Label(master=tableFrame, text="Y value in mm", font=18)
y_lbl.grid(row=0, column=1)

x0 = tk.Label(master=tableFrame, text=f"0", font= 18)
x0.grid(row=1, column=0)    
x1 = tk.Label(master=tableFrame, text=f"0", font= 18)
x1.grid(row=2, column=0)
x2 = tk.Label(master=tableFrame, text=f"0", font= 18)
x2.grid(row=3, column=0)
x3 = tk.Label(master=tableFrame, text=f"0", font= 18)
x3.grid(row=4, column=0)
x4 = tk.Label(master=tableFrame, text=f"0", font= 18)
x4.grid(row=5, column=0)
x5 = tk.Label(master=tableFrame, text=f"0", font= 18)
x5.grid(row=6, column=0)
x6 = tk.Label(master=tableFrame, text=f"0", font= 18)
x6.grid(row=7, column=0)
x7 = tk.Label(master=tableFrame, text=f"0", font= 18)
x7.grid(row=8, column=0)
   
y0 = tk.Label(master=tableFrame, text=f"0", font= 18)
y0.grid(row=1, column=1)
y1 = tk.Label(master=tableFrame, text=f"0", font= 18)
y1.grid(row=2, column=1)
y2 = tk.Label(master=tableFrame, text=f"0", font= 18)
y2.grid(row=3, column=1)
y3 = tk.Label(master=tableFrame, text=f"0", font= 18)
y3.grid(row=4, column=1)
y4 = tk.Label(master=tableFrame, text=f"0", font= 18)
y4.grid(row=5, column=1)
y5 = tk.Label(master=tableFrame, text=f"0", font= 18)
y5.grid(row=6, column=1)
y6 = tk.Label(master=tableFrame, text=f"0", font= 18)
y6.grid(row=7, column=1)
y7 = tk.Label(master=tableFrame, text=f"0", font= 18)
y7.grid(row=8, column=1)

btn0 = tk.Button(master=tableFrame, text="Remove Point?", bg="#F55447")
btn0.grid(row=1,column=2)
btn1 = tk.Button(master=tableFrame, text="Remove Point?", bg="orange")
btn1.grid(row=2,column=2)
btn2 = tk.Button(master=tableFrame, text="Remove Point?", bg="orange")
btn2.grid(row=3,column=2)
btn3 = tk.Button(master=tableFrame, text="Remove Point?", bg="yellow")
btn3.grid(row=4,column=2)
btn4 = tk.Button(master=tableFrame, text="Remove Point?", bg="yellow")
btn4.grid(row=5,column=2)
btn5 = tk.Button(master=tableFrame, text="Remove Point?", bg="#50F97C")
btn5.grid(row=6,column=2)
btn6 = tk.Button(master=tableFrame, text="Remove Point?", bg="#50F97C")
btn6.grid(row=7,column=2)
btn7 = tk.Button(master=tableFrame, text="Remove Point?", bg="#7ED2F6")
btn7.grid(row=8,column=2)

resMax_lbl = tk.Label(master=tableFrame, text="Max Residual Value (in mm): ",font=18)
resMax_lbl.grid(row=1, column=3, padx=40)
resMin_lbl = tk.Label(master=tableFrame, text="Min Residual Value (in mm): ",font=18)
resMin_lbl.grid(row=2, column=3, padx=40)
lpFidMax_lbl = tk.Label(master=tableFrame, text="Max distance from LP to Fiducial Regression (in mm): ", font=18)
lpFidMax_lbl.grid(row=3, column=3, padx=40)
lpFidMin_lbl = tk.Label(master=tableFrame, text="Min distance from LP to Fiducial Regression (in mm): ", font=18)
lpFidMin_lbl.grid(row=4, column=3, padx=40)


compValue = 13.891
#Add linear fit on removing graph, save locking points as text file
window.mainloop()