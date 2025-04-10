import asyncio
import websockets
import json
from typing import Set
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('websockets')

class WebSocketServer:
    def __init__(self):
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
    
    async def register(self, websocket: websockets.WebSocketServerProtocol):
        remote = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"New connection from {remote}")
        self.clients.add(websocket)
        try:
            await self.handle_connection(websocket)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed by {remote}")
        except Exception as e:
            logger.error(f"Error in connection {remote}: {e}")
        finally:
            self.clients.remove(websocket)
            logger.info(f"Connection cleaned up for {remote}")
    
    async def handle_connection(self, websocket):
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received message: {data}")
                await self.broadcast(data, sender=websocket)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received")
            except Exception as e:
                logger.error(f"Error handling message: {e}")

    async def broadcast(self, data, sender=None):
        message = json.dumps(data)
        for client in self.clients:
            if client != sender and client.open:
                try:
                    await client.send(message)
                except:
                    logger.warning("Failed to send to client")

async def start_server():
    server = WebSocketServer()
    async with websockets.serve(
        server.register,
        "localhost",
        8765,
        ping_interval=20,
        ping_timeout=60,
        close_timeout=1
    ):
        logger.info("WebSocket server started on ws://localhost:8765")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(start_server())
