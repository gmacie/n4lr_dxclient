# cluster_async.py  12/21/2025 - Added connect/disconnect control

from backend.app_logging import get_logger

logger = get_logger(__name__)

import asyncio
from backend.message_bus import publish
from backend.config import get_user_callsign, get_current_server

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

# Global queue for commands from UI
command_queue = asyncio.Queue()

# Global connection control
_should_disconnect = False
_connection_task = None


async def run_cluster_monitor(server_host: str = None, server_port: int = None):
    """
    Main VE7CC cluster monitor loop with connect/disconnect support.
    """
    global _should_disconnect
    
    print(f"DEBUG: run_cluster_monitor called with host={server_host}, port={server_port}")  # ADD THIS LINE
    
    # Get server from config if not specified
    if not server_host:
        server_str = get_current_server()
        print(f"DEBUG: Got server from config: {server_str}")  # ADD THIS LINE
        parts = server_str.split(':')
        server_host = parts[0]
        server_port = int(parts[1]) if len(parts) > 1 else 23
    
    callsign = get_user_callsign()
    print(f"DEBUG: Using callsign: {callsign}")  # ADD THIS
    _should_disconnect = False
    
    try:
        while not _should_disconnect:
            try:
                print(f"DEBUG: Attempting connection to {server_host}:{server_port}")  # ADD THIS
                publish({"type": "status", "data": f"Connecting to {server_host}:{server_port}..."})
                reader, writer = await asyncio.open_connection(server_host, server_port)
                print(f"DEBUG: Connected! Sending login...")  # ADD THIS
                publish({"type": "status", "data": f"Connected to {server_host}"})
                
                # login commands
                print(f"DEBUG: Sending callsign: {callsign}")
                writer.write(f"{callsign}\n".encode())
                await writer.drain()
                
                # Read the welcome/prompt
                for i in range(5):
                    line = await reader.readline()
                    print(f"DEBUG: Server response {i}: {line.decode(errors='ignore').strip()}")
                
                print(f"DEBUG: Sending cluster commands...")
                
                logger.info("STARTUP → Sending initialization commands")
                
                writer.write(b"set/nofilter\n")
                logger.info("STARTUP CMD - set/nofilter")
                
                writer.write(b"set/ve7cc\n")
                logger.info("STARTUP CMD - set/ve7cc")
                
                writer.write(b"set/skimmer\n")
                logger.info("STARTUP CMD - set/skimmer")
                
                logger.info("STARTUP OK Initialization complete")
                
                await writer.drain()
                print(f"DEBUG: Login commands sent, waiting for spots...")
                
                # Start task to handle commands from UI
                command_task = asyncio.create_task(handle_commands(writer))
                
                while not _should_disconnect:
                    line = await reader.readline()
                    if not line:
                        command_task.cancel()
                        raise ConnectionError("Cluster disconnected")
                    
                    s = line.decode(errors="ignore").strip()
                    
                    if s:
                        pass
                        #print(f"DEBUG: Received: {s[:100]}")
                        
                    if not s:
                        continue
                        
                    # Parse WWV solar data from cluster
                    if s.startswith("WWV"):
                        # Skip WWV header line
                        continue
                        
                    # Parse solar data lines (format: "23-Dec-2025   15   133  25   4 Minor...")
                    if "-2025" in s and len(s) > 30:  # Looks like a date line
                        parts_wwv = s.split()
                        if len(parts_wwv) >= 5:
                            try:
                                # Parse: Date Hour SFI A K ...
                                sfi = float(parts_wwv[2])  # "133"
                                a = int(parts_wwv[3])      # "25"
                                k = int(parts_wwv[4])      # "4"
                
                                # Publish solar data update
                                publish({
                                    "type": "solar_update",
                                    "data": {
                                        "sfi": sfi,
                                        "a": a,
                                        "k": k,
                                    }
                                })
                                continue  # Don't process as spot
                            except (ValueError, IndexError):
                                pass  # Not a valid solar line
    
                    # Skip other non-spot lines
                    if s.startswith(("WCY", "To ")):
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
                    #73print(f"DEBUG: Publishing spot: {spot['call']} on {spot['band']}")
                    publish({"type": "spot", "data": spot})
                
                # Clean disconnect
                command_task.cancel()
                writer.close()
                await writer.wait_closed()
                publish({"type": "status", "data": "Disconnected"})
                break  # Exit loop on manual disconnect
                    
            except asyncio.CancelledError:
                # Task was cancelled - clean exit
                publish({"type": "status", "data": "Disconnected"})
                return
                
            except Exception as e:
                if _should_disconnect:
                    publish({"type": "status", "data": "Disconnected"})
                    break
                else:
                    publish({
                        "type": "status",
                        "data": f"Connection lost — retrying in 5s... ({e})"
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
            
            # Log success
            logger.info(f"CLUSTER CMD - {cmd.strip()}")
            publish({"type": "status", "data": f"Sent: {cmd.strip()}"})
            
    except asyncio.CancelledError:
        pass

async def start_connection(server_host: str = None, server_port: int = None):
    """Start cluster connection (call from UI using page.run_task)"""
    global _connection_task, _should_disconnect
    
    _should_disconnect = False
    
    # Cancel existing connection if any
    if _connection_task and not _connection_task.done():
        _connection_task.cancel()
    
    # Start the monitor
    await run_cluster_monitor(server_host, server_port)


def stop_connection():
    """Stop cluster connection (call from UI)"""
    global _should_disconnect, _connection_task
    
    _should_disconnect = True
    
    if _connection_task and not _connection_task.done():
        _connection_task.cancel()
