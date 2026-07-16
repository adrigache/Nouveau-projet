# 01 Moteur

Moteur Project Finance Python (ALTGR / MCA) — Excel → TOML → engine.

**Pour les agents / reprise de contexte** : lire [`AGENTS.md`](AGENTS.md) et [`STATUS.md`](STATUS.md).

## Development

Use `ty` for checking static types and `pytest`.

> pip install ty
> ty check

```bash
python -m venv .venv
# activer .venv puis installer deps (voir pyproject.toml)
pytest test/model/test_real_model_bs.py -q
```

## Notes
