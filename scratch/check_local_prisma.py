import sys
import os

# Add the project root to sys.path so we can import from app
sys.path.append(os.getcwd())

try:
    from app.generated.prisma import Prisma
    db = Prisma()
    print(f"Has user attribute: {hasattr(db, 'user')}")
    print(f"Has otp attribute: {hasattr(db, 'otp')}")
    print(f"Has refreshtoken attribute: {hasattr(db, 'refreshtoken')}")
except Exception as e:
    print(f"Error: {e}")
