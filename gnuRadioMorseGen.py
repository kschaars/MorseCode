#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 MIT Haystack.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Author: Kevin Schaars
# This code is to generate a OOK Morse code signal at a desired frequency 
import numpy as np
from gnuradio import gr
import time

class WSPR(gr.sync_block):
    """
    docstring for block 
    """
    def __init__(self, word = 'Haystack Observatory', dotLength = 0.5, sampleRate = 48000, centerBeaconFreq = 10000, centerOffSet = 10000, debug = 0, repeat = 0, minVal = 0 ):
        gr.sync_block.__init__(self,
            name="Morse Code Generator",
            in_sig= [],             #This is a signal block, no inputs
            out_sig=[np.complex64]) #Outputs a complex signal
        #Declare Variables
        self.debug = debug
        self.word = word.upper()
        self.dotLength = dotLength
        self.CBF = centerBeaconFreq
        self.centerOffSet = centerOffSet
        self.sampleRate = sampleRate
        self.repeat = abs(repeat)
        self.minVal = minVal
        self.time = 0
        self.state = 0
        self.B = 10000.0
        self.finalOutputString = "00000"
        #Incrementing variables for the output
        self.buffer_index = 0
        self.sampleCount = 0
        #Calls generating function to create encoded signal based on user inputs
        self.symbol_buffer = self.generateSymbols()
        
    def generateSymbols(self):
        # get information varibales for the signal generation
        word = self.word
        dotLength = self.dotLength
        #morse code dictionary. 1 = dot, 3 = dash, ' ' = 7 count between words
        morseDic = {'A': '13', 'B': '3111', 'C': '3131', 'D': '311', 'E': '1', 'F': '1131','G': '331', 'H': '1111', 'I': '11', 'J': '1333', 'K': '313', 'L': '1311','M': '33', 'N': '31', 'O': '333', 'P': '1331', 'Q': '3313', 'R': '131','S': '111', 'T': '3', 'U': '113', 'V': '1113', 'W': '133', 'X': '3113','Y': '3133', 'Z': '3311', '1': '13333', '2': '11333', '3': '11133','4': '11113', '5': '11111', '6': '31111', '7': '33111', '8': '33311','9': '33331', '0': '33333', ', ': '331133', '.': '131313', '?': '113311','/': '31131' , '(': '31331', ')': '313313', ' ': '7'}
        outputString = ""
        if self.debug != 0: 
            for char in word: 
                outputString += morseDic[char] + "0"
            print(outputString)
        else: 
            for char in word: 
                outputString += morseDic[char] + "0"
        #First transmission has a delay, and the message starts with prosign
        self.finalOutputString = self.finalOutputString + "1110101110101110000000"
        for char in outputString:
            match char: 
                case "3": 
                    self.finalOutputString += "1110"
                case "7": 
                    self.finalOutputString += "000000" 
                case "0": 
                    self.finalOutputString += "00" 
                case "1": 
                    self.finalOutputString += "10" 
                case _: 
                    print("Unknown Symbol")
        self.finalOutputString = self.finalOutputString + "0000001011101011101" #add 'AR' prosign to indicate end of message
        self.numSamplesTX = int(dotLength*self.sampleRate)
        return self.finalOutputString
           
    def work(self, input_items, output_items):
        out = output_items[0]
        noutput_items = len(out)
        n_written = 0
        
        # Idle/Waiting for repeat timer to elapse 
        if self.repeat != 0 and self.state == 1:
            if time.time() >= self.wait_start_time + self.repeat:
                # Wait time completed. Reset transmission indexes and transition back to Transmitting state
                self.buffer_index = 0
                self.sampleCount = 0
                self.state = 0
            else:
                # Still waiting. Fill the entire output buffer with quiet zeros and return early
                out[:] = 0 + 0j
                return noutput_items
        
        # Transmitting symbols
        while n_written < noutput_items:
            if self.buffer_index < len(self.symbol_buffer):
                # How many samples does the current symbol still need?
                samples_needed_for_symbol = self.numSamplesTX - self.sampleCount
                # How much space is left in the current GNU Radio output buffer?
                space_left_in_buffer = noutput_items - n_written
                # Determine the size of the next contiguous chunk to process
                chunk_size = min(samples_needed_for_symbol, space_left_in_buffer)
                
                # Calculate frequency and phase steps for the current symbol
                current_symbol = float(self.symbol_buffer[self.buffer_index])
                if current_symbol== 0: 
                    current_symbol = self.minVal
                phase = (2.0 * np.pi * (self.CBF + self.centerOffSet) / self.sampleRate)
                
                # Vectorized Generation
                t = np.arange(chunk_size)
                chunk_phases = (t * phase)
                
                # Compute the complex exponential for the entire chunk at once
                out[n_written : n_written + chunk_size] = current_symbol * np.exp(1j * chunk_phases)
                
                # Update tracking variables
                self.sampleCount += chunk_size
                n_written += chunk_size
                
                # Advance to the next symbol if this one is finished
                if self.sampleCount >= self.numSamplesTX:
                    self.buffer_index += 1
                    self.sampleCount = 0
            else:
                # All symbols sent. Fill the remaining space with zeros
                out[n_written:] = 0 + 0j
                n_written = noutput_items
                
                # If repeating is enabled, trigger state transition and capture timestamp once
                if self.repeat != 0:
                    self.state = 1
                    self.wait_start_time = time.time()
            
        return noutput_items



