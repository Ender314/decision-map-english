# Evolución de la planificación de escenarios

> Documento vivo de transición técnica para registrar el estado real de **Escenarios**, decisiones en evaluación, drift entre documentación/código y posibles restos obsoletos.

## 1) Propósito y alcance

Este documento **no** busca documentación final de producto.

Su objetivo es servir como:
- **log de evolución** de implementación,
- **referencia rápida** para decidir siguientes pasos,
- **rastreador de drift** (qué está activo vs qué quedó atrás),
- **inventario de deuda temporal** durante la fase de experimentación.

Se centra en el módulo **Escenarios** y su integración con el resto de la app.

---

## 2) Snapshot actual (Feb 2026)

### Estado funcional actual

- La pestaña **Escenarios** está activa en el flujo principal de análisis.
- `components/scenarios.py` funciona como **wrapper** y delega en la implementación interactiva.
- Motor principal actual: `components/advanced_scenarios_interactive.py`.
- El árbol se puede recentrar manualmente con botón **"🎯 Centrar árbol"**.

Referencias:
- `src/components/scenarios.py`
- `src/components/advanced_scenarios_interactive.py`
- `src/app_with_routing.py`

### Modelo actual en ejecución (alto nivel)

- Árbol de decisión unificado en sesión:
  - raíz: objetivo,
  - nivel 1: alternativas sincronizadas automáticamente,
  - niveles siguientes: ramas/sub-ramas editables por interacción.
- Visualización interactiva con `streamlit-agraph`.
- Filtrado de alternativas descalificadas por **No Negociables**.
- El centrado/rezoom del árbol se fuerza por remount controlado del componente (`_iact_tree_recenter_nonce`).

### Salidas actuales dentro de Escenarios

- **Toggle único** de visualizaciones para evitar coste de render durante edición del árbol.
- **Distribuciones de probabilidad** en un único gráfico con:
  - eje X compartido (0-10),
  - separación vertical por alternativa,
  - área no espejada (one-sided),
  - marcador EV por alternativa.
- **Matriz de decisión** en estructura de 2 pestañas:
  1. `Vista básica`: burbujas MCDA × EV (compuesto + incertidumbre).
  2. `🔍 Detalle`: visual MCDA × EV por hojas (densidad por alternativa) sin encabezado extra.
- Colores de alternativas **consistentes** entre `Vista básica` y `🔍 Detalle`.
- Orden de alternativas **alineado** entre ambas vistas usando orden MCDA.

---

## 3) Compatibilidad de datos (estado actual)

Actualmente conviven dos representaciones para mantener compatibilidad:

1. **Canónica para edición** (árbol interactivo)
2. **Proyección legacy** (`scenarios` plano) para módulos existentes (Resultados/Informe/export)

Resultado práctico:
- Se puede seguir exportando/importando con compatibilidad histórica,
- pero existe complejidad adicional por sincronización y puentes de formato.

---

## 4) Drift y restos potencialmente obsoletos

### Drift documentación vs implementación

- Parte de la documentación aún describe Escenarios con enfoque anterior (o genérico).
- La arquitectura real hoy depende del árbol interactivo unificado y de una UI de visualización por etapas (toggle + tabs).

### Señales de código transicional / posible obsolescencia

- `advanced_scenarios.py` mantiene utilidades (p. ej. Plotly tree) que **no parecen formar parte del flujo principal activo**.
- Existen funciones/constantes con aparente duplicidad o desalineación entre módulos.
- Hay artefactos de UI/constantes que pueden provenir de iteraciones previas.
- La estrategia de remount por micro-cambio de configuración para `agraph` es un workaround práctico y conviene revisarla si se actualiza `streamlit-agraph`.

> Nota: esto no implica borrar inmediatamente. Solo marca candidatos para revisión cuando la dirección de diseño quede establecida.

---

## 5) Decisiones abiertas (en reevaluación)

1. ¿Mantener el árbol unificado como modelo definitivo?
2. ¿Consolidar en una sola fuente de verdad de estado para Escenarios?
3. ¿Qué piezas legacy conservar por compatibilidad y cuáles retirar?
4. ¿Mantener o retirar definitivamente la visualización legacy/experimental fuera de las 2 vistas consolidadas?
5. ¿Cuándo pasar de "documentación de transición" a "documentación oficial"?

---

## 6) Registro de cambios (log)

> Añadir nuevas entradas al inicio (orden descendente por fecha).

### [2026-02-19] Consolidación UX/visual de Escenarios interactivos

- **Cambio implementado:**
  - Se consolidan visualizaciones bajo un solo toggle (`Mostrar visualizaciones`).
  - Se mueve `Distribuciones de probabilidad` justo después de la definición del árbol.
  - Se rediseña `Distribuciones` a vista consolidada con eje X compartido y separación vertical por alternativa.
  - Se integra `MCDA × EV (densidad por alternativa)` dentro de la sección Matriz mediante tabs (`Vista básica` / `🔍 Detalle`).
  - Se centra el botón `Aplicar cambios` del panel de edición de nodo.
  - Se unifican colores y orden de alternativas entre `Vista básica` y `🔍 Detalle`.
  - Se incorpora botón `🎯 Centrar árbol` con intento explícito de recenter + rezoom por remount.
