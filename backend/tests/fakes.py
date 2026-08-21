"""
In-memory doubles for the repositories.

Сервисы - это бизнес-логика поверх репозиториев, поэтому проверяем именно ее,
не поднимая PostgreSQL. Фейки повторяют наблюдаемое поведение настоящих
репозиториев: те же сортировки, те же исключения, тот же счетчик коммитов
(сервисы обязаны коммитить, репозитории - нет).
"""

from datetime import date, datetime, timedelta, timezone
from typing import cast

from duohabit.models.chat import Conversation, ConversationParticipant, Message
from duohabit.models.habits import Habit, HabitCheck, HabitType
from duohabit.models.push import PushSubscription
from duohabit.models.users import User
from duohabit.repositories.chat import ChatRepository
from duohabit.repositories.habits import HabitRepository
from duohabit.repositories.push import PushRepository
from duohabit.repositories.users import UsersRepository
from duohabit.schemas.common import PaginationParams


def make_user(
    user_id: int,
    username: str = "user",
    email: str | None = None,
    is_platform_admin: bool = False,
) -> User:
    """Build a transient User model for tests."""
    return User(
        id=user_id,
        email=email or f"{username}@duohabit.com",
        username=username,
        hashed_password="hashed",
        is_platform_admin=is_platform_admin,
        is_active=True,
        is_superuser=False,
        is_verified=False,
    )


class FakeChatRepository:
    """In-memory stand-in for ChatRepository."""

    def __init__(self) -> None:
        self.conversations: dict[int, Conversation] = {}
        self.messages: list[Message] = []
        self.commits = 0
        self._next_conversation_id = 1
        self._next_message_id = 1

    async def commit(self) -> None:
        """Count commits so tests can assert services persist their work."""
        self.commits += 1

    # ========== CONVERSATIONS ==========

    async def get_conversation(self, conversation_id: int) -> Conversation | None:
        """Get a conversation by ID."""
        return self.conversations.get(conversation_id)

    async def get_direct_conversation(
        self, user_a_id: int, user_b_id: int
    ) -> Conversation | None:
        """Find a conversation with exactly these two participants."""
        pair = {user_a_id, user_b_id}
        for conversation in self.conversations.values():
            members = {p.user_id for p in conversation.participants}
            if members == pair and len(conversation.participants) == 2:
                return conversation
        return None

    async def create_conversation(
        self, user_ids: list[int], initiator_id: int
    ) -> Conversation:
        """Create a conversation with the given participants, starting out pending."""
        conversation = Conversation(
            id=self._next_conversation_id,
            last_message_at=None,
            status="pending",
            initiator_id=initiator_id,
            participants=[
                ConversationParticipant(
                    id=self._next_conversation_id * 100 + index,
                    conversation_id=self._next_conversation_id,
                    user_id=user_id,
                    last_read_message_id=None,
                )
                for index, user_id in enumerate(user_ids)
            ],
        )
        self.conversations[conversation.id] = conversation
        self._next_conversation_id += 1
        return conversation

    async def accept_conversation(self, conversation: Conversation) -> Conversation:
        """Accept a pending request."""
        conversation.status = "accepted"
        return conversation

    async def delete_conversation(self, conversation: Conversation) -> None:
        """Decline a pending request - the conversation and its messages are gone."""
        self.conversations.pop(conversation.id, None)
        self.messages = [
            message for message in self.messages if message.conversation_id != conversation.id
        ]

    async def list_conversations(
        self, user_id: int, pagination: PaginationParams | None = None
    ) -> list[Conversation]:
        """List the user's conversations, freshest first."""
        mine = [
            conversation
            for conversation in self.conversations.values()
            if any(p.user_id == user_id for p in conversation.participants)
        ]

        # Порядок как в SQL: last_message_at DESC NULLS LAST, затем id DESC
        epoch = datetime.min.replace(tzinfo=timezone.utc)
        mine.sort(
            key=lambda c: (c.last_message_at or epoch, c.id),
            reverse=True,
        )

        if pagination is not None:
            mine = mine[pagination.offset : pagination.offset + pagination.limit]

        return mine

    # ========== PARTICIPANTS ==========

    async def get_participant(
        self, conversation_id: int, user_id: int
    ) -> ConversationParticipant | None:
        """Get a participant row."""
        conversation = self.conversations.get(conversation_id)
        if conversation is None:
            return None

        for participant in conversation.participants:
            if participant.user_id == user_id:
                return participant
        return None

    async def set_last_read(
        self, participant: ConversationParticipant, message_id: int
    ) -> ConversationParticipant:
        """Move the read position forward only."""
        current = participant.last_read_message_id or 0
        if message_id > current:
            participant.last_read_message_id = message_id
        return participant

    # ========== MESSAGES ==========

    async def create_message(
        self, conversation: Conversation, sender_id: int, text: str
    ) -> Message:
        """Store a message and bump the conversation freshness marker."""
        message = Message(
            id=self._next_message_id,
            conversation_id=conversation.id,
            sender_id=sender_id,
            text=text,
            created_at=datetime.now(timezone.utc),
        )
        self._next_message_id += 1
        self.messages.append(message)
        conversation.last_message_at = message.created_at
        return message

    async def get_message(self, message_id: int) -> Message | None:
        """Get a message by ID."""
        for message in self.messages:
            if message.id == message_id:
                return message
        return None

    async def get_messages(
        self, conversation_id: int, before_id: int | None = None, limit: int = 50
    ) -> list[Message]:
        """Get a page of messages, newest first."""
        found = [m for m in self.messages if m.conversation_id == conversation_id]

        if before_id is not None:
            found = [m for m in found if m.id < before_id]

        found.sort(key=lambda m: m.id, reverse=True)
        return found[:limit]

    async def get_last_messages(
        self, conversation_ids: list[int]
    ) -> dict[int, Message]:
        """Get the newest message of every given conversation."""
        last: dict[int, Message] = {}
        for message in sorted(self.messages, key=lambda m: m.id):
            if message.conversation_id in conversation_ids:
                last[message.conversation_id] = message
        return last

    async def unread_counts(self, user_id: int) -> dict[int, int]:
        """Count unread messages per conversation."""
        counts: dict[int, int] = {}

        for conversation in self.conversations.values():
            participant = None
            for item in conversation.participants:
                if item.user_id == user_id:
                    participant = item
                    break

            if participant is None:
                continue

            border = participant.last_read_message_id or 0
            unread = sum(
                1
                for message in self.messages
                if message.conversation_id == conversation.id
                and message.sender_id != user_id
                and message.id > border
            )

            if unread:
                counts[conversation.id] = unread

        return counts


