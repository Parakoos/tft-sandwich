from time import monotonic
from gc import mem_free

debug_ts = monotonic()
prev_memory = mem_free()

timers = {}

def debug(text):
    seconds_into_run = monotonic() - debug_ts
    print(f"{seconds_into_run:.3f}: {text}")

def time_progress(tag, text):
    now = round(monotonic() * 1000)
    if not tag in timers:
        timers[tag] = (now, None, None)
    if timers[tag][1] != None:
        debug(f"{tag} {now-timers[tag][2]:>4} ms: {timers[tag][1]}")
    if text == None:
        debug(f"{tag} {now-timers[tag][0]:>4} ms: (TOTAL TIME)")
        del timers[tag]
    else:
        timers[tag] = (timers[tag][0], text, now)

def show_memory(tag):
    global prev_memory
    curr_mem = mem_free()
    used_mem = curr_mem - prev_memory
    prev_memory = curr_mem
    curr_memory_kb = f"{round(curr_mem/1000):>4} kb"
    used_memory_kb = f"{round(used_mem/1000):>4} kb"
    debug(f"Mem: {curr_memory_kb}, (Used {used_memory_kb})  --- {tag}")