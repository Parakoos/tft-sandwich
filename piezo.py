from simpleio import tone
from settings import PIEZO_PIN

# Define a list of tones/music notes to play.
TONE_FREQ = [ 262,  # C4
              294,  # D4
              330,  # E4
              349,  # F4
              392,  # G4
              440,  # A4
              494 ] # B4

def beep_success():
    tone(PIEZO_PIN, TONE_FREQ[3], duration=0.1)

def beep_shake():
    tone(PIEZO_PIN, TONE_FREQ[5], duration=0.1)
    tone(PIEZO_PIN, TONE_FREQ[2], duration=0.1)
    tone(PIEZO_PIN, TONE_FREQ[5], duration=0.1)
    tone(PIEZO_PIN, TONE_FREQ[2], duration=0.1)

def beep_error():
    tone(PIEZO_PIN, TONE_FREQ[0], duration=0.1)
    tone(PIEZO_PIN, TONE_FREQ[6], duration=0.2)

def cascade():
    for i in range(len(TONE_FREQ)):
        tone(PIEZO_PIN, TONE_FREQ[i], duration=0.1)