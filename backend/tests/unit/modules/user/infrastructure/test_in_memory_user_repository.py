import pytest

from src.modules.user.domain.user import ROLE_ADMIN, ROLE_STUDENT, User
from src.modules.user.infrastructure.in_memory_user_repository import (
    InMemoryUserRepository,
)
from src.shared.common.errors import NotFoundError

STUDENT = User(
    id="u-001", username="sinhvien01", full_name="Sinh viên Demo", role=ROLE_STUDENT
)
ADMIN = User(id="u-002", username="admin01", full_name="Quản trị", role=ROLE_ADMIN)


def make_repo(*users: User) -> InMemoryUserRepository:
    repo = InMemoryUserRepository()
    for user in users:
        repo.save(user)
    return repo


def test_find_by_id_tim_thay_va_khong_thay():
    repo = make_repo(STUDENT)
    assert repo.find_by_id("u-001") == STUDENT
    assert repo.find_by_id("khong-ton-tai") is None


def test_find_by_username_tim_thay_va_khong_thay():
    repo = make_repo(STUDENT, ADMIN)
    assert repo.find_by_username("sinhvien01") == STUDENT
    assert repo.find_by_username("khong-ton-tai") is None


def test_save_tao_moi_va_cap_nhat():
    repo = make_repo(STUDENT)
    repo.save(ADMIN)
    assert len(repo.list_all()) == 2
    updated = STUDENT.with_full_name("Nguyễn Văn A")
    repo.save(updated)
    assert len(repo.list_all()) == 2
    assert repo.find_by_id("u-001").full_name == "Nguyễn Văn A"


def test_list_all_tra_tat_ca():
    repo = make_repo(ADMIN, STUDENT)
    assert {user.id for user in repo.list_all()} == {"u-001", "u-002"}


def test_set_va_check_password_dung_sai():
    repo = make_repo(STUDENT)
    repo.set_password("sinhvien01", "mat-khau-1")
    assert repo.check_password("sinhvien01", "mat-khau-1") is True
    assert repo.check_password("sinhvien01", "sai-mat-khau") is False


def test_check_password_chua_dat_mat_khau_tra_false():
    repo = make_repo(STUDENT)
    assert repo.check_password("sinhvien01", "bat-ky") is False


def test_check_password_nguoi_khong_ton_tai_tra_false():
    assert make_repo().check_password("khong-ton-tai", "bat-ky") is False


def test_mat_khau_khong_duoc_luu_plaintext():
    """Bảo mật: kho chỉ giữ hash PBKDF2 salt$digest, không giữ mật khẩu gốc."""
    repo = make_repo(STUDENT)
    repo.set_password("sinhvien01", "mat-khau-goc-123")
    stored = repo._credentials["sinhvien01"]
    assert stored != "mat-khau-goc-123"
    assert "mat-khau-goc-123" not in stored
    salt_hex, _digest_hex = stored.split("$", 1)
    assert len(salt_hex) == 32


def test_salt_ngau_nhien_hash_khac_nhau():
    repo = make_repo(STUDENT, ADMIN)
    repo.set_password("sinhvien01", "cung-mat-khau")
    repo.set_password("admin01", "cung-mat-khau")
    assert (
        repo._credentials["sinhvien01"] != repo._credentials["admin01"]
    ), "2 mật khẩu giống nhau phải cho hash khác nhau (salt ngẫu nhiên)"


def test_set_password_nguoi_khong_ton_tai_nem_not_found():
    """Không ghi credential mồ côi — username phải có user thật."""
    repo = make_repo()
    with pytest.raises(NotFoundError):
        repo.set_password("khong-ton-tai", "mat-khau-1")
    assert repo._credentials == {}


def test_singleton_tra_cung_mot_object(monkeypatch):
    """get_user_repository() phải trả cùng một object (dữ liệu sống qua nhiều request)."""
    from src.modules.user.infrastructure import in_memory_user_repository as mod

    existing = InMemoryUserRepository()
    monkeypatch.setattr(mod, "_USER_REPOSITORY", existing)
    assert mod.get_user_repository() is existing


def test_seed_tao_2_tai_khoan_demo():
    from src.modules.user.infrastructure.in_memory_user_repository import (
        get_user_repository,
    )

    repo = get_user_repository()
    student = repo.find_by_username("sinhvien01")
    admin = repo.find_by_username("admin01")
    assert student is not None and student.role == ROLE_STUDENT
    assert admin is not None and admin.role == ROLE_ADMIN
    assert repo.check_password("sinhvien01", "demo-password") is True
    assert repo.check_password("sinhvien01", "sai") is False
