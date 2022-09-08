# -*- coding: utf-8 -*-
"""
Created on Sun Jul 19 17:51:22 2020

@author: James Hoyland

LabTrinket:
    
This class encapsulates serial communications with the Trinket M0 running the lab trinket python code.

Through this interface you can set LED color and brightness, get ADC values and control the PWM and true analog output on the board.


"""


import serial
import time

class LabTrinket:
    
    #Command strings for Trinket M0
    
    cmdADCDelay     = "adc@delay={:.4f}\r"
    cmdADCVolts     = "adc@mode={}\r"
    cmdADCNow       = "adc!\r"
    cmdADCRun       = "adc@run\r"
    cmdADCStop      = "adc@stop\r"
    
    cmdDACOn        = "dac@on\r"
    cmdDACOff       = "dac@off\r"
    cmdDACLevel     = "dac@level={:}\r"
    
    cmdLEDcolor     = "led#{:02X}{:02X}{:02X}\r"
    cmdLEDbright    = "led%{:}\r"
    cmdLEDoff       = "led%0\r"
    
    maxVolts = 3.3
    
    def __init__(self,connection):
        self.connection = connection
        self.value = 0 #stores latest value from the ADC
        self.dly = 1 #delay in seconds between ADC measurements when free running
        self.volts = False  #by default 
        #Some default settings for LED so ledOn does something if used right away
        self.red = 128
        self.green = 0
        self.blue = 0
        self.brightness = 100
     
    
    #requests a single ADC value. This does not return the actual value

    #Note: unless adcWriteOptions is called first the ADC settings will be as currently set on the board
    #not necessarily the values stored in the LabTrinket instance. If the Trinket has been set into free running mode
    #using adcRun then this has already been done
        
    def adcRequestValue(self):
        self.connection.write(LabTrinket.cmdADCNow.encode())

    #Checks to see if the trinket has sent any values
        
    def adcValueReady(self):
        return self.connection.in_waiting > 0

    #Gets the actual value. Will try a set number of times to retrieve a value from the serial buffer. Returns true if a 
    #value was successfully retrieved. The retrieved value is placed in the instance variable 'value'
    
    # CircuitPython's "input" method echoes the serial sent to the board. 
    # So we have to strip out these echoes from the response
    # Correct board response begins with '>'
    
    def adcGetValue(self,tries=50):
        success = False
        while self.adcValueReady() and not success and tries>0:
            response = self.connection.readline()
            responseText = response.decode('ascii')
            if responseText[0] == '>':
                if responseText[1] == 'i':
                    self.value = int(responseText[2:])
                    success = True
                elif responseText[1] == 'v':
                    self.value = float(responseText[2:])
                    success = True
            tries = tries - 1
                    
        return success

    # Writes the current ADC options to the trinket
    
    def adcWriteOptions(self):
        
        self.connection.write((LabTrinket.cmdADCDelay.format(self.dly)).encode())
        if self.volts:
            self.connection.write((LabTrinket.cmdADCVolts.format("volts")).encode())
        else:
            self.connection.write((LabTrinket.cmdADCVolts.format("raw")).encode())
            
    # Sets the ADC into free running mode. The trinket will send ADC values at the interval determined by self.dly

    def adcRun(self):
        self.adcWriteOptions()
        self.connection.write(LabTrinket.cmdADCRun.encode())
        self.connection.reset_input_buffer()

    # Stop ADC
        
    def adcStop(self):
        self.connection.write(LabTrinket.cmdADCStop.encode())
        
    #adcVoltMode: Sets the Trinket ADC to "volt" mode. In this case ADC values are converted to actual voltages and 
    #sent as a floating point number. Otherwise the ADC returns the raw ADC integer (12-bit value) 
    
    def adcVoltMode(self,mode=True):
        self.volts = mode
        if self.volts:
            self.connection.write((LabTrinket.cmdADCVolts.format("volts")).encode())
        else:
            self.connection.write((LabTrinket.cmdADCVolts.format("raw")).encode())

    # Set the delay for ADC measurements
            
    def adcDelay(self,delay=1):
        self.dly = delay
        self.connection.write((LabTrinket.cmdADCDelay.format(self.dly)).encode())   
        
    def adcAveragedValue(self,n):
        
        accumulated = 0
        
        self.adcRun()
        
        i = 0
        
        while i<n:
            
            if self.adcGetValue():
                
                accumulated += self.value
                i = i + 1
            
        self.adcStop()
            
        return accumulated / n
        
    # Turn on the DAC
        
    def dacOn(self):
        self.connection.write(LabTrinket.cmdDACOn.encode())

    # Turn off the DAC
        
    def dacOff(self):
        self.connection.write(LabTrinket.cmdDACOff.encode())

    # Set the DAC level. Does not turn the DAC on if it is off. Does not check for valid level right now so be careful!
        
    def dacLevel(self,level):
        self.connection.write((LabTrinket.cmdDACLevel.format(level)).encode())
        
    # Set the DAC voltage. 

    def dacVolts(self,volts):
        if volts > LabTrinket.maxVolts:
            volts = LabTrinket.maxVolts
        if volts < 0:
            volts = 0
            
        level = int(65536 * volts / LabTrinket.maxVolts)
        
        self.dacLevel(level)
        
    
    #Set RGB values for NeoStar LED, ignores values which are out of range. Only changes
    #The values requested, e.g. can change red without changing other values.
    
    def ledSetColor(self,red=-1, green = -1, blue = -1, writeToTrinket = True):
        if red >= 0 and red < 256:
            self.red = red
        if green >= 0 and green < 256:
            self.green = green
        if blue >= 0 and blue < 256:
            self.blue = blue
            
        if writeToTrinket:
            self.connection.write((LabTrinket.cmdLEDcolor.format(self.red,self.green,self.blue)).encode())
        
    #Set brightness. Sets overall brightness.

    def ledSetBrightness(self, brightness = -1, writeToTrinket = True):
        
        if brightness >= 0 and brightness <= 100:
            self.brightness = brightness
        
        if writeToTrinket:
            self.connection.write((LabTrinket.cmdLEDbright.format(self.brightness)).encode())

    # Turns on the LED with the last saved color
        
    def ledOn(self):
        self.ledSetBrightness()
        self.ledSetColor()
        
    # Turns off the LED

    def ledOff(self):
        self.connection.write(LabTrinket.cmdLEDoff.encode())
    

# Use case example
    
if __name__ == "__main__":
    
    # Setup serial connection

    serconn = serial.Serial()
    serconn.port = 'COM17'
    serconn.baudrate = 9600
    serconn.open()
    
    # Create LabTrinet object
    
    trinket = LabTrinket(serconn)
    
    i = 0
    
    # Set ADC to volt mode with 0.5s delay
    
    trinket.volts = True
    trinket.delay = 0.5
    
    # Set onboard LED color and brightness
    
    trinket.red = 250
    trinket.green = 12
    trinket.blue = 112
    
    trinket.brightness = 75
    
    trinket.ledOn()
    
    # Put ADC into free-running mode
    
    trinket.adcRun()
    
    # Get 50 ADC values while modifying the LED color
    
    while i<50:
        if trinket.adcGetValue():
            print("{}: {}".format(i,trinket.value))
            i = i+1
            trinket.green += 2
            trinket.red -= 4
            trinket.ledSetColor()
    
    
    print("Done")
    
    # Clean up and close the connection
    
    trinket.adcStop()
    
    trinket.ledOff()
    
    serconn.close()

        
        
        
        
        
        

