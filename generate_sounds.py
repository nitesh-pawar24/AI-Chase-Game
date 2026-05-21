"""
Sound generator for AI Chase Game.
Generates all required sound effects as WAV files in assets/sounds/.
"""
import os
import struct
import math
import wave
import numpy as np

SAMPLE_RATE = 44100
OUTPUT_DIR = os.path.join("assets", "sounds")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def save_wav(filename, samples, rate=SAMPLE_RATE):
    """Save numpy float32 array (values in -1..1) as a 16-bit mono WAV file."""
    samples = np.clip(samples, -1.0, 1.0)
    int_samples = (samples * 32767).astype(np.int16)
    path = os.path.join(OUTPUT_DIR, filename)
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(int_samples.tobytes())
    print(f"  Created: {path}")

t_sec = lambda duration: np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)

# ──────────────────────────────────────────────
# 1. MENU BACKGROUND MUSIC  (looping ambient)
# ──────────────────────────────────────────────
def gen_menu_music():
    dur = 8.0
    t = t_sec(dur)

    # Drone base note  (A2 = 110 Hz)
    base = np.sin(2 * np.pi * 110 * t) * 0.18
    # Slow pulsing pad (E3 = 164.81 Hz)
    pad1 = np.sin(2 * np.pi * 164.81 * t + np.sin(2 * np.pi * 0.4 * t)) * 0.12
    # Higher shimmer (A4 = 440 Hz), tremolo
    shimmer = np.sin(2 * np.pi * 440 * t) * (0.06 + 0.04 * np.sin(2 * np.pi * 3.5 * t))
    # Sparkle hits every 2 s
    sparkle = np.zeros_like(t)
    for hit in [0.0, 2.0, 4.0, 6.0]:
        start = int(hit * SAMPLE_RATE)
        env = np.exp(-np.linspace(0, 8, int(0.5 * SAMPLE_RATE)))
        end = min(start + len(env), len(sparkle))
        sparkle[start:end] += np.sin(2 * np.pi * 880 * t[:end - start]) * env[:end - start] * 0.08

    mix = base + pad1 + shimmer + sparkle
    # Smooth fade-in and fade-out for seamless looping
    fade = int(0.4 * SAMPLE_RATE)
    mix[:fade] *= np.linspace(0, 1, fade)
    mix[-fade:] *= np.linspace(1, 0, fade)
    save_wav("menu_music.wav", mix)

# ──────────────────────────────────────────────
# 2. PLAYER WON  (triumphant arpeggio)
# ──────────────────────────────────────────────
def gen_player_won():
    notes = [523.25, 659.25, 783.99, 1046.50]  # C5 E5 G5 C6
    all_s = []
    for freq in notes:
        dur = 0.18
        t = t_sec(dur)
        env = np.exp(-t * 6)
        s = np.sin(2 * np.pi * freq * t) * env * 0.7
        all_s.append(s)
    # Final long chord
    dur = 0.9
    t = t_sec(dur)
    env = np.exp(-t * 1.8)
    chord = (np.sin(2 * np.pi * 523.25 * t) +
             np.sin(2 * np.pi * 659.25 * t) +
             np.sin(2 * np.pi * 783.99 * t)) * env * 0.28
    all_s.append(chord)
    save_wav("player_won.wav", np.concatenate(all_s))

# ──────────────────────────────────────────────
# 3. PLAYER CAUGHT  (descending doom)
# ──────────────────────────────────────────────
def gen_player_caught():
    dur = 1.2
    t = t_sec(dur)
    freq = 440 * np.exp(-t * 2.0)           # pitch drops over time
    env = np.exp(-t * 1.5)
    wave_data = np.sign(np.sin(2 * np.pi * freq * t)) * env * 0.55  # square for harshness
    # low rumble underneath
    rumble = np.random.normal(0, 0.15, len(t)) * np.exp(-t * 2.5)
    save_wav("player_caught.wav", wave_data + rumble)

# ──────────────────────────────────────────────
# 4. TIME UP  (urgent beep sequence)
# ──────────────────────────────────────────────
def gen_time_up():
    parts = []
    for i in range(4):
        dur = 0.12
        t = t_sec(dur)
        freq = 880 if i < 3 else 440
        env = np.exp(-t * 20)
        parts.append(np.sin(2 * np.pi * freq * t) * env * 0.6)
        parts.append(np.zeros(int(0.08 * SAMPLE_RATE)))  # gap
    # Final long low tone
    dur = 0.7
    t = t_sec(dur)
    env = np.exp(-t * 2)
    parts.append(np.sin(2 * np.pi * 220 * t) * env * 0.5)
    save_wav("time_up.wav", np.concatenate(parts))

# ──────────────────────────────────────────────
# 5. FOOTSTEP  (short thud + shuffle)
# ──────────────────────────────────────────────
def gen_footstep():
    dur = 0.14
    t = t_sec(dur)
    # Low thud
    thud_freq = 120
    thud = np.sin(2 * np.pi * thud_freq * t) * np.exp(-t * 30) * 0.55
    # High-frequency shuffle (filtered noise)
    noise = np.random.normal(0, 1, len(t))
    # Simple moving average to band-pass noise
    kernel_size = 5
    kernel = np.ones(kernel_size) / kernel_size
    noise = np.convolve(noise, kernel, mode='same') * np.exp(-t * 50) * 0.25
    save_wav("footstep.wav", thud + noise)

# ──────────────────────────────────────────────
# 6. COUNTDOWN (Ticks and GO!)
# ──────────────────────────────────────────────
def gen_countdown_tick():
    dur = 0.15
    t = t_sec(dur)
    env = np.exp(-t * 20)
    beep = np.sin(2 * np.pi * 600 * t) * env * 0.4
    save_wav("countdown_tick.wav", beep)

def gen_countdown_go():
    dur = 0.6
    t = t_sec(dur)
    env = np.exp(-t * 5)
    chord = (np.sin(2 * np.pi * 800 * t) + np.sin(2 * np.pi * 1000 * t)) * env * 0.5
    save_wav("countdown_go.wav", chord)

# ──────────────────────────────────────────────
# Run all generators
# ──────────────────────────────────────────────
print("Generating sounds...")
gen_menu_music()
gen_player_won()
gen_player_caught()
gen_time_up()
gen_footstep()
gen_countdown_tick()
gen_countdown_go()
print("All sounds generated successfully!")
