"""Synthesized sound effects + original music bed for the demo film (no samples).

Cues come from src/generated/demo.json (scene timing) plus the in-scene event times used in src/v2/scenes.tsx.
Usage: python scripts/sound.py <out_dir>  -> writes sfx.wav and music.wav (48 kHz stereo).
"""
import json
import pathlib
import sys
import wave

import numpy as np

SR = 48000
ROOT = pathlib.Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "src" / "generated" / "demo.json").read_text())
SEG = {s["id"]: s for s in D["timeline"]}
TOTAL = D["total"]


def at(seg_id, t):
    s = SEG.get(seg_id)
    return None if s is None else s["from"] + t


def env(n, a=0.002, d=0.3):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / d)


def bell(rng, f=1320, d=0.5):
    n = int(SR * d * 2.5)
    t = np.arange(n) / SR
    y = sum(g * np.sin(2 * np.pi * f * m * t) for m, g in [(1, 1), (2.76, 0.35), (5.4, 0.12)])
    return y * env(n, 0.001, d) * 0.5


def pop(rng, f0=900, f1=300, d=0.08):
    n = int(SR * 0.18)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t / 0.02)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, d) * 0.7


def impact(rng):
    n = int(SR * 1.4)
    t = np.arange(n) / SR
    f = 45 + 160 * np.exp(-t / 0.05)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.45)
    crack = rng.standard_normal(n) * env(n, 0.0005, 0.03) * 0.5
    return np.tanh(2.2 * (y + crack)) * 0.8


def noise_sweep(rng, d=0.7, f0=300, f1=6000, rev=False):
    n = int(SR * d)
    x = rng.standard_normal(n)
    # one-pole low-pass whose cutoff sweeps; amplitude rises then falls
    cut = np.geomspace(f0, f1, n)
    if rev:
        cut = cut[::-1]
    a = np.exp(-2 * np.pi * cut / SR)
    y = np.zeros(n)
    acc = 0.0
    for i in range(n):
        acc = (1 - a[i]) * x[i] + a[i] * acc
        y[i] = acc
    shape = np.sin(np.linspace(0, np.pi, n)) ** (0.6 if not rev else 2.0)
    return y * shape * 1.6


def pluck(rng, f=440, d=0.6):
    n = int(SR * d)
    p = int(SR / f)
    buf = rng.uniform(-1, 1, p)
    out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = 0.5 * (buf[i % p] + buf[(i + 1) % p]) * 0.996
    return out * 0.6


def glitch(rng):
    parts = []
    for _ in range(7):
        k = int(SR * rng.uniform(0.012, 0.04))
        if rng.random() < 0.5:
            seg = rng.standard_normal(k) * 0.6
        else:
            t = np.arange(k) / SR
            seg = np.sign(np.sin(2 * np.pi * rng.uniform(200, 900) * t)) * 0.35
        parts += [seg, np.zeros(int(SR * rng.uniform(0.005, 0.03)))]
    return np.concatenate(parts)


def chime(rng):
    return bell(rng, 1046, 0.6) + np.pad(bell(rng, 1568, 0.7), (int(SR * 0.09), 0))[: len(bell(rng, 1046, 0.6))]


SFX = {
    "ding": lambda r: bell(r, 1760 * r.uniform(0.97, 1.03), 0.35),
    "chime": chime,
    "success": lambda r: bell(r, 1318, 0.5) + np.pad(bell(r, 1975, 0.6), (int(SR * 0.11), 0))[: int(SR * 1.25)],
    "pop": lambda r: pop(r, 900 * r.uniform(0.9, 1.15)),
    "pop_lo": lambda r: pop(r, 520, 160, 0.06),
    "impact": impact,
    "whoosh": lambda r: noise_sweep(r, 0.6),
    "swish": lambda r: noise_sweep(r, 0.35, 800, 9000),
    "riser": lambda r: noise_sweep(r, 1.6, 200, 9000),
    "reverse": lambda r: noise_sweep(r, 0.5, 6000, 400, rev=True),
    "pluck": lambda r: pluck(r, 440 * r.choice([1, 1.25, 1.5])),
    "glitch": glitch,
    "zip": lambda r: pop(r, 300, 1400, 0.12),
}


