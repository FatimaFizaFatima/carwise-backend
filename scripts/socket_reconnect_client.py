import asyncio
import sys
import aiohttp
import socketio

BASE = "http://localhost:8000"
token = sys.argv[1]
conversation_id = int(sys.argv[2])
stay = int(sys.argv[3]) if len(sys.argv) > 3 else 120
last_id = int(sys.argv[4]) if len(sys.argv) > 4 else 0


async def main():
    global last_id
    http = aiohttp.ClientSession(headers={"Authorization": f"Bearer {token}"})
    sio = socketio.AsyncClient(
        reconnection=True, reconnection_delay=1, reconnection_delay_max=5
    )

    async def confirm(up_to_id):
        payload = {"conversation_id": conversation_id, "up_to_message_id": up_to_id}
        await sio.call("message_delivered", payload)
        await sio.call("messages_read", payload)

    async def catch_up():
        global last_id
        params = {"after_id": last_id} if last_id else {"limit": 30}
        url = f"{BASE}/chat/conversations/{conversation_id}/messages"
        async with http.get(url, params=params) as resp:
            body = await resp.json()
            if resp.status != 200:
                print("catch-up failed:", resp.status, body)
                return
        ids = [m["id"] for m in body]
        print("caught up, message ids:", ids)
        if ids:
            last_id = max(last_id, max(ids))
            await confirm(last_id)

    async def on_ready():
        result = await sio.call("join_conversation", {"conversation_id": conversation_id})
        print("join result:", result)
        await catch_up()

    @sio.event
    async def connect():
        print("connected, sid:", sio.sid)
        asyncio.create_task(on_ready())

    @sio.event
    async def disconnect():
        print("disconnected")

    @sio.on("new_message")
    async def on_new_message(data):
        global last_id
        print("new_message:", data)
        last_id = max(last_id, data["id"])
        await confirm(data["id"])

    @sio.on("message_status")
    async def on_message_status(data):
        print("message_status:", data)

    @sio.on("presence_update")
    async def on_presence_update(data):
        print("presence_update:", data)

    await sio.connect(BASE, auth={"token": token})
    await asyncio.sleep(stay)
    await sio.disconnect()
    await http.close()


asyncio.run(main())