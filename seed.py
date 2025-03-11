import asyncio
from db import database
from models import roles, users, user_roles
from utils import hash_password

async def seed():
    await database.connect()

    # Seed Roles
    role_names = ["admin", "user"]
    for role_name in role_names:
        query = roles.select().where(roles.c.name == role_name)
        existing_role = await database.fetch_one(query)
        if not existing_role:
            query = roles.insert().values(name=role_name)
            await database.execute(query)

    role_query = roles.select().where(roles.c.name == "admin")
    admin_role = await database.fetch_one(role_query)

    role_query = roles.select().where(roles.c.name == "user")
    user_role = await database.fetch_one(role_query)

    # Seed Admin User
    admin_email = "admin@example.com"
    query = users.select().where(users.c.email == admin_email)
    existing_admin = await database.fetch_one(query)

    if not existing_admin:
        query = users.insert().values(
            username="admin",
            email=admin_email,
            password_hash=hash_password("admin123"),
        )
        admin_id = await database.execute(query)

        # Assign Admin and User roles to the admin
        await database.execute(user_roles.insert().values(user_id=admin_id, role_id=admin_role["id"]))
        await database.execute(user_roles.insert().values(user_id=admin_id, role_id=user_role["id"]))

    print("Database seeded successfully!")
    await database.disconnect()

asyncio.run(seed())
