import pytest

try:
    from app import create_app
except Exception:  # pragma: no cover
    create_app = None


@pytest.fixture(scope="module")
def test_client():
    if create_app:
        app = create_app(testing=True)
    else:
        from app import app as global_app  # type: ignore
        app = global_app

    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


@pytest.fixture
def mongo_db():
    from app.database import get_mongo_db

    db = get_mongo_db()
    assert db is not None, "MongoDB no disponible para test"
    return db
