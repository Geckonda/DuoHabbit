"""Chat repository."""

from sqlalchemy import and_, case, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from duohabit.models.chat import Conversation, ConversationParticipant, Message
from duohabit.schemas.common import PaginationParams
from duohabit.utils.pagination import apply_pagination


class ChatRepository:
    """Repository for conversations and messages."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self._session.commit()

    # ========== CONVERSATIONS ==========

    async def get_conversation(self, conversation_id: int) -> Conversation | None:
        """Get a conversation by ID."""
        stmt = (
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(selectinload(Conversation.participants))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_direct_conversation(
        self, user_a_id: int, user_b_id: int
    ) -> Conversation | None:
        """
        Find the one-to-one conversation between two users.

        Matches only conversations with exactly these two participants,
        so a future group chat containing both is never returned here.
        """
        pair = [user_a_id, user_b_id]
        matched = func.count(
            distinct(
                case(
                    (
                        ConversationParticipant.user_id.in_(pair),
                        ConversationParticipant.user_id,
                    )
                )
            )
        )

        stmt = (
            select(ConversationParticipant.conversation_id)
            .group_by(ConversationParticipant.conversation_id)
            .having(func.count() == 2)
            .having(matched == 2)
            .limit(1)
        )
        result = await self._session.execute(stmt)
        conversation_id = result.scalar_one_or_none()

        if conversation_id is None:
            return None

        return await self.get_conversation(conversation_id)

    async def create_conversation(
        self, user_ids: list[int], initiator_id: int
    ) -> Conversation:
        """Create a conversation with the given participants, starting out pending."""
        conversation = Conversation(
            status="pending",
            initiator_id=initiator_id,
            participants=[
                ConversationParticipant(user_id=user_id) for user_id in user_ids
            ],
        )
        self._session.add(conversation)
        await self._session.flush()
        await self._session.refresh(conversation, attribute_names=["participants"])
        return conversation

    async def accept_conversation(self, conversation: Conversation) -> Conversation:
        """Accept a pending request - both sides can message freely from here on."""
        conversation.status = "accepted"
        await self._session.flush()
        await self._session.refresh(conversation)
        return conversation

    async def delete_conversation(self, conversation: Conversation) -> None:
        """Decline a pending request - the whole conversation (and its messages) is gone."""
        await self._session.delete(conversation)
        await self._session.flush()

    async def list_conversations(
        self, user_id: int, pagination: PaginationParams | None = None
    ) -> list[Conversation]:
        """List conversations the user takes part in, freshest first."""
        stmt = (
            select(Conversation)
            .join(
                ConversationParticipant,
                ConversationParticipant.conversation_id == Conversation.id,
            )
            .where(ConversationParticipant.user_id == user_id)
            .options(selectinload(Conversation.participants))
            .order_by(
                Conversation.last_message_at.desc().nullslast(),
                Conversation.id.desc(),
            )
        )

        if pagination is not None:
            stmt = apply_pagination(stmt, pagination)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ========== PARTICIPANTS ==========

    async def get_participant(
        self, conversation_id: int, user_id: int
    ) -> ConversationParticipant | None:
        """Get a participant row. Doubles as the access check."""
        stmt = select(ConversationParticipant).where(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def set_last_read(
        self, participant: ConversationParticipant, message_id: int
    ) -> ConversationParticipant:
        """
        Move the read position forward.

        Never backwards: two tabs reading at once must not un-read the dialog.
        """
        current = participant.last_read_message_id or 0
        if message_id > current:
            participant.last_read_message_id = message_id
            await self._session.flush()
            await self._session.refresh(participant)
        return participant

    # ========== MESSAGES ==========

    async def create_message(
        self, conversation: Conversation, sender_id: int, text: str
    ) -> Message:
        """Store a message and bump the conversation's freshness marker."""
        message = Message(
            conversation_id=conversation.id,
            sender_id=sender_id,
            text=text,
        )
        self._session.add(message)
        await self._session.flush()
        await self._session.refresh(message)

        conversation.last_message_at = message.created_at
        await self._session.flush()

        return message

    async def get_message(self, message_id: int) -> Message | None:
        """Get a single message by ID."""
        stmt = select(Message).where(Message.id == message_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_messages(
        self, conversation_id: int, before_id: int | None = None, limit: int = 50
    ) -> list[Message]:
        """Get a page of messages, newest first, older than the cursor."""
        stmt = select(Message).where(Message.conversation_id == conversation_id)

        if before_id is not None:
            stmt = stmt.where(Message.id < before_id)

        stmt = stmt.order_by(Message.id.desc()).limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_last_messages(
        self, conversation_ids: list[int]
    ) -> dict[int, Message]:
        """Get the newest message of every given conversation in one query."""
        if not conversation_ids:
            return {}

        stmt = (
            select(Message)
            .where(Message.conversation_id.in_(conversation_ids))
            .distinct(Message.conversation_id)
            .order_by(Message.conversation_id, Message.id.desc())
        )
        result = await self._session.execute(stmt)
        return {message.conversation_id: message for message in result.scalars().all()}

    async def unread_counts(self, user_id: int) -> dict[int, int]:
        """
        Count unread messages per conversation for a user in one query.

        Conversations with nothing unread are simply absent from the result.
        """
        stmt = (
            select(
                ConversationParticipant.conversation_id,
                func.count(Message.id),
            )
            .join(
                Message,
                and_(
                    Message.conversation_id
                    == ConversationParticipant.conversation_id,
                    Message.sender_id != user_id,
                    Message.id
                    > func.coalesce(ConversationParticipant.last_read_message_id, 0),
                ),
            )
            .where(ConversationParticipant.user_id == user_id)
            .group_by(ConversationParticipant.conversation_id)
        )
        result = await self._session.execute(stmt)
        return {row[0]: row[1] for row in result.all()}
