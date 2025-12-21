# cluster_async.py  12/20/2025
import asyncio
from backend.message_bus import publish, register_callback

# CC11 field indices
spotType           = 0
spotFreq           = 1
spotDXCall         = 2
spotDate           = 3
spotZulu           = 4
spotComment        = 5
spotSpotter        = 6
spotDXITU          = 10
spotDXCountry      = 16
spotDXGrid         = 18
spotSpotterState   = 15

# Simple ARRL band plan in kHz
ARRL_BAND_PLAN = [
    (1800,  2000,  "160m"),
    (3500,  4000,  "80m"),
    (5000,  5450,  "60m"),
    (7000,  7300,  "40m"),
    (10100, 10150, "30m"),
    (14000, 14350, "20m"),
    (18068, 18168, "17m"),
    (21000, 21450, "15m"),
    (24890, 24990, "12m"),
    (28000, 29700, "10m"),
    (50000, 54000, "6m"),
]

def determine_band(freq_value):
    try:
        f = float(freq_value)
    except:
        return "?"
    for low, high, name in ARRL_BAND_PLAN:
        if low <= f <= high:
            return name
    return "?"

HOST = "www.ve7cc.net"
PORT = 23

# Global queue for commands from UI
command_queue = asyncio.Queue()

async def run_cluster_monitor():
    """
    Main VE7CC cluster monitor loop.
    Includes clean shutdown support to avoid pending-task warnings.
    """
    # Register callback to receive commands from UI
    def on_command(msg: dict):
        if msg.get("type") == "cluster_command":
            cmd = msg.get("data", "")
            print(f"DEBUG BACKEND: Received command: '{cmd}'")
            if cmd:
                command_queue.put_nowait(cmd)
    
    register_callback(on_command)
    
    try:
        while True:
            try:
                publish({"type": "status", "data": "Connecting to cluster..."})
                reader, writer = await asyncio.open_connection(HOST, PORT)
                publish({"type": "status", "data": "Cluster connected"})
                
                # login commands
                writer.write(b"N4LR\n")
                writer.write(b"set/nofilter\n")
                writer.write(b"set/ve7cc\n")
                writer.write(b"set/skimmer\n")
                await writer.drain()
                
                # Start task to handle commands from UI
                command_task = asyncio.create_task(handle_commands(writer))
                
                while True:
                    line = await reader.readline()
                    if not line:
                        command_task.cancel()
                        raise ConnectionError("Cluster disconnected")
                    
                    s = line.decode(errors="ignore").strip()
                    if not s:
                        continue
                    
                    if s.startswith(("WCY", "WWV", "To ")):
                        continue
                    
                    parts = s.split("^")
                    if len(parts) < 20:
                        continue
                    
                    if parts[spotType] != "CC11":
                        continue
                    
                    spot = {
                        "tag": "",
                        "band": determine_band(parts[spotFreq]),
                        "freq": parts[spotFreq],
                        "call": parts[spotDXCall],
                        "dxcc": parts[spotDXCountry],
                        "grid": parts[spotDXGrid],
                        "spotter": parts[spotSpotter],
                        "comment": parts[spotComment],
                        "time": parts[spotZulu],
                    }
                    publish({"type": "spot", "data": spot})
                    
            except Exception as e:
                publish({
                    "type": "status",
                    "data": f"Cluster lost — retrying in 5s... ({e})"
                })
                await asyncio.sleep(5)
                
    except asyncio.CancelledError:
        # clean exit — stop raising warnings
        publish({"type": "status", "data": "Backend stopped."})
        return

async def handle_commands(writer):
    """Handle commands from the UI and send to cluster"""
    try:
        while True:
            cmd = await command_queue.get()
            # Ensure command ends with newline
            if not cmd.endswith("\n"):
                cmd += "\n"
            writer.write(cmd.encode())
            await writer.drain()
            publish({"type": "status", "data": f"Sent: {cmd.strip()}"})
    except asyncio.CancelledError:
        pass
