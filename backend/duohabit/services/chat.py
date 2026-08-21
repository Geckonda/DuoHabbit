"""Chat business logic."""

from duohabit.models.chat import Conversation, Message
from duohabit.models.users import User
from duohabit.repositories.chat import ChatRepository
from duohabit.repositories.users import UsersRepository
from duohabit.schemas.chat import ConversationRead, MessageCreate, MessageRead
from duohabit.schemas.common import PaginationParams
from duohabit.services.users import user_model_to_schema


class ChatError(Exception):
    """Base class for chat errors."""


class ChatNotFoundError(ChatError):
    """
    The requested entity does not exist, or the caller may not see it.

    Deliberately also raised for non-participants: otherwise the status code
    would tell a stranger whether a conversation exists.
    """


class ChatValidationError(ChatError):
    """The request does not make sense, e.g. a conversation with oneself."""


def message_model_to_schema(message_model: Message) -> MessageRead:
    """Convert a Message model to its schema."""
    return MessageRead(
        id=message_model.id,
        conversation_id=message_model.conversation_id,
        sender_id=message_model.sender_id,
        text=message_model.text,
        created_at=message_model.created_at,
    )


def conversation_model_to_schema(
    conversation_model: Conversation,
    companion: User,
    last_message: Message | None = None,
    unread_count: int = 0,
) -> ConversationRead:
    """Convert a Conversation model to its schema for one participant's view."""
    return ConversationRead(
        id=conversation_model.id,
        companion=user_model_to_schema(companion),
        last_message=(
            message_model_to_schema(last_message) if last_message is not None else None
        ),
        unread_count=unread_count,
        status=conversation_model.status,
        initiator_id=conversation_model.initiator_id,
    )


def _companion_id(conversation: Conversation, user_id: int) -> int | None:
    """Get the id of the other party in a conversation."""
    for participant in conversation.participants:
        if participant.user_id != user_id:
            return participant.user_id
    return None


async def _get_conversation_for_user(
    repo: ChatRepository, conversation_id: int, user_id: int
) -> Conversation:
    """Load a conversation, ensuring the caller takes part in it."""
    conversation = await repo.get_conversation(conversation_id)
    if conversation is None:
        raise ChatNotFoundError("Conversation not found")

    participant = await repo.get_participant(conversation_id, user_id)
    if participant is None:
        raise ChatNotFoundError("Conversation not found")

    return conversation


async def open_direct_conversation(
    repo: ChatRepository,
    users_repo: UsersRepository,
    user_id: int,
    companion_id: int,
) -> ConversationRead:
    """Get the existing one-to-one conversation with a user, or start one."""
    if companion_id == user_id:
        raise ChatValidationError("Cannot start a conversation with yourself")

    companion = await users_repo.get_user(companion_id)
    if companion is None:
        raise ChatNotFoundError("User not found")

    conversation = await repo.get_direct_conversation(user_id, companion_id)

    if conversation is None:
        conversation = await repo.create_conversation(
            [user_id, companion_id], initiator_id=user_id
        )
        await repo.commit()
        return conversation_model_to_schema(conversation, companion)

    last_messages = await repo.get_last_messages([conversation.id])
    unread = await repo.unread_counts(user_id)

    return conversation_model_to_schema(
        conversation,
        companion,
        last_messages.get(conversation.id),
        unread.get(conversation.id, 0),
    )


async def list_conversations(
    repo: ChatRepository,
    users_repo: UsersRepository,
    user_id: int,
    pagination: PaginationParams | None = None,
) -> list[ConversationRead]:
    """List the user's conversations, freshest first."""
    conversations = await repo.list_conversations(user_id, pagination)
    if not conversations:
        return []

    conversation_ids = [conversation.id for conversation in conversations]
    companion_ids = {
        companion_id
        for companion_id in (
            _companion_id(conversation, user_id) for conversation in conversations
        )
        if companion_id is not None
    }

    companions = {
        companion.id: companion
        for companion in await users_repo.get_users_by_ids(list(companion_ids))
    }
    last_messages = await repo.get_last_messages(conversation_ids)
    unread = await repo.unread_counts(user_id)

    result: list[ConversationRead] = []
    for conversation in conversations:
        companion_id = _companion_id(conversation, user_id)
        companion = companions.get(companion_id) if companion_id is not None else None
        if companion is None:
            # Собеседника удалили - показывать диалог не с кем
            continue

        result.append(
            conversation_model_to_schema(
                conversation,
                companion,
                last_messages.get(conversation.id),
                unread.get(conversation.id, 0),
            )
        )

    return result


