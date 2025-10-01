# Lambda Pro - Corporate Decision Analysis Tool

A Streamlit application designed for structuring thinking around high-stakes corporate decisions using proven decision analysis methodologies.

## Features

- **Multi-tab workflow** with adaptive complexity based on time allocation
- **Impact assessment** with temporal analysis (short, medium, long term)
- **MCDA (Multi-Criteria Decision Analysis)** with weighted scoring
- **Scenario planning** with probability distributions
- **Comprehensive data collection** (KPIs, timelines, stakeholders)
- **Executive summary** with recommendations
- **Export/Import** functionality for session persistence

## Project Structure (Phase 1 - Modular Architecture)

```
Lambda project Pro/
├── src/                          # New modular source code
│   ├── app.py                   # Main Streamlit application
│   ├── config/
│   │   ├── __init__.py
│   │   └── constants.py         # All constants and configuration
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── calculations.py      # Mathematical operations and MCDA
│   │   ├── data_manager.py      # Session state and export/import
│   │   └── visualizations.py    # Chart generation with Plotly
│   └── components/
│       ├── __init__.py
│       ├── dimensionado.py      # Impact assessment tab
│       ├── alternativas.py      # Alternatives management
│       ├── prioridades.py       # Priorities/criteria management
│       ├── evaluacion.py        # MCDA evaluation
│       └── sidebar.py           # Export/import sidebar
├── Lambda Pro desarrollo.py     # Original monolithic file (backup)
├── streamlit_venv/              # Virtual environment
└── README.md                    # This file
```

## Installation & Usage

### Prerequisites
- Python 3.8+
- Virtual environment with Streamlit and dependencies

### Running the Application

#### Option 1: New Modular Version (Recommended)
```bash
# Activate virtual environment (Windows)
streamlit_venv\Scripts\activate

# Run modular version
python -m streamlit run src/app.py
```

#### Option 2: Original Version
```bash
# Activate virtual environment (Windows)
streamlit_venv\Scripts\activate

# Run original version
python -m streamlit run "Lambda Pro desarrollo.py"
```

## Phase 1 Implementation Status

### ✅ Completed Components
- **Project Structure**: Modular architecture with clear separation of concerns
- **Constants & Configuration**: Centralized configuration management
- **Utilities**: Mathematical calculations, data management, and visualizations
- **All Tabs**: Complete functionality for all 8 tabs
  - **Dimensionado**: Impact assessment with temporal analysis
  - **Alternativas**: Alternatives management with CRUD operations
  - **Objetivo**: Simple objective definition
  - **Prioridades**: Ordered priorities with up/down controls
  - **Información**: KPIs, timeline, stakeholders with visualizations
  - **Evaluación**: Full MCDA evaluation with weighted scoring
  - **Scenario Planning**: Probability distributions with violin plots
  - **Resultados**: Comprehensive executive summary dashboard
- **Export/Import**: Full session persistence with JSON format
- **Sidebar**: Integrated export/import functionality
- **Error Handling**: Robust error handling for visualizations and data loading

### ✅ Recent Fixes (v0.2.1)
- **Plotly Methods**: Fixed `update_yaxis` → `update_yaxes` for proper chart rendering
- **Import Issues**: Resolved relative import problems in data_manager
- **Error Handling**: Added try-catch blocks for visualization components
- **Data Loading**: Improved robustness when loading exported decision data

## Key Improvements in Modular Version

1. **Maintainability**: 1,824-line monolith split into focused modules
2. **Reusability**: Shared utilities and components
3. **Testability**: Isolated functions and clear interfaces
4. **Scalability**: Easy to add new tabs and features
5. **Code Quality**: Consistent patterns and documentation

## Architecture Benefits

- **Single Responsibility**: Each module has a clear purpose
- **Dependency Injection**: Components receive dependencies explicitly
- **Configuration Management**: Centralized constants and settings
- **Error Handling**: Improved error boundaries and validation
- **Performance**: Cached calculations and optimized rendering

## Next Steps (Phase 2)

1. **Complete remaining components** (Información, Scenarios, Resultados)
2. **Implement generic CRUD components** to reduce code duplication
3. **Add caching and performance optimizations**
4. **Create SessionManager class** for better state management
5. **Enhance error handling and user feedback**

## Development Guidelines

- **Consistent naming**: Use Spanish for UI, English for code
- **Type hints**: Add type annotations for better code clarity
- **Documentation**: Document all public functions and classes
- **Error handling**: Graceful degradation and user-friendly messages
- **Testing**: Unit tests for utility functions

## Contributing

When adding new components:
1. Follow the established pattern in existing components
2. Add type hints and documentation
3. Update the main app.py to include new components
4. Test both individual components and full integration
