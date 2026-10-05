# houses

Programs of the colony's houses, written in Hope and run by `hope-runtime` (repo `vm`), one VM per house.

| Program | Behaviour |
|---|---|
| `comfort` | 21 C; under a grid limit eco 16 C, under a hard limit (<= 1800 W) antifreeze 6 C |
| `eco` | 18 C by day, 15 C at night, 2 C less while the grid sheds load (level 3+) |
| `night_setback` | 21 C by day, 16 C from 22:00 to 06:00, warm-up from 05:00, 14 C on the UPS |
| `storm_ready` | banks heat at 23.5 C in a storm or wind above 20 m/s, 12 C on the UPS |
| `dumb` | always 26 C, the baseline the others are compared with |

House `i` runs `programs[i % 5]` in the order above, the same assignment as the Python controllers in `world`.

## How a program talks to its house

```
event Sensors()                          // posted by the runtime when the house's readings arrive

on Sensors()
    var t_in of real = sense("t_in")     // any field of hh/house/{id}/sensors, hh/env/weather, hh/env/power
    act("target_c", 21.0)                // actuators: target_c, heater_on, valve_open, appliances_on
    act_text("reason", "comfort 21")     // text actuators: program, reason
end
```

Booleans are read and written as 0.0 / 1.0. A field the world has not sent reads as 0.0.

## Build and run

```bash
HOPEC=../compiler/build/install/untitled/bin/untitled ./build.sh
hope-runtime --programs build/comfort.hbc,build/eco.hbc,build/night_setback.hbc,build/storm_ready.hbc,build/dumb.hbc \
             --houses 300 --mqtt localhost:1883
```

## Test

`tests/diff_against_python.py` sends the same random readings to the runtime and to the Python programs and
compares every decision (target, heater, valves, appliances, reason). 4500 decisions, 0 differences; the `eco`
reason is not compared because the language has no number-to-string conversion yet.
