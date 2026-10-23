from src.modules.user.application.list_users import ListUsers
from src.modules.user.domain.user import User
from tests.unit.modules.user.application.fakes import (
    ADMIN_USER,
    DEMO_USER,
    FakeUserRepository,
)


def test_liet_ke_tat_ca_user():
    repo = FakeUserRepository([DEMO_USER, ADMIN_USER])
    users = ListUsers(repo).execute()
    assert {user.id for user in users} == {"u-001", "u-002"}


def test_ket_qua_xep_theo_id():
    extra = User(id="u-003", username="sv03", full_name="Sinh viên 3", role="student")
    repo = FakeUserRepository([extra, DEMO_USER, ADMIN_USER])
    users = ListUsers(repo).execute()
    assert [user.id for user in users] == ["u-001", "u-002", "u-003"]


def test_kho_rong_tra_danh_sach_rong():
    assert ListUsers(FakeUserRepository()).execute() == []
