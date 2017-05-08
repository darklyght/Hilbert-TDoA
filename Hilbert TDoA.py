#!/usr/bin/env python
import os
import subprocess
import time
import numpy as np
import scipy.signal as sig
import scipy.fftpack as fft

def get_direction():
    directions = []
    path = '/home/'
    subprocess.call(["bash", "getData.sh"]) # Run bash file on Raspberry Pi to get data
    time.sleep(1)
    for i in range(1,4):
        newest = path + str(i) + '0.csv'
        
        ##### Parameters #####
        SamplingRate = 200000. # Sampling rate (include decimal place)
        BandpassLow = 20000 # Lower limit of Butterworth bandpass filter
        BandpassHigh = 30000 # Upper limit of Butterworth bandpass filter
        BandpassOrder = 10 # Filter order
        Threshold = 750 # Hilbert transform threshold
        Speed = 1484.0 # Speed of wave in medium
        x_max = 10. # Maximum x range
        x_diff  = 0.1 # Precision of x range
        y_max = 10. # Maximum y range
        y_diff = 0.1 # Precision of y range
        z_max = 5. # Maximum z range
        z_diff = 0.1 # Precision of z range
        Hydrophones = np.array([[0.15, 0.18, 0.], [-0.15, 0.18, 0.], [0., 0., 0.]]) # Array configuration [x1, y1, z1], [x2, y2, z2]...
        
        ##### Initial sample test #####
        y = np.transpose(np.genfromtxt(newest, delimiter = ',', skip_header = 0, max_rows = 256, usecols=(1, 2, 3)))
        y = y - np.mean(y)
        FFT_test = np.abs(fft.fft(y))
        freqs_test = np.fft.fftfreq(FFT_test[0].size, d=1/SamplingRate)
        index = np.where(freqs_test >= 25000)[0][0]
        
        ##### Get Sample Difference #####
        if (FFT_test[0][index-1] < 20000):
            # Extract data from relevant channels and remove DC component
            x = np.transpose(np.genfromtxt(newest, delimiter = ',', skip_header = 0, max_rows = 2048, usecols=(1, 2, 3)))
            x = x - np.mean(x)
            
            # Filter sample
            nyq = 0.5 * (SamplingRate)
            low = BandpassLow / nyq
            high = BandpassHigh / nyq
            #b,a = sig.butter(BandpassOrder, [low, high], 'bandpass') # Butterworth filter
            #b,a = sig.ellip(7, 3, 40, [low, high], 'bandpass') # Elliptic filter
            b,a = sig.bessel(5, [low, high], 'bandpass') # Bessel filter
            x[0] = sig.lfilter(b,a,x[0])
            x[1] = sig.lfilter(b,a,x[1])
            x[2] = sig.lfilter(b,a,x[2])
            
            # Hilbert transform
            x[0] = np.abs(sig.hilbert(x[0]))
            x[1] = np.abs(sig.hilbert(x[1]))
            x[2] = np.abs(sig.hilbert(x[2]))
            
            # Get first point above threshold ignoring initial and final instability
            index0 = np.where(x[0][100:1900] > Threshold)[0][0]
            index1 = np.where(x[1][100:1900] > Threshold)[0][0]
            index2 = np.where(x[2][100:1900] > Threshold)[0][0]
            
            ##### Get TDoA #####
            # Generate coordinates
            x_range = np.arange(-x_max, x_max + x_diff, x_diff)
            y_range = np.arange(-y_max, y_max + y_diff, y_diff)
            z_range = np.arange(-z_max, z_max + z_diff, z_diff)
            
            # Generate coordinate system
            x, y, z = np.meshgrid(x_range, y_range, z_range)
            
            # Calculate distance from each point in coordinate system to hydrophones
            dist1 = np.zeros(x.shape)
            dist1 = np.sqrt(np.square(x-Hydrophones[0][0]) + np.square(y-Hydrophones[0][1]) + np.square(z-Hydrophones[0][2]))
            dist2 = np.zeros(x.shape)
            dist2 = np.sqrt(np.square(x-Hydrophones[1][0]) + np.square(y-Hydrophones[1][1]) + np.square(z-Hydrophones[1][2]))
            dist3 = np.zeros(x.shape)
            dist3 = np.sqrt(np.square(x-Hydrophones[2][0]) + np.square(y-Hydrophones[2][1]) + np.square(z-Hydrophones[2][2]))
            
            # Calculate time difference of each point in array to each pair of hydrophones
            time_diff1 = (dist2 - dist1) / Speed
            time_diff2 = (dist3 - dist1) / Speed
            
            ##### Calculate DoA using TDoA #####
            # Time difference
            index = [index0, index1, index2]
            diff1 = (index[1] - index[0]) * 1/SamplingRate
            diff2 = (index[2] - index[0]) * 1/SamplingRate
            
            # Calculate difference coefficient
            diff_coeff = np.absolute(time_diff1 - diff1) + np.absolute(time_diff2 - diff2)
            
            # Use 1-dimension for azimuth only
            coeff_1d = diff_coeff[:, :, 0]
            
            # Get index of minima
            P, Q = np.unravel_index(coeff_1d.argmin(), coeff_1d.shape)
            
            # Append direction to array for mean calculation
            directions.append(-(np.arctan2(y_range[Q], x_range[P]) * 180/np.pi - 90))
            
            # Remove file
            subprocess.call(["rm", newest])
    
    ##### Write mean of directions to file #####        
    with open('direction.txt', 'w') as f:
        f.write(str(-(np.mean(directions)-90)))
        
if __name__ == '__main__':
    get_direction()