These programs are designed to be run in GNU radio in order to generate and decode AM Morse code signals.

#### Encode Block:
* The generator take in 8 base variables:
  * **word**: The text that you want to encode and transmit
  * **Dotlength**: the base unit of time for the encoder that is the time of a dot (in seconds). All other durations are based on this value
  * **sampleRate**: The sample rate of the GnuRadio flowchart that the block is being run in
  * **Centerbeaconfreq**: This is the carrier frequency that is desired for the tranmsission
  * **centeroffset**: the positive offset from the center frequency
    * **NOTE** If this block is being used with a SDR that does upconversion for the transmission, leave one of these two variables as 0, becuase the carrier is determined by the SDR
  * **debug**: If this is set to anything besides 0, helpful debug text will print as the program runs 
  * **repeat**: The amount of time in seconds that is desired between transmissions 
    * ***NOTE*** To ensure proper functions, make sure that the repeat time (the input integer in seconds) is longer 
      than 10 times the dot length. 
  * **minVal**: set this to a value 0 <= minVal <= 1 to make the off portion of the tramsission have an amplitude 
            equal to minVal (the "on" portion has an amplitude of 1)
* This block outputs this generated signal as a complex OOK (ON-OFF keying) signal.
* Follows standard Morse code protocol
  * Dot is 1 unit
  * Inter-symbol space is 1 unit
  * Dash is 3 units
  * Inter-character space is 3 units
  * Inter-word space is 7 units
* Each tranmsission begins with "-.-.-" (CT) and ends with ".-.-." (AR) prosigns
* First tranmsission is padded with 4 units of silence to avoid start up noise
* Valid characters:
  * A - Z
  * 0 - 9
  * , . ? / ( ) _space_

#### Decode Block:
* This block takes in 5 base variables:
  * **Sample_rate**: sample rate of GNU radio flowchart block is working within
  * **SignalCenterFrequency**: The frequency that the Morse code signal is centered at
  * **MaxRecordLength**: The amount of time in seconds that the decoder should attempt to decode a given transmission
  * **Filteronly**: will not decode if set to 1 and just acts as a filter, will decode if set to 0 and will still filter signal
  * **Debug**: Will print debug text if set to anything but 0, such as calculated dash and dot length.
* This block is designed to decode a Morse Code signal with any dot length, which is determined by the code based on the recived signal
* It also generates a bandpass filter centered at the center frequency that was a width of 2kHz.
  * If the generated signal is less than 1kHz offset from 0 when input to the block, a lowpass filter will be used instead
* The block will also detect the start and end of a tranmsission based on silence duration
* Full decoded message will be printed, and any unknown symbols or errors in the decoding will be printed as [?]
* The filtered signal will be output by the block for debugging purposes so that the user can see what the decoder does  

  



