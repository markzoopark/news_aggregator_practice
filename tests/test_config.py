import importlib.util
from pathlib import Path
from tools import gen_config

def test_config_generated(tmp_path, monkeypatch):
    # 1) Переходимо в окрему теку
    monkeypatch.chdir(tmp_path)
    # 2) Створюємо student_id.txt з іменем TestStudent
    (tmp_path / 'student_id.txt').write_text('TestStudent', encoding='utf-8')

    # 3) Генеруємо config.py
    gen_config.generate_config()

    # 4) Динамічно завантажуємо щойно створений config.py
    config_path = tmp_path / 'config.py'
    spec = importlib.util.spec_from_file_location("config", str(config_path))
    cfg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cfg)

    # 5) Перевіряємо, що STUDENT_ID починається з 'TestStudent_'
    assert cfg.STUDENT_ID.startswith('TestStudent_')
    # 6) SOURCES має бути списком і порожнім
    assert isinstance(cfg.SOURCES, list)
    assert cfg.SOURCES == []
