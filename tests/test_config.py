def test_settings_load():
    from app.config import settings
    assert settings.database_url.startswith("postgresql")
    assert len(settings.secret_key) >= 32
