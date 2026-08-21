"""Tests for the chat business logic."""

import pytest

from duohabit.schemas.chat import MessageCreate
from duohabit.services.chat import (
    ChatNotFoundError,
    ChatValidationError,
    accept_conversation,
    decline_conversation,
    get_messages,
    list_conversations,
    mark_read,
    open_direct_conversation,
    send_message,
)
from tests.fakes import (
    FakeChatRepository,
    FakeUsersRepository,
    as_chat_repo,
    as_users_repo,
    make_user,
)

ALICE = 1
BOB = 2
EVE = 3


def build_repos() -> tuple[FakeChatRepository, FakeUsersRepository]:
    """Two known users and an empty chat store."""
    users = FakeUsersRepository(
        [
            make_user(ALICE, "alice"),
            make_user(BOB, "bob"),
            make_user(EVE, "eve"),
        ]
    )
    return FakeChatRepository(), users


async def seed_conversation(
    chat: FakeChatRepository, users: FakeUsersRepository
) -> int:
    """Open a dialog between alice and bob, already accepted, return its id."""
    conversation = await open_direct_conversation(
        as_chat_repo(chat), as_users_repo(users), ALICE, BOB
    )
    await accept_conversation(as_chat_repo(chat), as_users_repo(users), conversation.id, BOB)
    return conversation.id


# ========== OPEN CONVERSATION ==========


@pytest.mark.asyncio(loop_scope="session")
async def test_open_conversation_creates_and_commits() -> None:
    """A first dialog is created, persisted and returned with the companion."""
    chat, users = build_repos()

    conversation = await open_direct_conversation(
        as_chat_repo(chat), as_users_repo(users), ALICE, BOB
    )

    assert conversation.companion.username == "bob"
    assert conversation.unread_count == 0
    assert conversation.last_message is None
    assert conversation.status == "pending"
    assert conversation.initiator_id == ALICE
    assert chat.commits == 1


@pytest.mark.asyncio(loop_scope="session")
async def test_open_conversation_is_idempotent() -> None:
    """Opening the same dialog twice must not create a second one."""
    chat, users = build_repos()

    first = await open_direct_conversation(
        as_chat_repo(chat), as_users_repo(users), ALICE, BOB
    )
    second = await open_direct_conversation(
        as_chat_repo(chat), as_users_repo(users), ALICE, BOB
    )

    assert first.id == second.id
    assert len(chat.conversations) == 1
    # Второй вызов ничего не создает, значит и коммитить нечего
    assert chat.commits == 1


@pytest.mark.asyncio(loop_scope="session")
async def test_open_conversation_from_the_other_side_returns_same_dialog() -> None:
    """The companion opening the dialog lands in the very same conversation."""
    chat, users = build_repos()

    first = await open_direct_conversation(
        as_chat_repo(chat), as_users_repo(users), ALICE, BOB
    )
    mirrored = await open_direct_conversation(
        as_chat_repo(chat), as_users_repo(users), BOB, ALICE
    )

    assert mirrored.id == first.id
    assert mirrored.companion.username == "alice"


@pytest.mark.asyncio(loop_scope="session")
async def test_open_conversation_returns_state_of_existing_dialog() -> None:
    """An existing dialog comes back with its last message and unread count."""
    chat, users = build_repos()
    conversation_id = await seed_conversation(chat, users)

    await send_message(
        as_chat_repo(chat), BOB, conversation_id, MessageCreate(text="привет")
    )

    conversation = await open_direct_conversation(
        as_chat_repo(chat), as_users_repo(users), ALICE, BOB
    )

    assert conversation.last_message is not None
    assert conversation.last_message.text == "привет"
    assert conversation.unread_count == 1


@pytest.mark.asyncio(loop_scope="session")
async def test_open_conversation_with_self_is_rejected() -> None:
    """Talking to yourself is not a dialog."""
    chat, users = build_repos()

    with pytest.raises(ChatValidationError):
        await open_direct_conversation(
            as_chat_repo(chat), as_users_repo(users), ALICE, ALICE
        )

    assert chat.commits == 0


@pytest.mark.asyncio(loop_scope="session")
async def test_open_conversation_with_unknown_user_is_rejected() -> None:
    """A dialog with a non-existent user cannot be opened."""
    chat, users = build_repos()

    with pytest.raises(ChatNotFoundError):
        await open_direct_conversation(
            as_chat_repo(chat), as_users_repo(users), ALICE, 999
        )

    assert not chat.conversations


# ========== LIST ==========


