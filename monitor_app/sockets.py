from process_monitor.asgi import sio  # import the server
import psutil
import asyncio

""" WebSocket consumer for real-time process monitoring. """
@sio.event
async def connect(sid, environ):
    print("Client connected:", sid)
    await sio.emit("server_message", {"data": "Welcome to Process Monitor!"}, to=sid)

@sio.event
async def disconnect(sid):
    print("Client disconnected:", sid)

# custom event to stream process data
@sio.event
async def get_processes(sid):
    while True:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                processes.append(proc.info)
            except:
                continue

        await sio.emit("process_data", processes, to=sid)
        await asyncio.sleep(5)  # send updates every 5 seconds
