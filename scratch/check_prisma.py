from prisma import Prisma

db = Prisma()
print(f"Has user attribute: {hasattr(db, 'user')}")
print(f"Has otp attribute: {hasattr(db, 'otp')}")
print(f"Has refreshtoken attribute: {hasattr(db, 'refreshtoken')}")
