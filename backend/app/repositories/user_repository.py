from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate


def get_user_by_id(db: Session, user_id: int) -> User | None:
    statement = select(User).where(User.id == user_id)
    return db.scalar(statement)


def get_user_by_email(db: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    return db.scalar(statement)


def get_user_by_username(db: Session, username: str) -> User | None:
    statement = select(User).where(User.username == username)
    return db.scalar(statement)


def get_user_by_email_or_username(
    db: Session,
    email: str,
    username: str,
) -> User | None:
    statement = select(User).where(
        or_(
            User.email == email,
            User.username == username,
        )
    )
    return db.scalar(statement)


def create_user(db: Session, user_in: UserCreate) -> User:
    user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    user = get_user_by_email(db=db, email=email)

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user