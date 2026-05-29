def test_fastapi_app_imports_with_orm_models():
    from app.main import app

    assert app.title == "AI Study Knowledge Base"
