"""Differential test: the Hope programs on hope-runtime against the Python controllers in world, over a real broker.

    WORLD=../world python3 tests/diff_against_python.py 300 15 1883

hope-runtime must be running with the programs in the order comfort, eco, night_setback, storm_ready, dumb.
"""
import json, os, random, sys, time, threading
sys.path.insert(0, os.environ.get('WORLD', '../world'))
import paho.mqtt.client as mqtt
from hadleys.controllers.programs import PROGRAMS
NAMES = ["comfort", "eco", "night-setback", "storm-ready", "dumb"]
N, ROUNDS, PORT = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
rng = random.Random(7)
got = {}; lock = threading.Lock()
def on_msg(c, u, m):
    if m.topic.endswith('/actuators'):
        with lock: got[int(m.topic.split('/')[2])] = json.loads(m.payload)
c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2); c.on_message = on_msg
c.connect('localhost', PORT); c.subscribe('hh/house/+/actuators'); c.loop_start(); time.sleep(0.5)
mem = {i: {} for i in range(N)}; bad = 0; checked = 0; worst = 0.0
for r in range(ROUNDS):
    weather = {"t": r, "t_out": -40.0, "wind": rng.choice([5.0, 25.0]), "storm": rng.random() < 0.3,
               "hour": rng.choice([3.0, 5.5, 12.0, 23.0]), "night": rng.random() < 0.5}
    power = {"t": r, "available_kw": 3000, "demand_kw": 2800, "shedding": rng.choice([0, 0, 3, 5])}
    c.publish('hh/env/weather', json.dumps(weather)); c.publish('hh/env/power', json.dumps(power)); time.sleep(0.15)
    sens = {}
    with lock: got.clear()
    for i in range(N):
        s = {"t": r, "id": i, "t_in": round(rng.uniform(4, 28), 1), "on_ups": rng.random() < 0.2,
             "limit_w": rng.choice([0, 0, 0, 1500, 2500]), "pipes_ok": rng.random() < 0.9, "net_online": rng.random() < 0.8}
        sens[i] = s; c.publish(f'hh/house/{i}/sensors', json.dumps(s))
    t0 = time.time()
    while time.time() - t0 < 10:
        with lock:
            if len(got) >= N: break
        time.sleep(0.02)
    lat = time.time() - t0; worst = max(worst, lat)
    for i in range(N):
        want = PROGRAMS[NAMES[i % 5]]({"sensors": sens[i], "weather": weather, "power": power, "mem": mem[i]})
        have = got.get(i)
        checked += 1
        if have is None: bad += 1; print("missing", i); continue
        for k in ("target_c", "heater_on", "appliances_on", "valve_open"):
            if (abs(have[k] - want[k]) > 1e-9) if isinstance(want[k], float) else (bool(have[k]) != bool(want[k])):
                bad += 1; print("MISMATCH", r, i, NAMES[i % 5], k, have[k], want[k], sens[i]); break
        else:
            if NAMES[i % 5] != "eco" and have["reason"] != want["reason"]:
                bad += 1; print("REASON", i, have["reason"], "|", want["reason"])
print(f"checked {checked} decisions over {ROUNDS} rounds x {N} houses: {bad} mismatches; slowest round answered in {worst*1000:.0f} ms")
sys.exit(1 if bad else 0)