def cues():
    c = []
    add = lambda t, sfx, gain=1.0, pan=0.0: t is not None and c.append({"t": t, "sfx": sfx, "gain": gain, "pan": pan})
    # Scene cuts: a different transition sound for each.
    trans = ["swish", "whoosh", "reverse", "swish", "whoosh", "reverse"]
    for i, s in enumerate(D["timeline"]):
        if s["id"] in ("01", "02", "06", "07", "08", "09", "10", "11"):
            continue
        add(s["from"] - 0.15, trans[i % len(trans)], 0.45)
    # 01 hook: fragment pops while the flood builds, slams on each phrase, riser into the rush.
    h = SEG["01"]
    vo = D["vo"].get("01", {}).get("dur", 7.4)
    rush = h["dur"] - 26 / 30
    for i in range(0, 46, 2):
        t = (i / 46) * rush * 0.85
        add(h["from"] + t, "pop", 0.18, float(np.sin(i * 1.7)) * 0.7)
    for wi in (9, 11, 13):
        add(h["from"] + h["voAt"] + wi / 19 * vo, "impact", 0.55)
    add(h["from"] + rush - 1.0, "riser", 0.5)
    # 02 reveal: the hit lands on the logo.
    add(at("02", 0.0), "impact", 1.0)
    add(at("02", 0.05), "whoosh", 0.5)
    add(at("02", 1.6), "chime", 0.45)
    # 03 gather: plucks as records stream; 04 audit: scan swish, pops on issues.
    for k in range(6):
        add(at("03", 0.9 + k * 0.45), "pluck", 0.22, -0.4 + k * 0.15)
    add(at("04", 0.4), "swish", 0.35)
    for t in (2.6, 3.1, 3.6):
        add(at("04", t), "pop", 0.4, 0.5)
    add(at("04", 6.2), "ding", 0.35, 0.3)
    # Loop: Band messages (right side), phone bubbles, money token, approvals.
    for seg, t, g in [("05", 0.8, 0.35), ("05", 3.2, 0.35), ("06", 0.6, 0.35), ("06", 3.4, 0.6), ("10", 3.6, 0.35), ("11", 0.6, 0.35)]:
        add(at(seg, t), "pop_lo", g, 0.6)
    add(at("06", 3.5), "success", 0.45, 0.5)
    for seg, t in [("07", 1.0), ("07", 4.6), ("08", 0.6), ("08", 4.2), ("09", 0.8), ("09", 2.4)]:
        add(at(seg, t), "ding", 0.4, 0.55)
    add(at("08", 1.5), "glitch", 0.25, 0.55)  # "Ambiguous" stamp
    add(at("07", 0.2), "pop", 0.3, -0.4)
    add(at("10", 1.6), "zip", 0.45, -0.3)
    add(at("10", 3.4), "success", 0.35, 0.2)
    add(at("11", 2.2), "chime", 0.35, -0.2)
    # 12-13 under the hood
    add(at("12", 0.0), "impact", 0.45)
    # 15 memory: typing plucks, process-exit glitch, strike, success.
    for t in (0.6, 1.2, 2.0, 4.6, 5.4, 6.4):
        add(at("15", t), "pluck", 0.15, -0.4)
    add(at("15", 3.4), "glitch", 0.5, -0.3)
    add(at("15", 7.4), "whoosh", 0.3, 0.4)
    add(at("15", 8.6), "zip", 0.35, 0.4)
    add(at("15", 10.6), "success", 0.45, 0.4)
    # 16 recap callouts, 17 close
    for t in (0.8, 1.6, 2.4):
        add(at("16", t), "pop", 0.3, 0.5)
    add(at("17", 0.0), "impact", 0.6)
    add(at("17", 0.4), "chime", 0.4)
    return [x for x in c if 0 <= x["t"] < TOTAL]


def place(cs):
    n = int(SR * (TOTAL + 2))
    L = np.zeros(n)
    R = np.zeros(n)
    for i, q in enumerate(cs):
        y = SFX[q["sfx"]](np.random.default_rng(1000 + i)) * q["gain"]
        s = int(q["t"] * SR)
        e = min(n, s + len(y))
        y = y[: e - s]
        p = (q["pan"] + 1) / 2
        L[s:e] += y * np.cos(p * np.pi / 2)
        R[s:e] += y * np.sin(p * np.pi / 2)
    # light reverb: a few decaying early reflections
    for d, g in [(0.029, 0.25), (0.047, 0.2), (0.071, 0.14), (0.113, 0.09)]:
        k = int(d * SR)
        L[k:] += g * R[:-k]
        R[k:] += g * L[:-k]
    return L, R


def music():
    """Original ambient bed: soft pad chords + muted pulse at 100 BPM; lifts after the reveal."""
    n = int(SR * (TOTAL + 2))
    t = np.arange(n) / SR
    bpm = 100
    beat = 60 / bpm
    chords = [[220.0, 277.18, 329.63], [196.0, 246.94, 293.66], [174.61, 220.0, 261.63], [196.0, 246.94, 329.63]]
    bar = 4 * beat
    L = np.zeros(n)
    R = np.zeros(n)
    idx = (t // (2 * bar)).astype(int) % len(chords)
    for v in range(3):
        f = np.array([chords[i][v] for i in range(len(chords))])[idx]
        ph = 2 * np.pi * np.cumsum(f) / SR
        L += np.sin(ph * 1.003) * 0.12 + np.sin(ph * 2) * 0.03
        R += np.sin(ph * 0.997) * 0.12 + np.sin(ph * 2.001) * 0.03
    # pulse: soft bass on each beat, from the reveal onward
    reveal = SEG["02"]["from"]
    pulse = np.zeros(n)
    k = 0
    while True:
        s = reveal + k * beat
        if s >= TOTAL:
            break
        i0 = int(s * SR)
        m = min(n - i0, int(SR * 0.4))
        bf = chords[int((s // (2 * bar)) % len(chords))][0] / 2
        tt = np.arange(m) / SR
        pulse[i0 : i0 + m] += np.sin(2 * np.pi * bf * tt) * np.exp(-tt / 0.18) * (0.22 if k % 4 == 0 else 0.13)
        k += 1
    L += pulse
    R += pulse
    # dynamics: quiet tense hook, lift at reveal, settle, swell at close
    g = np.interp(t, [0, 1, reveal - 0.5, reveal, reveal + 8, TOTAL - 10, TOTAL - 4, TOTAL, TOTAL + 2], [0, 0.35, 0.5, 0.9, 0.65, 0.6, 0.85, 0.0, 0])
    return L * g, R * g


def write(path, L, R, peak_db=-1.0):
    m = max(np.abs(L).max(), np.abs(R).max(), 1e-9)
    s = 10 ** (peak_db / 20) / m
    data = (np.stack([L, R], 1) * s * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


if __name__ == "__main__":
    out = pathlib.Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    cs = cues()
    (out / "cues.json").write_text(json.dumps(cs, indent=1))
    write(out / "sfx.wav", *place(cs))
    write(out / "music.wav", *music(), peak_db=-3.0)
    print(f"{len(cs)} cues · total {TOTAL:.1f}s")