class FakeHabitRepository:
    """In-memory stand-in for HabitRepository."""

    def __init__(self) -> None:
        self.habits: dict[int, Habit] = {}
        self.checks: list[HabitCheck] = []
        self.commits = 0
        self._next_habit_id = 1
        self._next_check_id = 1

    async def commit(self) -> None:
        """Count commits so tests can assert services persist their work."""
        self.commits += 1

    async def create(
        self,
        user_id: int,
        title: str,
        description: str | None = None,
        habit_type: HabitType = HabitType.DAILY,
    ) -> Habit:
        """Create a habit."""
        habit = Habit(
            id=self._next_habit_id,
            user_id=user_id,
            title=title,
            description=description,
            habit_type=(
                habit_type.value if isinstance(habit_type, HabitType) else habit_type
            ),
            current_streak=0,
            is_active=True,
            is_private=True,
        )
        self.habits[habit.id] = habit
        self._next_habit_id += 1
        return habit

    async def get_by_user(self, user_id: int, only_active: bool = True) -> list[Habit]:
        """Get the user's habits."""
        found = [h for h in self.habits.values() if h.user_id == user_id]
        if only_active:
            found = [h for h in found if h.is_active]
        return sorted(found, key=lambda h: h.id)

    async def get_by_id(
        self, habit_id: int, user_id: int, load_checks: bool = False
    ) -> Habit | None:
        """Get a habit scoped to its owner."""
        habit = self.habits.get(habit_id)
        if habit is None or habit.user_id != user_id:
            return None

        if load_checks:
            habit.checks = [c for c in self.checks if c.habit_id == habit_id]

        return habit

    async def update(self, habit: Habit, **kwargs: object) -> Habit:
        """Update habit fields, ignoring attempts to change the owner."""
        kwargs.pop("user_id", None)
        for key, value in kwargs.items():
            if hasattr(habit, key):
                setattr(habit, key, value)
        return habit

    async def delete(self, habit: Habit) -> None:
        """Delete a habit."""
        self.habits.pop(habit.id, None)

    async def archive(self, habit: Habit) -> Habit:
        """Archive a habit."""
        habit.is_active = False
        return habit

    async def restore(self, habit: Habit) -> Habit:
        """Restore a habit."""
        habit.is_active = True
        return habit

    # ========== CHECKS ==========

    async def create_check(
        self, habit_id: int, check_date: date | None = None
    ) -> HabitCheck:
        """Create a check, rejecting a second one for the same day."""
        if check_date is None:
            check_date = date.today()

        existing = await self.get_check_by_date(habit_id, check_date)
        if existing:
            raise ValueError(f"Check for {check_date} already exists")

        check = HabitCheck(
            id=self._next_check_id,
            habit_id=habit_id,
            check_date=check_date,
            created_at=datetime.now(timezone.utc),
        )
        self._next_check_id += 1
        self.checks.append(check)
        return check

    async def get_check_by_id(self, check_id: int) -> HabitCheck | None:
        """Get a check by ID."""
        for check in self.checks:
            if check.id == check_id:
                return check
        return None

    async def get_check_by_date(
        self, habit_id: int, check_date: date
    ) -> HabitCheck | None:
        """Get a check for a specific habit and day."""
        for check in self.checks:
            if check.habit_id == habit_id and check.check_date == check_date:
                return check
        return None

    async def get_checks(
        self, habit_id: int, limit: int = 30, offset: int = 0
    ) -> list[HabitCheck]:
        """Get checks, newest first."""
        found = [c for c in self.checks if c.habit_id == habit_id]
        found.sort(key=lambda c: c.check_date, reverse=True)
        return found[offset : offset + limit]

    async def delete_check(self, check_id: int) -> None:
        """Delete a check."""
        self.checks = [c for c in self.checks if c.id != check_id]

    def add_checks(self, habit_id: int, days_ago: list[int]) -> None:
        """Seed checks relative to today. Helper, not part of the repository API."""
        today = date.today()
        for offset in days_ago:
            self.checks.append(
                HabitCheck(
                    id=self._next_check_id,
                    habit_id=habit_id,
                    check_date=today - timedelta(days=offset),
                    created_at=datetime.now(timezone.utc),
                )
            )
            self._next_check_id += 1