- **Motivación:** mejorar legibilidad comparativa, reducir coste de render mientras se edita el árbol, y mejorar ergonomía de navegación del grafo.
- **Archivos tocados:**
  - `src/components/advanced_scenarios_interactive.py`
- **Impacto funcional visible:** UX más guiada (primero edición de árbol, luego visualización), mayor coherencia entre gráficos y control manual de centrado.
- **Impacto en compatibilidad (import/export/resultados/informe):** sin cambios de formato; se mantiene puente árbol canónico + proyección legacy (`advanced_scenarios` + `scenarios`).
- **Drift/obsolescencia detectada:** persiste código/artefactos de etapas previas y workaround de remount para `agraph`.
- **Decisión tomada / pendiente:**
  - Tomada: consolidar visualizaciones en estructura toggle + tabs.
  - Pendiente: decidir limpieza final de piezas legacy y estabilización post-experimentos.

### [2026-02-17] Baseline inicial del documento

- Se crea este archivo como referencia viva de transición para Escenarios.
- Se confirma que la ruta activa actual usa wrapper `scenarios.py` → `advanced_scenarios_interactive.py`.
- Se registra coexistencia de modelo canónico (árbol) + proyección legacy (plano) para compatibilidad.
- Se identifica presencia de drift de documentación y posibles restos transicionales.

---

## 7) Plantilla para próximas entradas

Copiar y completar:

```md
### [YYYY-MM-DD] Título corto del cambio

- **Cambio implementado:**
- **Motivación:**
- **Archivos tocados:**
- **Impacto funcional visible:**
- **Impacto en compatibilidad (import/export/resultados/informe):**
- **Drift/obsolescencia detectada:**
- **Decisión tomada / pendiente:**
```

---

## 8) Criterio de salida de transición

Este documento podrá congelarse (o migrarse a docs oficiales) cuando:
- el modelo final de Escenarios esté decidido,
- el puente legacy se simplifique o estabilice,
- y el inventario de código transicional quede resuelto.

---

## 9) Seed de checklist de estabilización (consolidación)

> Uso recomendado: copiar este bloque a una issue/PR de consolidación y marcar estado por ítem (`TODO` / `IN PROGRESS` / `DONE`).

### A. Modelo de estado y consistencia interna

- [ ] Validar que `advanced_scenarios_decision_tree` es la única fuente editable en runtime (sin writes paralelos conflictivos).
- [ ] Confirmar sincronización estable de nivel 1 (alternativas) al crear/editar/eliminar alternativas.
- [ ] Verificar que el filtrado por **No Negociables** no deja nodos huérfanos ni escenarios proyectados inconsistentes.
- [ ] Revisar y documentar invariantes de probabilidades por nodo padre (sumatoria esperada y reglas de rebalanceo).

### B. UX/flujo de interacción

- [ ] Verificar que `Mostrar visualizaciones` evita render costoso mientras se edita el árbol.
- [ ] Confirmar que el orden de alternativas es consistente en `Vista básica`, `🔍 Detalle` y distribuciones.
- [ ] Confirmar que el mapeo de colores por alternativa es consistente en todas las vistas.
- [ ] Validar comportamiento del botón `🎯 Centrar árbol` (centrado + rezoom percibido) en sesiones largas.
- [ ] Revisar mensajes de ayuda/captions para minimizar ambigüedad entre vista básica y detalle.

### C. Rendimiento y reruns

- [ ] Medir reruns por interacción clave (editar nodo, bifurcar, eliminar, recentrar, cambiar tabs/toggle).
- [ ] Confirmar que no persiste el patrón de "rerun extra" tras recentrar.
- [ ] Evaluar impacto del workaround de remount (`_iact_tree_recenter_nonce`) y definir criterio de sustitución futura.

### D. Compatibilidad de datos (import/export + downstream)

- [ ] Testear export/import round-trip (JSON) preservando árbol canónico + proyección legacy.
- [ ] Confirmar compatibilidad con archivos legacy (sin `advanced_scenarios` o con estructura parcial).
- [ ] Validar que `Resultados` e `Informe` siguen consumiendo datos esperados sin regresiones.

### E. Limpieza técnica y deuda transicional

- [ ] Inventariar funciones/código no usados en `advanced_scenarios.py` vs flujo activo.
- [ ] Identificar constantes/artefactos de UI duplicados o heredados que puedan consolidarse.
- [ ] Decidir explicitamente qué componentes se quedan como "legacy bridge" y cuáles se deprecian.

### F. Evidencia de estabilidad antes de cerrar transición

- [ ] Crear checklist de regresión manual mínima (happy path + edge cases críticos).
- [ ] Adjuntar capturas/video corto de flujo estable (edición árbol → visualizaciones → resultados).
- [ ] Registrar en el log de este documento la decisión final de arquitectura y alcance de limpieza.
