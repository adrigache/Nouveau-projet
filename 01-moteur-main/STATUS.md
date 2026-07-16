# STATUS — État du projet (maj. 2026-07-16)

## Objectif inchangé

Moteur Python générique (TOML → engine), fidèle Excel au centime, cas particuliers **paramétrables**. Excel = golden / extract only.

Repo GitHub : https://github.com/adrigache/Nouveau-projet  
Code sous `01-moteur-main/`.

---

## Phases

| Phase | Contenu | État |
|-------|---------|------|
| **0** | Extracteur → `real_model.toml`, OPEX pipeline | ✅ |
| **1** | Revenus contracté + merchant exacts | ✅ |
| **2** | Operating CF : taxes locales, agency SPV=0, WCR | ✅ |
| **3** | CAPEX, D&A, EBITDA, EBIT | ✅ |
| **4** | Financement SPV (SHL, IS ATAD/CSB, CP), polish CIT+CP | ✅ |
| **5** | B/S SPV+Holdco, Overview, HDSCR, hiérarchie | ✅ (Holdco own via schedules) |
| **6** | UI Streamlit entrée + sortie | ⏳ **suivant** |

---

## Phase 4 — points clés

- Cascade : IS payé → CFADS → div → SHL → CP → IS dû (NFC = SHL + CP si flag).
- `cit_include_cash_pooling = true` (Excel r282+r149) — corrige ~1.7 k€ SPV_5.
- `cit_n_deposits = 4` — acomptes IS (SPV_6 CFADS/proceeds).
- Proceeds BoP dans CFADS ; SPV_6 sans actifs : NBV vehicle + proceeds + RE + CIT → A=L.
- SPV_1–5 SHL/EBT/CIT/net exacts vs golden.

## Phase 5 — points clés

- Parents : SPV_1–2→Holdco_1, SPV_3–6→Holdco_2.
- B/S SPV_1–5 YE2026 exacts ; SPV_6 empty path OK.
- Détentions Holdco (SC/SHL/CP) **calculées**.
- B/S Holdco complet : détentions + postes propres depuis `holdco_schedules.toml`.
- Overview : `dashboard.overview_entity` (défaut Holdco_1).
- HDSCR Holdco_2 2027 ≈ 1.15 (tolérance 0.01 ; fees engagement non encore dans le numérateur Excel).

### Limite assumée Holdco

`senior_schedule_mode = "imported"` : senior / EBL / RE / NBV fees / proceeds propres **importés**, pas sculptés.  
Régénérer : `python _extract_holdco_schedules.py` (nécessite `model_real.xlsx` local).

---

## Tests de non-régression (derniers runs)

- `test_real_model_bs.py` : **18 passed**
- `test_real_model_financing.py` (sous-ensemble SPV_2/5/6) : **15 passed**
- Full financing suite ~33 tests (long : ~15 min)

---

## Fichiers locaux non Git

| Fichier | Pourquoi |
|---------|----------|
| `model_real.xlsx` (~25 Mo) | Golden Excel — à recopier manuellement sur l’autre PC |
| `.venv/` | Recréer : `python -m venv .venv` + install deps |
| `.env` | Secrets / chemins locaux |

Sans `model_real.xlsx`, les tests TOML/golden tournent ; seuls les extracteurs Excel bloquent.

---

## Prochaine session — brief suggéré

> Lis `AGENTS.md`, `STATUS.md`, `.cursor/rules/`.  
> Phase 5 terminée. Enchaîne **Phase 6 Streamlit** : formulaire d’hypothèses (TOML) + affichage résultats (P&L / B/S / ratios), en gardant le moteur générique et les flags déjà prévus (`cit_include_cash_pooling`, `overview_entity`, etc.).  
> Ne pas réécrire le financement SPV sauf bug. Holdco sculpting = chantier séparé si besoin.

---

## Décisions / pièges à ne pas répéter

1. **Pas d’Excel au runtime** — seulement TOML.
2. **Vehicle D&A CAPEX** = somme de **toutes** les colonnes actifs du SPV (actifs inactifs inclus), Excel r413.
3. **Dividendes avant SHL** + offset CP (ordre Excel r486–539).
4. CIT payé ≠ `2*due_prev` en général → formule acomptes.
5. SPV_6 : pas d’actifs → chemins `_spv_level_da_annual` + stocks via `hierarchy`.
6. Ne pas fantasiner des macros VBA « iterate » pour CIT↔CP : lag IS payé suffit.
