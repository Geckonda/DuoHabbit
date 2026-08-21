"""Web Push subscription model."""

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from duohabit.db import Base
from duohabit.models.mixins import TimestampMixin

# pylint: disable=too-few-public-methods
# Models exist for a different reason.


class PushSubscription(TimestampMixin, Base):
    """A browser's Web Push subscription, tied to the user who created it."""

    __tablename__ = "push_subscription"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), index=True
    )

    # Уникален глобально (выдаётся push-сервисом браузера на связку браузер+сайт),
    # поэтому по нему и делаем upsert - в т.ч. решает случай "тот же браузер, другой юзер"
    endpoint: Mapped[str] = mapped_column(Text, unique=True)
    p256dh: Mapped[str] = mapped_column(String(255))
    auth: Mapped[str] = mapped_column(String(255))
