# AGENTS.md — MCA / ALTGR Project Finance Engine

## Mission

Transformer un modèle Excel Project Finance (renouvelables) en **moteur Python** :

- **Fidélité** : Excel = source de vérité (golden) au centime près.
- **Runtime** : **TOML → moteur** uniquement (pas de lecture Excel en production).
- **Générique** : tout jeu de données via paramètres TOML / futur formulaire Streamlit.
- **Cas particuliers** : flags configurables (jamais hardcodés pour un SPV nommé).

Excel (`model_real.xlsx`, ~25 Mo, **non versionné**) sert à l’extraction one-shot et aux goldens. Ne jamais brancher le runtime dessus.

## Architecture

```
Model → TopCo → HoldCo → SPV → Asset
```

| Couche | Rôle |
|--------|------|
| `plumbing/` | Arbre objets, `build.load(toml)` |
| `model/` | Calculs (revenus, OPEX, taxes, CAPEX/D&A, financement, B/S, ratios) |
| `repository/filesystem/` | ETL Excel legacy (tagging) — le vrai chemin Phase 0+ est `_extract_real_model.py` → TOML |
| `interface/` | CLI + Streamlit (Phase 6) |
| `test/assets/` | `real_model.toml`, `golden_results.toml`, `holdco_schedules.toml` |

Calculs **asset-wise** via `TopCo.apply` → `SPV.apply_on_assets`. Agrégations SPV/Holdco via helpers dédiés.

## Fichiers critiques

| Fichier | Rôle |
|---------|------|
| `test/assets/real_model.toml` | Hypothèses extraites (183 actifs, 6 SPV, 2 Holdco) |
| `test/assets/golden_results.toml` | Cibles Excel (P&L, CF, B/S, ratios) |
| `test/assets/holdco_schedules.toml` | Échéanciers Holdco (senior/EBL/own BS) — mode `imported` |
| `src/mca_model/model/financing.py` | Cascade annuelle SPV (SHL, CP, IS, proceeds) |
| `src/mca_model/model/balance_sheet/` | B/S asset + `hierarchy.py` + `vehicle.py` |
| `src/mca_model/model/overview.py` | Vue entité (`overview_entity`) |
| `src/mca_model/model/ratios.py` | HDSCR / LLCR / PLCR |
| `_extract_real_model.py` | One-shot Excel → `real_model.toml` |
| `_extract_holdco_schedules.py` | One-shot → `holdco_schedules.toml` |

## Paramètres modulaires (formulaire Phase 6)

```toml
[dashboard]
overview_entity = "Holdco_1"   # vue Overview

[market.tax]
cit_include_cash_pooling = true  # Excel FR : CP dans base IS
cit_n_deposits = 4               # acomptes IS

# Holdco (holdco_schedules.toml)
senior_schedule_mode = "imported"  # futur : sculpting moteur
```

Hiérarchie véhicules : `ass_Vehicle` r41/r43 → `parent` dans TOML  
(`SPV_1–2 → Holdco_1`, `SPV_3–6 → Holdco_2`).

## Conventions de calcul

- Unités B/S / P&L / CF : **k€** (revenus électricité souvent /1000).
- Financement : **annuel** puis projection mensuelle.
- IS payé : acomptes Excel r332–339 (pas la formule naïve `2×prev`).
- Proceeds BoP entre dans CFADS (critique SPV_6 sans actifs).
- Détentions Holdco = Σ stocks enfants × `detention_pct` (défaut 100 %).
- Postes propres Holdco (senior, RE, NBV fees…) : schedules importés tant que le P&L Holdco n’est pas 100 % moteur.

## Tests

```bash
cd 01-moteur-main
.venv\Scripts\python.exe -m pytest test/model/test_real_model_bs.py -q
.venv\Scripts\python.exe -m pytest test/model/test_real_model_financing.py -q
```

Goldens : tolérance typique `abs=1e-2` (k€).  
`model_real.xlsx` requis seulement pour régénérer extracteurs / auditer Excel.

## Suite (Phase 6+)

1. UI Streamlit entrée/sortie (hypothèses + résultats).
2. Remplacer `senior_schedule_mode=imported` par sculpting DSCR moteur.
3. P&L Holdco 100 % calculé (revenus détention, agency, CIT).
4. Fees d’engagement dans HDSCR (écart ~0.002 vs Excel 1.15).
5. Topco / Overview multi-entité complet.

Voir **`STATUS.md`** pour l’état détaillé des phases.