class FakeUsersRepository:
    """In-memory stand-in for UsersRepository."""

    def __init__(self, users: list[User] | None = None) -> None:
        self.users: dict[int, User] = {user.id: user for user in (users or [])}
        self.commits = 0

    async def commit(self) -> None:
        """Count commits."""
        self.commits += 1

    async def get_user(self, user_id: int) -> User | None:
        """Get a user by ID."""
        return self.users.get(user_id)

    async def get_users_by_ids(self, user_ids: list[int]) -> list[User]:
        """Get several users at once."""
        return [self.users[uid] for uid in user_ids if uid in self.users]

    async def get_users(self, pagination: PaginationParams | None = None) -> list[User]:
        """Get all users ordered by id."""
        found = sorted(self.users.values(), key=lambda u: u.id)
        if pagination is not None:
            found = found[pagination.offset : pagination.offset + pagination.limit]
        return found

    async def get_user_by_email(self, email: str) -> User | None:
        """Get a user by email."""
        for user in self.users.values():
            if user.email == email:
                return user
        return None


class FakePushRepository:
    """In-memory stand-in for PushRepository."""

    def __init__(self) -> None:
        self.subscriptions: dict[str, PushSubscription] = {}
        self.commits = 0
        self._next_id = 1

    async def commit(self) -> None:
        """Count commits so tests can assert services persist their work."""
        self.commits += 1

    async def get_by_endpoint(self, endpoint: str) -> PushSubscription | None:
        """Get a subscription by its push-service endpoint."""
        return self.subscriptions.get(endpoint)

    async def upsert(
        self, user_id: int, endpoint: str, p256dh: str, auth: str
    ) -> PushSubscription:
        """Create or refresh a subscription by endpoint."""
        subscription = self.subscriptions.get(endpoint)
        if subscription is None:
            subscription = PushSubscription(
                id=self._next_id, user_id=user_id, endpoint=endpoint, p256dh=p256dh, auth=auth
            )
            self._next_id += 1
        else:
            subscription.user_id = user_id
            subscription.p256dh = p256dh
            subscription.auth = auth
        self.subscriptions[endpoint] = subscription
        return subscription

    async def delete_by_endpoint(self, user_id: int, endpoint: str) -> None:
        """Remove a subscription, scoped to its owner."""
        subscription = self.subscriptions.get(endpoint)
        if subscription is not None and subscription.user_id == user_id:
            del self.subscriptions[endpoint]

    async def delete(self, subscription: PushSubscription) -> None:
        """Remove a subscription."""
        self.subscriptions.pop(subscription.endpoint, None)

    async def get_by_users(self, user_ids: list[int]) -> list[PushSubscription]:
        """Get every subscription belonging to any of the given users."""
        ids = set(user_ids)
        return [sub for sub in self.subscriptions.values() if sub.user_id in ids]


# Сервисы типизированы настоящими репозиториями, а фейки повторяют только их
# поведение. Приведение типа держится в одном месте, чтобы не засорять тесты.


def as_chat_repo(fake: FakeChatRepository) -> ChatRepository:
    """Pass a fake where the service expects a ChatRepository."""
    return cast(ChatRepository, fake)


def as_habit_repo(fake: FakeHabitRepository) -> HabitRepository:
    """Pass a fake where the service expects a HabitRepository."""
    return cast(HabitRepository, fake)


def as_users_repo(fake: FakeUsersRepository) -> UsersRepository:
    """Pass a fake where the service expects a UsersRepository."""
    return cast(UsersRepository, fake)


def as_push_repo(fake: FakePushRepository) -> PushRepository:
    """Pass a fake where the service expects a PushRepository."""
    return cast(PushRepository, fake)
