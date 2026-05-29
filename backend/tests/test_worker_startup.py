def test_worker_runs_migrations_before_polling(monkeypatch):
    import app.worker as worker

    calls = []

    monkeypatch.setattr(worker, "run_migrations", lambda: calls.append("migrate"))
    monkeypatch.setattr(worker, "process_next_job", lambda db: (_ for _ in ()).throw(KeyboardInterrupt()))

    try:
        worker.run_forever()
    except KeyboardInterrupt:
        pass

    assert calls == ["migrate"]
