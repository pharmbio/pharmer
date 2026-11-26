# plaid_core: notice

This directory is PLAID_Core as bundled in iPLAID (`src/plaid_core/`), which is
derived from PLAID — Plate Layouts using Artificial Intelligence Design:
https://github.com/pharmbio/plaid (Maria Andreina Francisco Rodríguez, Ola Spjuth
and the pharmbio group, Uppsala University). Licensed under the Apache License
2.0; see `LICENSE` in this directory.

Changes made for the plate-layout-design skill:
- removed the pydantic `PlateConfigJSON` model and the JSON load/save helpers of
  `PlateDesigner` (the skill reads its own spec format in `design_layout.py`);
- `validate_minizinc_available()` also honours the `MINIZINC_PATH` variable, as
  the solver already did;
- `MiniZincSolver._generate_dzn` pads `compound_concentration_names` and
  `control_concentration_names` to a rectangular array; before, compounds (or
  controls) with different numbers of concentrations produced a .dzn that
  MiniZinc rejects;
- removed the examples, the unused `utils/dzn_generator.py` and the docs.
The MiniZinc model in `templates/` is unchanged.

Citation: Francisco Rodríguez, M. A.; Carreras Puigvert, J.; Spjuth, O.
Designing Microplate Layouts Using Artificial Intelligence. Artificial
Intelligence in the Life Sciences 3, 100073 (2023). doi:10.1016/j.ailsci.2023.100073

Disclaimer carried from upstream: the PLAID team accepts no responsibility or
liability for the use of PLAID or any direct or indirect damages arising out of
its use.
