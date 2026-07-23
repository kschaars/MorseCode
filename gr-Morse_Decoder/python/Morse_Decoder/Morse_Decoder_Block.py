#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 MIT Haystack Observatory.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
import numpy as np
from gnuradio import gr
import scipy.signal as signal

class wsprd_time_synced_block(gr.sync_block):
    def __init__(self, sample_rate=10000, signalCenterFrequency=1000,
                 maxRecordLength=60, filterOnly=1, debug = 0):
        gr.sync_block.__init__(self, name='Morse Code Decoder',
                               in_sig=[np.complex64], out_sig=[np.complex64])
        self.sample_rate = sample_rate
        self.signalCenterFreq = signalCenterFrequency
        self.samples_to_record = int(maxRecordLength * self.sample_rate)
        self.filterOnly = filterOnly
        self.deci = max(1, round(self.sample_rate / 100))
        self.d_count = self.deci
        self.debug = debug
        self.bits = []
        self.dotTimeArr = []          # ON-pulse lengths dot estimate
        self.ninputItems = 0
        self.state = 0
        self.highDurCounter = 0
        self.lowDurCounter = 0
        self.pwr_high = 0.004          # rising threshold
        self.pwr_low  = 0.002          # falling threshold 
        self.active = False
        self.finalList = []
        self.textOutput = ''
        self.morseDic = {
            '13':'A','3111':'B','3131':'C','311':'D','1':'E','1131':'F','331':'G',
            '1111':'H','11':'I','1333':'J','313':'K','1311':'L','33':'M','31':'N',
            '333':'O','1331':'P','3313':'Q','131':'R','111':'S','3':'T','113':'U',
            '1113':'V','133':'W','3113':'X','3133':'Y','3311':'Z',
            '13333':'1','11333':'2','311113':'3','11113':'4','11111':'5',
            '31111':'6','33111':'7','33311':'8','33331':'9','33333':'0',
            '331133':', ','131313':'.','113311':'?','31131':'/','31331':'(',
            '313313':')',
            '31313':'\n-- Start of Message --\n',   # CT / KA  (-.-.-)
            '13131':'\n-- End of Message --\n',      # AR       (.-.-.)
        }

        # band-pass filter
        fL = self.signalCenterFreq - 1000
        fH = self.signalCenterFreq + 1000
        NL = NH = 433
        beta = 6.755
        hlpf = np.sinc(2*fH/self.sample_rate*(np.arange(NH)-(NH-1)/2)) * np.kaiser(NH, beta)
        hlpf /= np.sum(hlpf)
        hhpf = np.sinc(2*fL/self.sample_rate*(np.arange(NL)-(NL-1)/2)) * np.kaiser(NL, beta)
        hhpf /= np.sum(hhpf)
        hhpf = -hhpf
        hhpf[(NL-1)//2] += 1
        if fL < 0:
            self.h = hlpf
        else:
            self.h = np.convolve(hlpf, hhpf)
        self.filter_state = np.zeros(len(self.h)-1, dtype=np.complex64)

    def _estimate_unit(self, on_runs):
        """Estimate the dot length (in counts) from ON-pulse durations.
        Returns (dot, dash, ok) where ok flags whether the 3:1 ratio held."""
        v = sorted(float(x) for x in on_runs if x > 0)
        if len(v) < 2:
            return (v[0], v[0]*3, False) if v else (None, None, False)

        # glitch rejection: discard runs < 30% of the median pulse
        med = np.median(v)
        v = [x for x in v if x >= 0.30 * med] or v

        # 2-means (dot cluster vs dash cluster)
        lo, hi = v[0], v[-1]
        for _ in range(50):
            g_lo = [x for x in v if abs(x - lo) <= abs(x - hi)]
            g_hi = [x for x in v if abs(x - lo) >  abs(x - hi)]
            if not g_lo or not g_hi:
                break
            nlo, nhi = np.mean(g_lo), np.mean(g_hi)
            if abs(nlo - lo) < 1e-6 and abs(nhi - hi) < 1e-6:
                break
            lo, hi = nlo, nhi
        ratio = hi / lo if lo > 0 else 0
        # If the two clusters are close, the message is probably all dots all
        # dashes
        if ratio < 1.8:
            dot = np.median(v)
            return dot, dot * 3, False
        return lo, hi, (2.2 <= ratio <= 4.0)   # ok if ratio is near the ideal 3:1

    def work(self, input_items, output_items):
        in0 = input_items[0]
        out_data = output_items[0]
        filtered_in0, self.filter_state = signal.lfilter(self.h, 1, in0, zi=self.filter_state)
        n = len(filtered_in0)
        out_data[:n] = filtered_in0
        if self.filterOnly == 1: 
            return n
        self.finalList = []
        self.textOutput = ''

        # Recording
        if self.ninputItems <= self.samples_to_record and self.state == 0:
            ni = 0
            while ni < n:
                self.d_count -= 1
                if self.d_count <= 0:
                    power = abs(filtered_in0[ni])**2
                    # only flip state when clearly crossing a threshold
                    if power >= self.pwr_high:
                        self.active = True
                    elif power <= self.pwr_low:
                        self.active = False

                    if self.active:
                        self.bits.append(1)
                        self.highDurCounter += 1
                        self.lowDurCounter = 0
                    else:
                        if self.highDurCounter > 0:
                            self.dotTimeArr.append(self.highDurCounter)
                            if len(self.dotTimeArr) == 1 and self.filterOnly != 1:
                                print("Message Receive Started...")
                        self.highDurCounter = 0
                        self.lowDurCounter += 1
                        self.bits.append(0)
                    if self.highDurCounter == 0 and len(self.dotTimeArr) >= 3:
                        dot_est = np.median(self.dotTimeArr)      # running estimate
                        if self.lowDurCounter >= 10 * dot_est:    # long silence => done
                            self.state = 1
                    self.d_count = self.deci
                ni += 1
                self.ninputItems += 1
            return n
            
        if len(self.dotTimeArr) == 0:
            print("No Morse pulses recorded.")
            self.ninputItems = 0 
            return n
        try:
            start_index = self.bits.index(1)
            self.bits = self.bits[start_index:]
        except ValueError:
            print("No active signals found in recording.")
            return -1
        # run-length encode
        rle = []
        cur, ln = self.bits[0], 1
        for b in self.bits[1:]:
            if b == cur:
                ln += 1
            else:
                rle.append([cur, ln]); cur, ln = b, 1
        rle.append([cur, ln])

        # rough dot estimate to set a glitch threshold
        on_runs = [l for s, l in rle if s == 1]
        dot, dash, ok = self._estimate_unit(on_runs)
        if dot is None:
            print("Could not estimate timing.")
            return -1
        min_run = 0.4 * dot

        #glitch removal: absorb sub-0.4-dot runs, then re-merge
        cleaned = []
        for state, length in rle:
            if length < min_run and cleaned:
                if len(cleaned) >= 2:
                    cleaned[-2][1] += length      # give time back to same-state run
                else:
                    cleaned[-1][1] += length
            else:
                cleaned.append([state, length])
        rle = []
        for state, length in cleaned:
            if rle and rle[-1][0] == state:
                rle[-1][1] += length
            else:
                rle.append([state, length])

        # refined estimate on cleaned data 
        on_runs = [l for s, l in rle if s == 1]
        dot, dash, ok = self._estimate_unit(on_runs)
        if self.filterOnly == 0 and self.debug ==1:
            print(f"[timing] dot~{dot:.1f} dash~{dash:.1f} counts "
                  f"({dot*self.deci/self.sample_rate*1000:.0f} ms/dot) "
                  f"{'OK' if ok else 'LOW-CONFIDENCE'}")

        #thresholds derived from the single estimated unit
        active_midpoint     = 2 * dot   # dot(1) vs dash(3)
        space_midpoint_char = 2 * dot   # intra-element(1) vs inter-char(3)
        space_midpoint_word = 5 * dot   # inter-char(3) vs inter-word(7)

        for state, length in rle:
            if state == 1:
                self.finalList.append('1' if length < active_midpoint else '3')
            else:
                if length < space_midpoint_char:
                    pass
                elif length < space_midpoint_word:
                    self.finalList.append('0')
                else:
                    self.finalList.append('7')
        # decode
        lastIndex = 0
        for curIndex in range(len(self.finalList)):
            marker = self.finalList[curIndex]
            if marker in ('0', '7'):
                t = "".join(self.finalList[lastIndex:curIndex])
                if t:
                    self.textOutput += self.morseDic.get(t, '[?]')
                    if t not in self.morseDic:
                        print(f"Warning: Unknown Morse sequence '{t}'")
                if marker == '7':
                    self.textOutput += ' '
                lastIndex = curIndex + 1

        # remove trailing element after the last space
        t = "".join(self.finalList[lastIndex:])
        if t:
            self.textOutput += self.morseDic.get(t, '[?]')

        if self.filterOnly == 0:
            print(self.textOutput)

        # reset for next message
        self.ninputItems = 0
        self.bits = []
        self.dotTimeArr = []
        self.state = 0
        self.active = False
        self.highDurCounter = 0
        self.lowDurCounter = 0
        return n

