"""Chat API routes."""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi_users.authentication.strategy.db import DatabaseStrategy
from sqlalchemy.ext.asyncio import AsyncSession

from duohabit.auth import get_db_strategy, get_token_claim, get_user_manager
from duohabit.chat_hub import hub
from duohabit.db import get_session
from duohabit.models.auth import AccessToken
from duohabit.models.users import User
from duohabit.repositories.chat import ChatRepository
from duohabit.repositories.users import UsersRepository
from duohabit.schemas.auth import AccessTokenClaim
from duohabit.schemas.chat import (
    ConversationCreate,
    ConversationRead,
    MarkReadRequest,
    MessageCreate,
    MessageRead,
)
from duohabit.schemas.common import PaginationParams
from duohabit.services.chat import (
    ChatError,
    ChatValidationError,
    accept_conversation,
    decline_conversation,
    get_messages,
    list_conversations,
    mark_read,
    open_direct_conversation,
    send_message,
)
from duohabit.services.notifications import NotificationPayload, notify_if_offline
from duohabit.services.users import UserManager

MESSAGE_PREVIEW_LIMIT = 120

chat_router = APIRouter(prefix="/chat", tags=["Chat"])


def _http_error(error: ChatError) -> HTTPException:
    """Convert a chat error into its HTTP counterpart."""
    if isinstance(error, ChatValidationError):
        return HTTPException(status_code=400, detail=str(error))
    return HTTPException(status_code=404, detail=str(error))


