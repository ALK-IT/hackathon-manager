from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models import Base


class Hackathon(Base):
    __tablename__ = "hackathons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