async def get_messages(
    repo: ChatRepository,
    user_id: int,
    conversation_id: int,
    before_id: int | None = None,
    limit: int = 50,
) -> list[MessageRead]:
    """Get a page of conversation history, oldest first within the page."""
    await _get_conversation_for_user(repo, conversation_id, user_id)

    messages = await repo.get_messages(conversation_id, before_id=before_id, limit=limit)

    # Репозиторий отдает свежие сверху для курсора, клиенту удобнее хронология
    return [message_model_to_schema(message) for message in reversed(messages)]


async def send_message(
    repo: ChatRepository,
    user_id: int,
    conversation_id: int,
    message_data: MessageCreate,
) -> tuple[MessageRead, list[int]]:
    """
    Store a message in a conversation.

    Returns the message together with the ids of everyone who should receive it,
    so the router can broadcast without loading the participants again.
    """
    conversation = await _get_conversation_for_user(repo, conversation_id, user_id)

    if conversation.status == "pending" and conversation.initiator_id != user_id:
        # Пока не принято, отвечать может только тот, кто открыл диалог -
        # получатель пока может только читать
        raise ChatValidationError("Accept the request before replying")

    text = message_data.text.strip()
    if not text:
        raise ChatValidationError("Message text cannot be empty")

    message = await repo.create_message(conversation, sender_id=user_id, text=text)
    await repo.commit()

    # Пока pending, доставка идет только самому отправителю (синхронизация его
    # вкладок) - собеседник ничего не увидит и не получит пуш, пока не примет
    recipient_ids = (
        [participant.user_id for participant in conversation.participants]
        if conversation.status == "accepted"
        else [user_id]
    )

    return message_model_to_schema(message), recipient_ids


async def accept_conversation(
    repo: ChatRepository,
    users_repo: UsersRepository,
    conversation_id: int,
    user_id: int,
) -> ConversationRead:
    """Accept a pending request - both sides can message freely from here on."""
    conversation = await _get_conversation_for_user(repo, conversation_id, user_id)

    if conversation.status != "pending":
        raise ChatValidationError("Conversation is not pending")
    if conversation.initiator_id == user_id:
        raise ChatValidationError("Cannot accept your own request")

    companion_id = _companion_id(conversation, user_id)
    companion = await users_repo.get_user(companion_id) if companion_id else None
    if companion is None:
        raise ChatNotFoundError("User not found")

    await repo.accept_conversation(conversation)
    await repo.commit()

    return conversation_model_to_schema(conversation, companion)


async def decline_conversation(
    repo: ChatRepository, conversation_id: int, user_id: int
) -> int:
    """
    Decline a pending request - the whole conversation disappears for both sides.

    Returns the initiator's id, so the router can tell their live tabs it's gone.
    """
    conversation = await _get_conversation_for_user(repo, conversation_id, user_id)

    if conversation.status != "pending":
        raise ChatValidationError("Conversation is not pending")
    if conversation.initiator_id == user_id:
        raise ChatValidationError("Cannot decline your own request")

    initiator_id = conversation.initiator_id
    await repo.delete_conversation(conversation)
    await repo.commit()

    return initiator_id


async def mark_read(
    repo: ChatRepository,
    user_id: int,
    conversation_id: int,
    message_id: int,
) -> tuple[int, list[int]]:
    """
    Mark the conversation read up to a message.

    Returns the resulting read position and the ids of everyone to notify.
    """
    conversation = await _get_conversation_for_user(repo, conversation_id, user_id)

    message = await repo.get_message(message_id)
    if message is None or message.conversation_id != conversation_id:
        # Иначе чужим или выдуманным id можно было бы обнулить свои непрочитанные
        raise ChatValidationError("Message does not belong to this conversation")

    participant = await repo.get_participant(conversation_id, user_id)
    if participant is None:
        raise ChatNotFoundError("Conversation not found")

    updated = await repo.set_last_read(participant, message_id)
    await repo.commit()

    recipient_ids = [item.user_id for item in conversation.participants]

    return updated.last_read_message_id or 0, recipient_ids
