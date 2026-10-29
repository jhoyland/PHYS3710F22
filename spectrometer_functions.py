# Find the slit. This function finds the location of the slit in the photograph of the spectrum
# The function takes a single line of the data and scans it to find the maximum value.
# If it finds a block of saturated pixels it finds the middle pixel to be the slit.
# The function returns the column number of the slit.

import math

def find_slit(data):
    
    mx = 0
    mxc = 0
    
    startslit = 0
    endslit = 0
    
    for c,d in enumerate(data):
        
        if d > mx:
            
            mx = d
            mxc = c
            
        if startslit == 0 and d >= 255:
            
            startslit = c
            
        if endslit == 0 and startslit > 0 and d < 254:
            
            endslit = c
            break
            
    # We found a slit of saturated values
    if startslit > 0 and endslit > startslit:
        
        return math.ceil(0.5 * (endslit - startslit) + startslit)
    
    # Or just return the location of the biggest value found
    else:
        
        return mxc

    # Reads in the data along with the grating pitch (g in lines/mm) and resolution in radians per pixel

def get_spectrum(data,g,res):
    
    s = find_slit(data)
    
    d2 = data[s::-1]

    d = 0.001 / g # convert lines/mm into grating spacing in m
    
    wvl = [ 1e9* d * math.sin(i * res) for i in range(len(d2))]
        
    return (wvl,d2)