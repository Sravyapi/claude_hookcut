"""Tests for AuthService — register, login, JWT, conflict handling."""
import pytest

from tests.conftest import TEST_USER_EMAIL
from app.exceptions import AuthenticationError, ConflictError
from app.models.user import User, CreditBalance
from app.services.auth_service import AuthService


class TestHashAndVerify:
    def test_hash_returns_bcrypt_string(self):
        hashed = AuthService.hash_password("secret123")
        assert hashed.startswith("$2b$")

    def test_verify_correct_password(self):
        hashed = AuthService.hash_password("mypassword")
        assert AuthService.verify_password("mypassword", hashed) is True

    def test_verify_wrong_password(self):
        hashed = AuthService.hash_password("mypassword")
        assert AuthService.verify_password("wrongpassword", hashed) is False

    def test_different_calls_produce_different_hashes(self):
        h1 = AuthService.hash_password("same")
        h2 = AuthService.hash_password("same")
        assert h1 != h2


class TestCreateAccessToken:
    def test_returns_string(self):
        token = AuthService.create_access_token("uid-1", "u@test.com")
        assert isinstance(token, str)
        assert len(token) > 20

    def test_token_contains_user_id(self):
        import jwt as pyjwt
        import os
        token = AuthService.create_access_token("uid-abc", "u@test.com")
        payload = pyjwt.decode(token, os.environ["NEXTAUTH_SECRET"], algorithms=["HS256"])
        assert payload["sub"] == "uid-abc"
        assert payload["email"] == "u@test.com"


class TestRegister:
    def test_creates_new_user(self, db):
        result = AuthService.register(db, "new@test.com", "pass1234", "Alice")
        assert result["email"] == "new@test.com"
        assert result["name"] == "Alice"
        assert result["role"] == "user"
        assert "access_token" in result
        assert result["user_id"] is not None

    def test_seeds_credit_balance(self, db):
        from sqlalchemy import select as sa_select
        result = AuthService.register(db, "credit@test.com", "pass1234", "Bob")
        balance = db.execute(
            sa_select(CreditBalance).where(CreditBalance.user_id == result["user_id"])
        ).scalar_one_or_none()
        assert balance is not None
        assert balance.free_minutes_remaining == 120.0

    def test_duplicate_email_with_password_raises_conflict(self, db):
        AuthService.register(db, "dup@test.com", "pass1234", "First")
        with pytest.raises(ConflictError) as exc_info:
            AuthService.register(db, "dup@test.com", "other1234", "Second")
        assert "already registered" in exc_info.value.detail

    def test_oauth_user_can_add_password(self, db):
        # Simulate OAuth user (no hashed_password)
        user = User(id="oauth-1", email="oauth@test.com", name="OAuth", role="user")
        db.add(user)
        db.flush()
        balance = CreditBalance(user_id="oauth-1")
        db.add(balance)
        db.commit()

        result = AuthService.register(db, "oauth@test.com", "newpass", "OAuth")
        assert result["user_id"] == "oauth-1"
        assert "access_token" in result

    def test_oauth_user_gets_name_if_missing(self, db):
        user = User(id="oauth-2", email="noname@test.com", role="user")
        db.add(user)
        db.flush()
        db.add(CreditBalance(user_id="oauth-2"))
        db.commit()

        result = AuthService.register(db, "noname@test.com", "pass1234", "NewName")
        assert result["name"] == "NewName"


class TestLogin:
    def _setup_user(self, db, email="login@test.com", password="secret123"):
        user = User(
            id="login-1",
            email=email,
            name="Tester",
            hashed_password=AuthService.hash_password(password),
            role="user",
        )
        db.add(user)
        db.commit()
        return user

    def test_valid_credentials_return_token(self, db):
        self._setup_user(db)
        result = AuthService.login(db, "login@test.com", "secret123")
        assert "access_token" in result
        assert result["email"] == "login@test.com"
        assert result["role"] == "user"

    def test_wrong_password_raises_authentication_error(self, db):
        self._setup_user(db)
        with pytest.raises(AuthenticationError):
            AuthService.login(db, "login@test.com", "wrongpass")

    def test_unknown_email_raises_authentication_error(self, db):
        with pytest.raises(AuthenticationError):
            AuthService.login(db, "nobody@test.com", "pass")

    def test_oauth_user_without_password_raises_error(self, db):
        # OAuth user has no hashed_password
        user = User(id="oauth-3", email="oonly@test.com", role="user")
        db.add(user)
        db.commit()
        with pytest.raises(AuthenticationError):
            AuthService.login(db, "oonly@test.com", "anypass")

    def test_admin_role_returned(self, db):
        user = User(
            id="admin-1",
            email="admin@test.com",
            name="Admin",
            hashed_password=AuthService.hash_password("adminpass"),
            role="admin",
        )
        db.add(user)
        db.commit()
        result = AuthService.login(db, "admin@test.com", "adminpass")
        assert result["role"] == "admin"
