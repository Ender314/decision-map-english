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

## Estado funcional actual

- La pestaña **Escenarios** está activa en el flujo principal de análisis.
- `components/scenarios.py` funciona como **wrapper** y delega en la implementación interactiva.
- Motor principal actual: `components/advanced_scenarios_interactive.py`.

Referencias:
- `src/components/scenarios.py`
- `src/components/advanced_scenarios_interactive.py`
- `src/app_with_routing.py`

## Modelo actual en ejecución (alto nivel)

- Árbol de decisión unificado en sesión:
  - raíz: objetivo,
  - nivel 1: alternativas sincronizadas automáticamente,
  - niveles siguientes: ramas/sub-ramas editables por interacción.
- Visualización interactiva con `streamlit-agraph`.
- Filtrado de alternativas descalificadas por **No Negociables**.

## Salidas actuales dentro de Escenarios

- Visual de densidad **MCDA × EV** por alternativa.
- Distribuciones suavizadas por mezcla de hojas.
- Matriz de decisión con ranking compuesto y slider de pesos MCDA/EV.

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

## Drift documentación vs implementación

- Parte de la documentación aún describe Escenarios con enfoque anterior (o genérico).
- La arquitectura real hoy depende del árbol interactivo unificado.

## Señales de código transicional / posible obsolescencia

- `advanced_scenarios.py` mantiene utilidades (p. ej. Plotly tree) que **no parecen formar parte del flujo principal activo**.
- Existen funciones/constantes con aparente duplicidad o desalineación entre módulos.
- Hay artefactos de UI/constantes que pueden provenir de iteraciones previas.

> Nota: esto no implica borrar inmediatamente. Solo marca candidatos para revisión cuando la dirección de diseño quede establecida.

---

## 5) Decisiones abiertas (en reevaluación)

1. ¿Mantener el árbol unificado como modelo definitivo?
2. ¿Consolidar en una sola fuente de verdad de estado para Escenarios?
3. ¿Qué piezas legacy conservar por compatibilidad y cuáles retirar?
4. ¿Cuándo pasar de "documentación de transición" a "documentación oficial"?

---

## 6) Registro de cambios (log)

> Añadir nuevas entradas al inicio (orden descendente por fecha).

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
