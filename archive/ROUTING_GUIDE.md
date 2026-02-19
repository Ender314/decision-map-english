# Lambda Pro - Integrated Routing System

> **Estado:** ARCHIVADO (2026-02-19)
>
> Guía histórica de implementación inicial del routing.
> Referencia activa: `src/app_with_routing.py` y `README.md`.

## 🚀 Overview

The Lambda Pro application now includes an integrated routing system that seamlessly combines the landing page with the main application functionality. Users can navigate between the marketing landing page and the decision analysis tools without losing their session data.

## 📁 New Files Created

### `src/app_with_routing.py`
- **Main application file** with integrated routing
- **Session-based navigation** between landing and app
- **Preserves all original functionality** while adding navigation
- **Wide layout** optimized for both landing and app views

### `src/components/landing_page.py`
- **Modular landing page component** 
- **Interactive demo visualizations** showcasing app capabilities
- **Navigation buttons** to switch to main app
- **Professional marketing presentation**

## 🔄 Navigation Flow

### **Landing Page → App**
1. User visits landing page (default)
2. Clicks "🚀 Launch Lambda Pro" or "🚀 Start Analysis"
3. Session state switches to `"app"` mode
4. Main application loads with full functionality

### **App → Landing Page**
1. User clicks "← Back to Home" (header or sidebar)
2. Session state switches to `"landing"` mode  
3. Landing page displays while **preserving all session data**
4. User can return to app without losing work

## 🎯 Key Features

### **Seamless Integration**
- ✅ **Single application** - no separate deployments needed
- ✅ **Session persistence** - data preserved during navigation
- ✅ **Consistent branding** - unified Lambda Pro experience
- ✅ **Performance optimized** - shared components and state

### **Navigation Options**
- ✅ **Header navigation** - prominent "Back to Home" button
- ✅ **Sidebar navigation** - always accessible in app mode
- ✅ **Landing page CTAs** - multiple entry points to app
- ✅ **Import redirection** - auto-switches to app after data import

### **User Experience**
- ✅ **Professional landing** - showcases value proposition
- ✅ **Interactive demos** - live chart examples
- ✅ **Clear workflow** - guides users through capabilities
- ✅ **Easy access** - one-click switching between modes

## 🚀 How to Run

### **Option 1: New Integrated Version (Recommended)**
```bash
cd "c:\Users\yomis\OneDrive\Desarrollos\Lambda project Pro"
streamlit_venv\Scripts\activate
python -m streamlit run src/app_with_routing.py --server.port 8501
```

### **Option 2: Original App Only**
```bash
python -m streamlit run src/app.py --server.port 8501
```

### **Option 3: Landing Page Only**
```bash
python -m streamlit run landing.py --server.port 8502
```

## 🔧 Technical Implementation

### **Session State Management**
- `st.session_state["current_page"]` controls routing
- `"landing"` = Landing page mode
- `"app"` = Main application mode
- All existing session data preserved during navigation

### **Component Structure**
```
src/
├── app_with_routing.py          # Main integrated app
├── components/
│   ├── landing_page.py          # Landing page component
│   ├── sidebar.py               # Enhanced with navigation
│   └── [existing components]    # All original functionality
└── [existing structure]         # Unchanged
```

### **Navigation Logic**
```python
# Main routing in app_with_routing.py
if st.session_state["current_page"] == "landing":
    render_landing_page()
else:
    render_main_app()
```

## 🎨 Landing Page Features

### **Professional Design**
- **Gradient headers** with Lambda Pro branding
- **Interactive visualizations** showing app capabilities
- **Modern card layouts** with feature descriptions
- **Responsive design** optimized for wide layout

### **Demo Visualizations**
- **Impact Assessment** - Temporal analysis chart
- **MCDA Evaluation** - Radar comparison charts  
- **Scenario Planning** - Violin plot distributions
- **Executive Dashboard** - Confidence gauge metrics

### **Marketing Content**
- **Value proposition** - Clear problem/solution framework
- **Feature showcase** - 8 analysis modules highlighted
- **Business benefits** - ROI-focused messaging
- **Use cases** - Strategic planning, operations, risk assessment

## 🔄 Migration Guide

### **From Original App**
- Replace `streamlit run src/app.py` with `streamlit run src/app_with_routing.py`
- All existing functionality preserved
- Session data automatically maintained
- No changes needed to existing components

### **Benefits of Integrated Version**
- ✅ **Professional first impression** with landing page
- ✅ **Better user onboarding** with feature showcase
- ✅ **Unified experience** - no separate deployments
- ✅ **Session continuity** - seamless navigation
- ✅ **Marketing ready** - can be shared with stakeholders

## 🎯 Best Practices

### **For Development**
- Use `app_with_routing.py` as main entry point
- Test navigation flows regularly
- Maintain session state consistency
- Keep landing page demos updated with app features

### **For Deployment**
- Deploy `app_with_routing.py` as primary application
- Landing page serves as marketing and onboarding
- Share single URL - users get full experience
- Monitor navigation analytics if needed

## 🏆 Result

The integrated routing system provides:
1. **Professional landing page** that showcases Lambda Pro's value
2. **Seamless navigation** between marketing and functionality  
3. **Preserved session data** during navigation
4. **Unified deployment** - single application to maintain
5. **Enhanced user experience** - clear onboarding path

Perfect for sharing with stakeholders, demonstrating capabilities, and providing a professional entry point to the Lambda Pro decision analysis platform.
