# Consolidación del cambio de escenarios (eliminar "flat bridge")

## Objetivo
Eliminar la dependencia de `st.session_state["scenarios"]` (formato plano legacy) y dejar como única fuente de verdad:

- `scenarios_decision_tree` (árbol canónico editable)
- `scenarios_tree_projection` (proyección por alternativa)

---

## 1) Mapa de dependencias actual (qué hay que cambiar)

### Estado de sesión
- `scenarios` sigue inicializado como clave de primer nivel: @src/utils/session_manager.py#47-50
- Aún hay validación de consistencia para `scenarios`: @src/utils/session_manager.py#252-260

### Runtime (UI)
- El editor de escenarios sincroniza árbol -> formato plano con `_sync_tree_to_flat(...)`: @src/components/scenarios_interactive_impl.py#327-362
- `Informe` consume formato plano y EV de 2 puntos (`p_best`, `worst`, `best`): @src/components/informe.py#63-97
- `Resultados` ya está parcialmente migrado (tree-first con fallback plano): @src/components/resultados.py#185-214

### Import/Export
- Validación de JSON aún asume campo `scenarios` (lista): @src/utils/data_manager.py#145-149
- Export genera filas planas en `scenarios` (además del árbol/proyección): @src/utils/data_manager.py#362-389, @src/utils/data_manager.py#443-445
- Import reconstruye desde árbol/proyección, y hace fallback desde formato plano: @src/utils/data_manager.py#666-680
- Import todavía rellena `st.session_state["scenarios"]`: @src/utils/data_manager.py#691-710
- Import desde Excel (`Escenarios`) sigue leyendo/escribiendo plano: @src/utils/data_manager.py#1226-1263

### Templates
- Plantillas construyen árbol a partir de estructura plana: @src/components/templates.py#25-56
- Loader de templates sigue escribiendo `st.session_state["scenarios"]`: @src/components/templates.py#366-396

---

## 2) Arquitectura objetivo (post-removal)

1. **Fuente única de datos de escenarios:** árbol + proyección.
2. **Sin `st.session_state["scenarios"]` en runtime.**
3. **Sin recomputar EV desde el modelo de 2 puntos** cuando exista árbol.
4. **Schema de exportación vNext:** escenarios canónicos (árbol/proyección), sin bloque plano.
5. **Compatibilidad legacy acotada y temporal** (solo en import, durante una ventana de transición).

---

## 3) Plan de migración por fases

### Fase 0 — Guardrails (PR pequeño, sin cambios funcionales)

#### Trabajo
- Crear helper único de métricas de escenario (idealmente en `data_manager` o módulo dedicado):
  - `get_scenario_metrics_by_alt(tree_projection, alts)`
  - Retorna como mínimo: `ev`, `uncertainty`, `leaf_count`, `best_score`, `worst_score`.
- Refactorizar lectores para usar ese helper (misma lógica observable).
- Añadir tests de regresión con:
  - alternativa con 2 hojas
  - alternativa con 3+ hojas

#### Aceptación
- Sin cambios visuales de UI.
- Métricas consistentes entre pestañas que usan escenarios.

### Fase 1 — Desacoplar runtime del formato plano

#### Trabajo
- Eliminar sincronización árbol -> `st.session_state["scenarios"]` en Scenarios (`_sync_tree_to_flat` y llamadas).
- Migrar `Informe` para consumir proyección/árbol (igual que `Resultados` tras el fix).
- Mantener compatibilidad **solo en capa de import/export**, no en estado runtime.

#### Aceptación
- Ninguna pestaña funcional depende de `st.session_state["scenarios"]`.
- Resultados e Informe calculan EV/uncertainty desde árbol.

### Fase 2 — Migración de schema (cambio intencional)

#### Trabajo
- Versionar formato de exportación (ej. `v0.5.0`).
- JSON export:
  - quitar `scenarios` plano
  - mantener `scenarios_decision_tree` (y opcionalmente `scenarios_tree_projection` como cache)
- JSON import:
  - ruta principal: árbol/proyección
  - ruta legacy temporal: si viene solo `scenarios` plano, convertir una vez a árbol
- Excel:
  - decidir entre deprecación del sheet plano `Escenarios` o soporte transitorio con conversión explícita

#### Aceptación
- Export/import nuevo hace round-trip sin usar formato plano.
- Los archivos legacy siguen importando durante ventana de transición.

### Fase 3 — Limpieza final (fin de compatibilidad)

#### Trabajo
- Eliminar convertidores/funciones legacy de escenario plano cuando termine la ventana:
  - `_create_tree_from_flat_scenario`
  - `_flatten_tree_to_legacy_row`
- Eliminar default y validaciones de `scenarios` en `session_manager`.
- Eliminar cualquier consumidor restante de EV 2-puntos para escenarios canónicos.
- Actualizar templates para definir/guardar directamente árbol/proyección.

### Aceptación
- Cero referencias productivas a `st.session_state["scenarios"]` en `src/`.

---

## 4) Checklist de cambios por archivo

- `src/components/scenarios_interactive_impl.py`
  - quitar `_sync_tree_to_flat(...)` y su uso: @src/components/scenarios_interactive_impl.py#327-362

- `src/components/informe.py`
  - reemplazar consumo plano por métricas de árbol/proyección: @src/components/informe.py#63-99

- `src/utils/session_manager.py`
  - eliminar default `scenarios` y validaciones asociadas: @src/utils/session_manager.py#47-50, @src/utils/session_manager.py#252-260

- `src/utils/data_manager.py`
  - actualizar validación/import/export para schema canónico:
    - @src/utils/data_manager.py#145-157
    - @src/utils/data_manager.py#355-389
    - @src/utils/data_manager.py#443-445
    - @src/utils/data_manager.py#640-710
    - @src/utils/data_manager.py#1226-1273

- `src/components/templates.py`
  - dejar de escribir `st.session_state["scenarios"]`: @src/components/templates.py#366-396

---

## 5) Riesgos y mitigaciones

- **Riesgo:** archivos antiguos no importan.
  - **Mitigación:** convertidor de import legacy (one-way) durante ventana definida.

- **Riesgo:** deriva entre métricas de Resultados/Informe.
  - **Mitigación:** helper común + tests snapshot con el mismo caso de decisión.

- **Riesgo:** fricción en flujo Excel.
  - **Mitigación:** comunicar deprecación, documentar nuevo formato y/o mantener import transitorio con aviso.

- **Riesgo:** quedan referencias ocultas al plano.
  - **Mitigación:** chequeo CI (grep) que falle si aparece `st.session_state["scenarios"]` fuera de shim legacy.

---

## 6) Política de rollout sugerida

- **Release N**
  - Runtime 100% tree-based
  - Import legacy habilitado
  - Warning explícito al importar archivos "flat-only"

- **Release N+1**
  - Eliminar import legacy y todo código plano residual

---

## Nota de precisión

El "flat bridge" no es solo una optimización técnica: es un **modelo con pérdida** para árboles de 3+ hojas. Por eso debe quedarse únicamente como transición de import legacy y no como fuente de cálculo en runtime.