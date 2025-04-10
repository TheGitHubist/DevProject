import asyncio
import websockets
import json

class WebSocketClient:
    def __init__(self, uri="ws://localhost:5000/ws"):
        self.uri = uri
        self.websocket = None
    
    async def connect(self):
        self.websocket = await websockets.connect(
            self.uri,
            extra_headers={
                'Origin': 'http://localhost',
                'User-Agent': 'PythonWebSocketClient',
                'Connection': 'Upgrade',
                'Upgrade': 'websocket',
                'Sec-WebSocket-Version': '13'
            },
            subprotocols=['chat']
        )
        return self
    
    async def send(self, data):
        if isinstance(data, dict):
            data = json.dumps(data)
        await self.websocket.send(data)
    
    async def receive(self):
        message = await self.websocket.recv()
        try:
            return json.loads(message)
        except json.JSONDecodeError:
            return message
    
    async def close(self):
        await self.websocket.close()

async def example_usage():
    client = await WebSocketClient().connect()
    try:
        await client.send({"type": "greeting", "data": "Hello Server!"})
        response = await client.receive()
        print("Received:", response)
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(example_usage())
