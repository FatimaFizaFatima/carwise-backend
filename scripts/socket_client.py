import asyncio
import sys
import socketio

token = sys.argv[1]
conversation_id = int(sys.argv[2])
text = sys.argv[3] if len(sys.argv) > 3 else None
stay = int(sys.argv[4]) if len(sys.argv) > 4 else 30


async def main():
    sio = socketio.AsyncClient()

    @sio.event
    async def connect():
        print("connected, sid:", sio.sid)

    @sio.event
    async def disconnect():
        print("disconnected")

    @sio.on("new_message")
    async def on_new_message(data):
        print("new_message:", data)
        payload = {"conversation_id": conversation_id, "up_to_message_id": data["id"]}
        print("delivered result:", await sio.call("message_delivered", payload))
        await asyncio.sleep(2)
        print("read result:", await sio.call("messages_read", payload))

    @sio.on("message_status")
    async def on_message_status(data):
        print("message_status:", data)

    @sio.on("presence_update")
    async def on_presence_update(data):
        print("presence_update:", data)

    try:
        await sio.connect("http://localhost:8000", auth={"token": token})
    except socketio.exceptions.ConnectionError as e:
        print("could not connect:", e)
        return

    print("join result:", await sio.call("join_conversation", {"conversation_id": conversation_id}))

    if text:
        await asyncio.sleep(1)
        result = await sio.call("send_message", {"conversation_id": conversation_id, "text": text})
        print("send result:", result)

    await asyncio.sleep(stay)
    await sio.disconnect()


asyncio.run(main())