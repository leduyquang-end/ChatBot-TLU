from dataclasses import dataclass

from src.modules.auth.infrastructure.repository_credential_checker import (
    RepositoryCredentialChecker,
)


@dataclass(frozen=True)
class StubUser:
    id: str
    username: str
    role: str


class StubRepository:
    def __init__(self, *, user=None, password_ok: bool = True) -> None:
        self._user = user
        self._password_ok = password_ok

    def find_by_username(self, username: str):
        if self._user is not None and self._user.username == username:
            return self._user
        return None

    def check_password(self, username: str, password: str) -> bool:
        return self._password_ok


USER = StubUser(id="u-001", username="sinhvien01", role="student")


def test_tra_ve_user_khi_dung_mat_khau():
    checker = RepositoryCredentialChecker(StubRepository(user=USER))
    user = checker.check("sinhvien01", "demo-password")
    assert user is USER
    assert user.id == "u-001"
    assert user.role == "student"


def test_tra_none_khi_khong_co_user():
    checker = RepositoryCredentialChecker(StubRepository(user=None))
    assert checker.check("khong-ton-tai", "x") is None


def test_tra_none_khi_sai_mat_khau():
    checker = RepositoryCredentialChecker(StubRepository(user=USER, password_ok=False))
    assert checker.check("sinhvien01", "sai") is None