@chat_router.post("/conversations", response_model=ConversationRead)
async def open_conversation_endpoint(
    conversation_data: ConversationCreate,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> ConversationRead:
    """
    Open a one-to-one conversation with another user.

    Idempotent: an existing dialog is returned instead of a second one.
    """
    try:
        return await open_direct_conversation(
            repo=ChatRepository(session),
            users_repo=UsersRepository(session),
            user_id=token_claim.user_id,
            companion_id=conversation_data.user_id,
        )
    except ChatError as error:
        raise _http_error(error) from error


@chat_router.get("/conversations", response_model=list[ConversationRead])
async def list_conversations_endpoint(
    pagination: PaginationParams = Depends(),
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> list[ConversationRead]:
    """List the current user's conversations, freshest first."""
    return await list_conversations(
        repo=ChatRepository(session),
        users_repo=UsersRepository(session),
        user_id=token_claim.user_id,
        pagination=pagination,
    )


@chat_router.get(
    "/conversations/{conversation_id}/messages", response_model=list[MessageRead]
)
async def get_messages_endpoint(
    conversation_id: int,
    before_id: int | None = Query(None, description="Return messages older than this"),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> list[MessageRead]:
    """Get a page of conversation history, oldest first within the page."""
    try:
        return await get_messages(
            repo=ChatRepository(session),
            user_id=token_claim.user_id,
            conversation_id=conversation_id,
            before_id=before_id,
            limit=limit,
        )
    except ChatError as error:
        raise _http_error(error) from error


@chat_router.post(
    "/conversations/{conversation_id}/messages", response_model=MessageRead
)
async def send_message_endpoint(
    conversation_id: int,
    message_data: MessageCreate,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> MessageRead:
    """Send a message and push it to everyone connected to the conversation."""
    try:
        message, recipient_ids = await send_message(
            repo=ChatRepository(session),
            user_id=token_claim.user_id,
            conversation_id=conversation_id,
            message_data=message_data,
        )
    except ChatError as error:
        raise _http_error(error) from error

    # Строго после коммита в сервисе: иначе собеседник получит сообщение,
    # которого еще нет в базе. Отправитель тоже в списке - синхронизируем его вкладки
    await hub.broadcast(
        recipient_ids,
        {
            "type": "message",
            "conversation_id": conversation_id,
            "message": message.model_dump(mode="json"),
        },
    )

    sender = await UsersRepository(session).get_user(token_claim.user_id)
    preview = (
        message.text
        if len(message.text) <= MESSAGE_PREVIEW_LIMIT
        else message.text[: MESSAGE_PREVIEW_LIMIT - 3] + "..."
    )
    # Себя из адресатов исключаем явно: notify_if_offline судит по hub.is_online(),
    # а не по тому, кто прислал этот самый запрос - живого сокета может не быть
    await notify_if_offline(
        session,
        [recipient_id for recipient_id in recipient_ids if recipient_id != token_claim.user_id],
        NotificationPayload(
            title=sender.username if sender else "DuoHabit",
            body=preview,
            url=f"/chats/{conversation_id}",
            tag=f"chat-{conversation_id}",
        ),
    )

    return message


@chat_router.post("/conversations/{conversation_id}/accept", response_model=ConversationRead)
async def accept_conversation_endpoint(
    conversation_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> ConversationRead:
    """Accept a pending chat request - both sides can message freely from here on."""
    try:
        result = await accept_conversation(
            repo=ChatRepository(session),
            users_repo=UsersRepository(session),
            conversation_id=conversation_id,
            user_id=token_claim.user_id,
        )
    except ChatError as error:
        raise _http_error(error) from error

    # Живым вкладкам обеих сторон - иначе у инициатора статус "Ожидает ответа"
    # зависает, пока он не перезайдет вручную
    await hub.broadcast(
        [result.initiator_id, token_claim.user_id],
        {
            "type": "conversation_accepted",
            "conversation": result.model_dump(mode="json"),
        },
    )

    acceptor = await UsersRepository(session).get_user(token_claim.user_id)
    await notify_if_offline(
        session,
        [result.initiator_id],
        NotificationPayload(
            title="Запрос принят",
            body=f"{acceptor.username if acceptor else 'Собеседник'} принял твой запрос на переписку",
            url=f"/chats/{conversation_id}",
            tag=f"chat-accepted-{conversation_id}",
        ),
    )

    return result


@chat_router.post("/conversations/{conversation_id}/decline", status_code=204)
async def decline_conversation_endpoint(
    conversation_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> None:
    """Decline a pending chat request - the whole conversation is gone for both sides."""
    try:
        initiator_id = await decline_conversation(
            repo=ChatRepository(session),
            conversation_id=conversation_id,
            user_id=token_claim.user_id,
        )
    except ChatError as error:
        raise _http_error(error) from error

    await hub.broadcast(
        [initiator_id, token_claim.user_id],
        {"type": "conversation_declined", "conversation_id": conversation_id},
    )


@chat_router.post("/conversations/{conversation_id}/read", status_code=204)
async def mark_read_endpoint(
    conversation_id: int,
    read_data: MarkReadRequest,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> None:
    """Mark the conversation read up to a message."""
    try:
        message_id, recipient_ids = await mark_read(
            repo=ChatRepository(session),
            user_id=token_claim.user_id,
            conversation_id=conversation_id,
            message_id=read_data.message_id,
        )
    except ChatError as error:
        raise _http_error(error) from error

    await hub.broadcast(
        recipient_ids,
        {
            "type": "read",
            "conversation_id": conversation_id,
            "user_id": token_claim.user_id,
            "message_id": message_id,
        },
    )


@chat_router.websocket("/ws")
async def chat_socket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(None),
    user_manager: UserManager = Depends(get_user_manager),
    strategy: DatabaseStrategy[User, int, AccessToken] = Depends(get_db_strategy),
) -> None:
    """
    Delivery channel for chat events.

    The token travels in the query string because a browser WebSocket cannot set
    the Authorization header that BearerTransport expects. Validation reuses the
    same database strategy as the REST endpoints.
    """
    user = await strategy.read_token(token, user_manager)

    if user is None:
        # Принимаем и закрываем с 1008, чтобы клиент отличил протухший токен
        # от обрыва сети и не уходил в бесконечный реконнект
        await websocket.accept()
        await websocket.close(code=1008)
        return

    await hub.connect(user.id, websocket)
    try:
        while True:
            # Канал работает только на доставку, входящие кадры не нужны.
            # Но читать обязательно: иначе разрыв соединения не будет замечен
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        hub.disconnect(user.id, websocket)
