import asyncio
import traceback

from app.infrastructure.database import get_session_factory
from app.modules.identity.application.services import AuthenticationService
from app.modules.identity.infrastructure.repositories.user_repository import UserRepository
from app.modules.identity.schemas.auth_schemas import RegisterRequest


async def main():
    factory = get_session_factory()
    async with factory() as session:
        repo = UserRepository(session)
        service = AuthenticationService(repo)
        req = RegisterRequest(email="samarth@curos.com", password="testpassword123", first_name="Samarth", last_name="Patil")  # noqa: S106
        try:
            await service.register(req)
            await session.commit()
            print("Success")
        except Exception:
            traceback.print_exc()

asyncio.run(main())
