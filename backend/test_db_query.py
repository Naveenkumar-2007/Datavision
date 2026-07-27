import asyncio
import uuid
import sys
from sqlalchemy.future import select
from sqlalchemy import cast, String

# Add backend to path
sys.path.insert(0, r"C:\Users\navee\Cisco Packet Tracer 8.2.2\saves\Datavision\backend")

from database.db import AsyncSessionLocal
from database.orm import WorkspaceMember, UserProfile

async def test():
    user_id = "18469900-b076-4b6a-a1f0-edcd87ad4ad3"
    user_id_obj = uuid.UUID(user_id)
    
    async with AsyncSessionLocal() as db:
        try:
            print("Running test query...")
            stmt = select(WorkspaceMember, UserProfile).join(
                UserProfile, WorkspaceMember.workspace_id == cast(UserProfile.id, String)
            ).where(WorkspaceMember.user_id == user_id_obj)
            
            res = await db.execute(stmt)
            memberships = res.all()
            print(f"Success! Found {len(memberships)} memberships")
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
