from prisma import Prisma

db = Prisma()

async def connect_db():
    await db.connect()

async def disconnect_db():
    if db.is_connected():
        await db.disconnect()