@pytest.mark.asyncio(loop_scope="session")
async def test_list_conversations_empty() -> None:
    """A user without dialogs gets an empty list, not an error."""
    chat, users = build_repos()

    assert (
        await list_conversations(as_chat_repo(chat), as_users_repo(users), ALICE) == []
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_list_conversations_reports_unread_per_viewer() -> None:
    """Unread counts are personal: the sender has nothing unread."""
    chat, users = build_repos()
    conversation_id = await seed_conversation(chat, users)

    for text in ("раз", "два", "три"):
        await send_message(
            as_chat_repo(chat), BOB, conversation_id, MessageCreate(text=text)
        )

    alice_view = await list_conversations(
        as_chat_repo(chat), as_users_repo(users), ALICE
    )
    bob_view = await list_conversations(as_chat_repo(chat), as_users_repo(users), BOB)

    assert alice_view[0].unread_count == 3
    assert bob_view[0].unread_count == 0
    assert alice_view[0].companion.username == "bob"
    assert bob_view[0].companion.username == "alice"


@pytest.mark.asyncio(loop_scope="session")
async def test_list_conversations_puts_freshest_first() -> None:
    """The dialog with the newest message comes first."""
    chat, users = build_repos()

    first_id = await seed_conversation(chat, users)
    second = await open_direct_conversation(
        as_chat_repo(chat), as_users_repo(users), ALICE, EVE
    )

    await send_message(
        as_chat_repo(chat), ALICE, first_id, MessageCreate(text="старое")
    )
    await send_message(
        as_chat_repo(chat), ALICE, second.id, MessageCreate(text="новое")
    )

    listed = await list_conversations(as_chat_repo(chat), as_users_repo(users), ALICE)

    assert [c.id for c in listed] == [second.id, first_id]


@pytest.mark.asyncio(loop_scope="session")
async def test_list_conversations_skips_dialog_without_companion() -> None:
    """A dialog whose companion is gone is hidden instead of crashing."""
    chat, users = build_repos()
    await seed_conversation(chat, users)

    del users.users[BOB]

    assert (
        await list_conversations(as_chat_repo(chat), as_users_repo(users), ALICE) == []
    )


# ========== HISTORY ==========


@pytest.mark.asyncio(loop_scope="session")
async def test_get_messages_returns_chronological_page() -> None:
    """Within a page messages go oldest first, the way a chat renders them."""
    chat, users = build_repos()
    conversation_id = await seed_conversation(chat, users)

    for text in ("1", "2", "3"):
        await send_message(
            as_chat_repo(chat), ALICE, conversation_id, MessageCreate(text=text)
        )

    history = await get_messages(as_chat_repo(chat), ALICE, conversation_id)

    assert [m.text for m in history] == ["1", "2", "3"]


@pytest.mark.asyncio(loop_scope="session")
async def test_get_messages_cursor_returns_only_older() -> None:
    """The before_id cursor walks backwards through history."""
    chat, users = build_repos()
    conversation_id = await seed_conversation(chat, users)

    for text in ("1", "2", "3", "4"):
        await send_message(
            as_chat_repo(chat), ALICE, conversation_id, MessageCreate(text=text)
        )

    full = await get_messages(as_chat_repo(chat), ALICE, conversation_id)
    older = await get_messages(
        as_chat_repo(chat), ALICE, conversation_id, before_id=full[2].id
    )

    assert [m.text for m in older] == ["1", "2"]


@pytest.mark.asyncio(loop_scope="session")
async def test_get_messages_respects_limit() -> None:
    """A page never exceeds the requested size, keeping the newest messages."""
    chat, users = build_repos()
    conversation_id = await seed_conversation(chat, users)

    for text in ("1", "2", "3", "4", "5"):
        await send_message(
            as_chat_repo(chat), ALICE, conversation_id, MessageCreate(text=text)
        )

    page = await get_messages(as_chat_repo(chat), ALICE, conversation_id, limit=2)

    assert [m.text for m in page] == ["4", "5"]


@pytest.mark.asyncio(loop_scope="session")
async def test_get_messages_hides_foreign_dialog() -> None:
    """An outsider must not learn that the dialog even exists."""
    chat, users = build_repos()
    conversation_id = await seed_conversation(chat, users)

    with pytest.raises(ChatNotFoundError):
        await get_messages(as_chat_repo(chat), EVE, conversation_id)


@pytest.mark.asyncio(loop_scope="session")
async def test_get_messages_of_missing_dialog() -> None:
    """A missing conversation is a plain not-found."""
    chat, _users = build_repos()

    with pytest.raises(ChatNotFoundError):
        await get_messages(as_chat_repo(chat), ALICE, 404)


# ========== SEND ==========


@pytest.mark.asyncio(loop_scope="session")
async def test_send_message_persists_and_lists_recipients() -> None:
    """A sent message is committed and addressed to every participant."""
    chat, users = build_repos()
    conversation_id = await seed_conversation(chat, users)
    commits_before = chat.commits

    message, recipients = await send_message(
        as_chat_repo(chat), ALICE, conversation_id, MessageCreate(text="  привет  ")
    )

    assert message.text == "привет"  # хвостовые пробелы срезаются
    assert message.sender_id == ALICE
    assert set(recipients) == {ALICE, BOB}  # отправитель тоже, ради своих вкладок
    assert chat.commits == commits_before + 1


@pytest.mark.asyncio(loop_scope="session")
async def test_send_message_rejects_whitespace_only() -> None:
    """Pydantic allows a single space, business logic must not."""
    chat, users = build_repos()
    conversation_id = await seed_conversation(chat, users)
    commits_before = chat.commits

    with pytest.raises(ChatValidationError):
        await send_message(
            as_chat_repo(chat), ALICE, conversation_id, MessageCreate(text="   ")
        )

    assert not chat.messages
    assert chat.commits == commits_before


@pytest.mark.asyncio(loop_scope="session")
async def test_send_message_from_outsider_is_rejected() -> None:
    """Someone outside the dialog cannot write into it."""
    chat, users = build_repos()
    conversation_id = await seed_conversation(chat, users)

    with pytest.raises(ChatNotFoundError):
        await send_message(
            as_chat_repo(chat), EVE, conversation_id, MessageCreate(text="подслушиваю")
        )

    assert not chat.messages


# ========== REQUESTS (ACCEPT/DECLINE) ==========


@pytest.mark.asyncio(loop_scope="session")
async def test_recipient_cannot_reply_before_accepting() -> None:
    """The invitee can only read a pending request, not answer it."""
    chat, users = build_repos()
    conversation = await open_direct_conversation(
        as_chat_repo(chat), as_users_repo(users), ALICE, BOB
    )

    with pytest.raises(ChatValidationError):
        await send_message(
            as_chat_repo(chat), BOB, conversation.id, MessageCreate(text="привет")
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_initiator_can_keep_writing_while_pending() -> None:
    """The one who opened the dialog isn't blocked while waiting for a response."""
    chat, users = build_repos()
    conversation = await open_direct_conversation(
        as_chat_repo(chat), as_users_repo(users), ALICE, BOB
    )

    message, recipients = await send_message(
        as_chat_repo(chat), ALICE, conversation.id, MessageCreate(text="привет")
    )

    assert message.text == "привет"
    # Получателю пока ничего не летит - только собственные вкладки отправителя
    assert recipients == [ALICE]


@pytest.mark.asyncio(loop_scope="session")
async def test_accept_conversation_lets_both_sides_message() -> None:
    chat, users = build_repos()
    conversation = await open_direct_conversation(
        as_chat_repo(chat), as_users_repo(users), ALICE, BOB
    )

    accepted = await accept_conversation(
        as_chat_repo(chat), as_users_repo(users), conversation.id, BOB
    )
    assert accepted.status == "accepted"

    _, recipients = await send_message(
        as_chat_repo(chat), BOB, conversation.id, MessageCreate(text="привет и тебе")
    )
    assert set(recipients) == {ALICE, BOB}


@pytest.mark.asyncio(loop_scope="session")
async def test_accept_own_request_is_rejected() -> None:
    """The initiator can't accept their own request."""
    chat, users = build_repos()
    conversation = await open_direct_conversation(
        as_chat_repo(chat), as_users_repo(users), ALICE, BOB
    )

    with pytest.raises(ChatValidationError):
        await accept_conversation(
            as_chat_repo(chat), as_users_repo(users), conversation.id, ALICE
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_decline_conversation_removes_it_entirely() -> None:
    chat, users = build_repos()
    conversation = await open_direct_conversation(
        as_chat_repo(chat), as_users_repo(users), ALICE, BOB
    )
    await send_message(
        as_chat_repo(chat), ALICE, conversation.id, MessageCreate(text="привет")
    )

    await decline_conversation(as_chat_repo(chat), conversation.id, BOB)

    assert await chat.get_conversation(conversation.id) is None
    assert not chat.messages

    # Ничто не мешает открыть диалог заново с чистого листа
    reopened = await open_direct_conversation(
        as_chat_repo(chat), as_users_repo(users), ALICE, BOB
    )
    assert reopened.id != conversation.id
    assert reopened.status == "pending"


@pytest.mark.asyncio(loop_scope="session")
async def test_decline_own_request_is_rejected() -> None:
    chat, users = build_repos()
    conversation = await open_direct_conversation(
        as_chat_repo(chat), as_users_repo(users), ALICE, BOB
    )

    with pytest.raises(ChatValidationError):
        await decline_conversation(as_chat_repo(chat), conversation.id, ALICE)


@pytest.mark.asyncio(loop_scope="session")
async def test_accept_and_decline_from_outsider_is_rejected() -> None:
    chat, users = build_repos()
    conversation = await open_direct_conversation(
        as_chat_repo(chat), as_users_repo(users), ALICE, BOB
    )

    with pytest.raises(ChatNotFoundError):
        await accept_conversation(
            as_chat_repo(chat), as_users_repo(users), conversation.id, EVE
        )
    with pytest.raises(ChatNotFoundError):
        await decline_conversation(as_chat_repo(chat), conversation.id, EVE)


@pytest.mark.asyncio(loop_scope="session")
async def test_accept_already_accepted_conversation_is_rejected() -> None:
    chat, users = build_repos()
    conversation_id = await seed_conversation(chat, users)  # уже accepted

    with pytest.raises(ChatValidationError):
        await accept_conversation(
            as_chat_repo(chat), as_users_repo(users), conversation_id, BOB
        )


# ========== READ MARKS ==========


@pytest.mark.asyncio(loop_scope="session")
async def test_mark_read_clears_unread() -> None:
    """Reading up to the last message zeroes the counter."""
    chat, users = build_repos()
    conversation_id = await seed_conversation(chat, users)

    message, _ = await send_message(
        as_chat_repo(chat), BOB, conversation_id, MessageCreate(text="привет")
    )
    commits_before = chat.commits

    read_id, recipients = await mark_read(
        as_chat_repo(chat), ALICE, conversation_id, message.id
    )

    assert read_id == message.id
    assert set(recipients) == {ALICE, BOB}
    assert chat.commits == commits_before + 1
    assert await chat.unread_counts(ALICE) == {}


@pytest.mark.asyncio(loop_scope="session")
async def test_mark_read_never_moves_backwards() -> None:
    """A late request from another tab must not un-read the dialog."""
    chat, users = build_repos()
    conversation_id = await seed_conversation(chat, users)

    first, _ = await send_message(
        as_chat_repo(chat), BOB, conversation_id, MessageCreate(text="раз")
    )
    second, _ = await send_message(
        as_chat_repo(chat), BOB, conversation_id, MessageCreate(text="два")
    )

    await mark_read(as_chat_repo(chat), ALICE, conversation_id, second.id)
    read_id, _ = await mark_read(as_chat_repo(chat), ALICE, conversation_id, first.id)

    assert read_id == second.id
    assert await chat.unread_counts(ALICE) == {}


@pytest.mark.asyncio(loop_scope="session")
async def test_mark_read_rejects_foreign_message() -> None:
    """A message from another dialog must not clear this one's counter."""
    chat, users = build_repos()
    conversation_id = await seed_conversation(chat, users)
    other = await open_direct_conversation(
        as_chat_repo(chat), as_users_repo(users), ALICE, EVE
    )

    await send_message(
        as_chat_repo(chat), BOB, conversation_id, MessageCreate(text="непрочитанное")
    )
    foreign, _ = await send_message(
        as_chat_repo(chat), ALICE, other.id, MessageCreate(text="из другого диалога")
    )

    with pytest.raises(ChatValidationError):
        await mark_read(as_chat_repo(chat), ALICE, conversation_id, foreign.id)

    assert (await chat.unread_counts(ALICE))[conversation_id] == 1


@pytest.mark.asyncio(loop_scope="session")
async def test_mark_read_rejects_unknown_message() -> None:
    """An invented message id cannot be used to zero the counter."""
    chat, users = build_repos()
    conversation_id = await seed_conversation(chat, users)

    await send_message(
        as_chat_repo(chat), BOB, conversation_id, MessageCreate(text="непрочитанное")
    )

    with pytest.raises(ChatValidationError):
        await mark_read(as_chat_repo(chat), ALICE, conversation_id, 999999)


@pytest.mark.asyncio(loop_scope="session")
async def test_mark_read_from_outsider_is_rejected() -> None:
    """An outsider cannot touch the read state of a dialog."""
    chat, users = build_repos()
    conversation_id = await seed_conversation(chat, users)
    message, _ = await send_message(
        as_chat_repo(chat), BOB, conversation_id, MessageCreate(text="привет")
    )

    with pytest.raises(ChatNotFoundError):
        await mark_read(as_chat_repo(chat), EVE, conversation_id, message.id)
