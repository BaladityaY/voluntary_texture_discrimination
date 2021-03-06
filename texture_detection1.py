import numpy as np 
from numpy.random import random, shuffle, randn
from tools import *
from psychopy import visual, core, misc, event
import psychopy.monitors.calibTools as calib
import matplotlib.pyplot as plt
from scipy.optimize import leastsq
import analyze_run as analysis
import sys

def wait_for_key():
    response = False
    while not response:
        for key in event.getKeys():
            if key in ['escape','q']:
                core.quit()
            else:
                response = True
    
if __name__ == "__main__":
    
    win = visual.Window([1024,768], monitor='testMonitor', units='deg',color = 'gray') 
    
    p = Params()
    app = wx.App()
    app.MainLoop()
    
    #p.set_by_gui()
    
    #automatic parameters for quick testing
    p.subject='test'
    p.demo=False
    p.texture_dur = .150
    

    calib.monitorFolder = './calibration/'# over-ride the usual setting of where
                                      # monitors are stored

    mon = calib.Monitor(p.monitor) #Get the monitor object and pass that as an
                                   #argument to win:
                                   
    
    #win = visual.Window(monitor=mon,units='deg',screen=p.screen_number,
      #             fullscr=p.full_screen)
    
    f = start_data_file(p.subject)
    p.save(f)
    
    f = save_data(f,'trial','target_ecc','correct','odd_first','neutral','rt')
    size = p.elems_per_row * p.elem_spacing
    pre_x = np.linspace(-size/2., size/2., p.elems_per_row) 
    pre_y = np.linspace(-p.elem_spacing, p.elem_spacing, 3) 

    xx,yy = np.meshgrid(pre_x,pre_y)

    x = np.ravel(xx)
    y = np.ravel(yy)
    xys=np.vstack([x,y]).T
    target_xys = xys[p.elems_per_row+1:p.elems_per_row*2-1]

    pi = np.pi 
    X, Y = np.mgrid[0:2*pi:2*pi/p.res, 0:2*pi:2*pi/p.res]

    gabor = np.sin(p.sf*(Y-pi/2))

    ea = visual.ElementArrayStim(win,
                                 nElements=p.elems_per_row*3,
                                 sizes=p.elem_size,
                                 fieldSize=size,
                                 xys=xys,
                                 elementTex=gabor
                                 )

    # Make two masks, one in each orientation (+/- 45 degrees), with 0.5
    # opacity, so they can mix when shown on top of each other:

    mask_tex = np.sin(5*(Y-pi/2))+np.sin(5*(X-pi/2))
    mask_tex /= np.max(mask_tex)
    
    mask = visual.ElementArrayStim(win,
                                   nElements=p.elems_per_row*3,
                                   sizes=p.elem_size,
                                   fieldSize=size,
                                   xys=xys,
                                   oris=45,
                                   elementTex=mask_tex
                                   )

    fixation = visual.PatchStim(win,
                                tex=None,
                                mask = 'circle',
                                color=-1*p.rgb,
                                size=p.fixation_size,
                                )
    
    Text(win)()
    fixation.draw()
    win.flip()
    clock = core.Clock()

    # Psuedo-randomly choose the odd element location for each trial: 
    trial_odds = np.mod(np.random.permutation(p.n_trials),p.elems_per_row-2)
    trial_foils = np.mod(np.random.permutation(p.n_trials),p.elems_per_row-2) 
    for trial in xrange(p.n_trials):
        clock.reset()
        # Randomly choose the odd element and the foil location for this trial:
        this_odd = trial_odds[trial] 
        this_foil = trial_foils[trial]
        # Whether this is a neutral cue trial: 
        neutral_cue = np.random.randn() > 0
        # Whether the odd element is first or second: 
        odd_first = np.random.randn() > 0

        # This determines the cue size and location:
        if neutral_cue:
            cue1_vertices = cue2_vertices = [[size/2, p.cue_size[1]],
                                             [-size/2, p.cue_size[1]]] 

            cue1_location1 = cue2_location1 = [0, 0]
            cue1_location2 = cue2_location2 = [0, -4*p.elem_spacing]
            cue1 = [visual.ShapeStim(win, 
                                lineColor='green',
                                lineWidth=p.line_width,
                                fillColor=None,
                                vertices=cue1_vertices,
                                closeShape=True,
                                pos=cue1_location1,
                                interpolate=True,
                                opacity=1),
                visual.ShapeStim(win, 
                                lineColor='green',
                                lineWidth=p.line_width,
                                fillColor=None,
                                vertices=cue1_vertices,
                                closeShape=True,
                                pos=cue1_location2,
                                interpolate=True,
                                opacity=1)]
    
            cue2 = [visual.ShapeStim(win, 
                                lineColor='green',
                                lineWidth=p.line_width,
                                fillColor=None,
                                vertices=cue2_vertices,
                                closeShape=True,
                                pos=cue2_location1,
                                interpolate=True,
                                opacity=1),
                visual.ShapeStim(win, 
                                lineColor='green',
                                lineWidth=p.line_width,
                                fillColor=None,
                                vertices=cue2_vertices,
                                closeShape=True,
                                pos=cue2_location2,
                                interpolate=True,
                                opacity=1)]
        else:
            cue1_vertices = cue2_vertices = [[p.cue_size[0]/2., p.cue_size[1]],
                                             [-1 * p.cue_size[0]/2., p.cue_size[1]]]


            cue1_location1 = cue1_location2 = [0,0]
            cue2_location1 = cue2_location2 = [0,0]
            
            if this_odd < 14:
                cuetext = "- "+str(14-this_odd)
            else:
                cuetext = str(this_odd-14)+" -"
            
            cue1 = [visual.TextStim(win,text=cuetext, pos=cue1_location1),
                                visual.TextStim(win,text=cuetext,opacity=0)]
            cue2 = [visual.TextStim(win,text=cuetext, pos=cue1_location1),
                                visual.TextStim(win,text=cuetext,opacity=0)]

        # Record the eccentricity of the odd element and of the foil cue:
        odd_ecc = np.sqrt(target_xys[this_odd][0]**2+target_xys[this_odd][1]**2)
        foil_ecc = np.sqrt(target_xys[this_foil][0]**2+target_xys[this_foil][1]**2)

        # Make some arrays that will contain different content for every run
        # through the stimulus sequence:
        cues = [cue1,cue2]
        odd = [odd_first,not odd_first]
        wait = [p.middle_fix_dur,0]

        # Loop over for the two intervals:
        for i,cue in enumerate(cues): 
            if neutral_cue:
            # Draw in the fixation if neutral cue
                fixation.draw()

            # Draw both parts of this cue:
            for c in cue: c.draw()
            win.flip()

            if p.demo: wait_for_key()

            # Wait for the duration of the cue and draw in only the fixation
            core.wait(p.cue_dur)
            if neutral_cue:
                fixation.draw()
            win.flip()

            if p.demo: wait_for_key()

            # Random orientation for the background:
            bkgrnd_orient = np.sign(np.random.randn()) * 45
            ea.setOris(bkgrnd_orient)

            # Change the orientation of the odd element if needed:
            if odd[i]:
                ea.oris[this_odd+p.elems_per_row+1] = bkgrnd_orient + 90 


            # Jitter spatial location of the elements in the array:
            ea.xys = xys + p.jitter * randn(ea.xys.shape[0],ea.xys.shape[1])
            
            if neutral_cue:
                fixation.draw()
            ea.draw()
            # Wait for the isi before flipping in the fixation + ea:
            core.wait(p.cue_to_ea)
            win.flip()

            if p.demo: wait_for_key()

            # Mask elements should have the same spatial location as the
            # texture elements: 
            mask.xys = ea.xys
            
            fixation.draw()
            mask.draw()
            core.wait(p.texture_dur)
            win.flip()

            if p.demo: wait_for_key()

            core.wait(p.mask_dur)
            fixation.draw()
            win.flip()

            if p.demo: wait_for_key()

            # Wait at the end for the  
            core.wait(wait[i])
        
        if odd_first:
            correct_ans = ['num_1','1']             
        else:
            correct_ans = ['num_2','2']
            
        response = False
        while not response:
            for key in event.getKeys():
                if key in ['escape','q']:
                    f.close()
                    win.close()
                    core.quit()
                elif key in ['1','2','num_1','num_2']:
                    if key in correct_ans:
                        p.correct_sound.play()
                        correct = 1
                        response = True
                        rt = clock.getTime()
                    else:
                        p.incorrect_sound.play()
                        correct = 0
                        response = True
                        rt = clock.getTime()

        core.wait(p.iti)
        event.clearEvents()  # keep the event buffer from overflowing
        f = save_data(f,trial,odd_ecc,correct,int(odd_first),int(neutral_cue),rt)

    win.close()
    f.close()
    
    if not p.demo:
        # Get rid of the dot and the slash in the beginning of the file-name:
        file_name = f.name[2:]
        # Run the analysis on the file, with file-name given:
        analysis.main(file_name)
        
