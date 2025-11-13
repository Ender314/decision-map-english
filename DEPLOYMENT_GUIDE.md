# 🚀 Streamlit Community Cloud Deployment Guide

This comprehensive guide will walk you through deploying your Lambda Pro Streamlit application to Streamlit Community Cloud.

## 📋 Prerequisites

Before starting the deployment process, ensure you have:

- [ ] A GitHub account
- [ ] Your Streamlit application code in a GitHub repository
- [ ] A Streamlit Community Cloud account (free)
- [ ] All dependencies properly configured

## 🏗️ Step 1: Prepare Your Application Structure

### 1.1 Verify File Organization

Your application should have the following structure:

```
Lambda project Pro/
├── src/
│   ├── app_with_routing.py          # Main application entry point
│   ├── components/                   # UI components
│   ├── utils/                       # Utility functions
│   └── config/                      # Configuration files
├── .streamlit/
│   └── secrets.toml                 # Local secrets (DO NOT commit)
├── requirements.txt                 # Python dependencies
└── README.md                        # Project documentation
```

### 1.2 Set Main Application File

Your main entry point is `src/app_with_routing.py`. This file contains:
- Multi-page routing system
- Session state management
- Component imports and rendering

## 🔧 Step 2: Configure Dependencies

### 2.1 Requirements.txt Setup

✅ **Already Created**: A `requirements.txt` file has been created in your project root with the following dependencies:

```txt
# Core Streamlit framework
streamlit>=1.28.0

# Data manipulation and analysis
pandas>=2.0.0
numpy>=1.24.0

# Visualization libraries
plotly>=5.15.0
seaborn>=0.12.0
matplotlib>=3.7.0

# Additional utilities
openpyxl>=3.1.0
```

### 2.2 Important Notes About Dependencies

- **Built-in libraries**: Don't include `math`, `random`, `os`, `sys`, `json`, `uuid`, `datetime` in requirements.txt
- **Streamlit**: Pre-installed on Community Cloud, but pinned for version consistency
- **Version pinning**: Use `>=` for flexibility while ensuring minimum required versions

### 2.3 Python Version Compatibility

Your app uses modern Python features and should work with Python 3.8+. Community Cloud automatically uses the latest supported Python version.

## 📁 Step 3: Repository Setup

### 3.1 Create GitHub Repository

1. **Create a new repository** on GitHub:
   - Go to [github.com](https://github.com)
   - Click "New repository"
   - Name it (e.g., "lambda-pro-streamlit")
   - Make it **public** (required for free Community Cloud)
   - Initialize with README

### 3.2 Upload Your Code

**Option A: Using Git Command Line**
```bash
# Clone your new repository
git clone https://github.com/yourusername/lambda-pro-streamlit.git
cd lambda-pro-streamlit

# Copy your application files
# Copy all files from your Lambda project Pro folder

# Add, commit, and push
git add .
git commit -m "Initial commit: Lambda Pro Streamlit app"
git push origin main
```

**Option B: Using GitHub Web Interface**
1. Use GitHub's "Upload files" feature
2. Drag and drop your entire project folder
3. Commit the changes

### 3.3 Repository Structure Verification

Ensure your GitHub repository has:
```
your-repo/
├── src/
│   ├── app_with_routing.py
│   ├── components/
│   ├── utils/
│   └── config/
├── requirements.txt
└── README.md
```

## 🌐 Step 4: Deploy to Streamlit Community Cloud

### 4.1 Access Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Authorize Streamlit to access your repositories

### 4.2 Create New App

1. Click **"New app"** or **"Create app"**
2. Fill in the deployment form:

   **Repository**: `yourusername/lambda-pro-streamlit`
   
   **Branch**: `main` (or your default branch)
   
   **Main file path**: `src/app_with_routing.py`
   
   **App URL**: Choose a custom URL (e.g., `lambda-pro-decision-tool`)

### 4.3 Advanced Settings (Optional)

Click **"Advanced settings"** if you need to:
- Set Python version (leave default for latest)
- Configure secrets (see Step 5)

### 4.4 Deploy

1. Click **"Deploy!"**
2. Wait for the build process (usually 2-5 minutes)
3. Monitor the build logs for any errors

## 🔐 Step 5: Configure Secrets (If Needed)

### 5.1 Secrets Management

If your app uses secrets (API keys, database credentials):

1. In your app dashboard, click **"Settings"**
2. Go to **"Secrets"**
3. Add your secrets in TOML format:

```toml
# Example secrets.toml format
[general]
debug_mode = false

[api]
openai_key = "your-api-key-here"
```

### 5.2 Accessing Secrets in Code

Your app already uses the correct pattern:
```python
try:
    debug_mode = st.secrets.get("debug_mode", False)
except:
    debug_mode = False
```

## 🚨 Step 6: Troubleshooting Common Issues

### 6.1 Import Errors

**Problem**: `ModuleNotFoundError`
**Solution**: 
- Check `requirements.txt` for missing dependencies
- Ensure all custom modules are in the repository
- Verify file paths and imports

### 6.2 Path Issues

**Problem**: File not found errors
**Solution**: Your app uses relative imports correctly:
```python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
```

### 6.3 Memory/Performance Issues

**Problem**: App runs slowly or crashes
**Solutions**:
- Your app already uses `@st.cache_data` decorators
- Session state is optimized with periodic cleanup
- Consider reducing data processing in real-time

### 6.4 Build Failures

**Problem**: Deployment fails during build
**Common fixes**:
1. Check requirements.txt syntax
2. Remove conflicting package versions
3. Ensure Python version compatibility

## 🔄 Step 7: Managing Updates

### 7.1 Automatic Redeployment

Community Cloud automatically redeploys when you:
- Push changes to your main branch
- Update requirements.txt
- Modify any tracked files

### 7.2 Manual Redeployment

1. Go to your app dashboard
2. Click **"Reboot app"** to restart
3. Click **"Delete app"** and redeploy for major changes

### 7.3 Monitoring Your App

- **Logs**: View real-time logs in the Community Cloud dashboard
- **Analytics**: Monitor usage and performance
- **Health**: Check app status and uptime

## 🎯 Step 8: Optimization Best Practices

### 8.1 Performance Optimization

Your app already implements:
- ✅ Caching with `@st.cache_data`
- ✅ Session state optimization
- ✅ Modular component structure
- ✅ Lazy loading of heavy computations

### 8.2 User Experience

- ✅ Loading states and progress indicators
- ✅ Error handling and user feedback
- ✅ Responsive design with columns
- ✅ Clean navigation system

### 8.3 Security

- ✅ Secrets management for sensitive data
- ✅ Input validation and sanitization
- ✅ No hardcoded credentials

## 📱 Step 9: Sharing Your App

### 9.1 App URL

Your deployed app will be available at:
```
https://your-app-name.streamlit.app
```

### 9.2 Custom Domain (Pro Feature)

For custom domains, you'll need Streamlit Cloud Pro.

### 9.3 Embedding

You can embed your app in websites using iframes:
```html
<iframe src="https://your-app-name.streamlit.app" width="100%" height="600"></iframe>
```

## 🆘 Getting Help

### Official Resources
- [Streamlit Documentation](https://docs.streamlit.io)
- [Community Cloud Status](https://status.streamlit.io)
- [Streamlit Forum](https://discuss.streamlit.io)

### Common Commands for Local Development
```bash
# Run locally
streamlit run src/app_with_routing.py

# Run on specific port
streamlit run src/app_with_routing.py --port 8501

# Run with debug mode
streamlit run src/app_with_routing.py --logger.level=debug
```

## ✅ Deployment Checklist

Before deploying, verify:

- [ ] Code is in a public GitHub repository
- [ ] `requirements.txt` is in the root directory
- [ ] Main app file path is correct (`src/app_with_routing.py`)
- [ ] No sensitive data is hardcoded
- [ ] All imports and dependencies are available
- [ ] App runs locally without errors
- [ ] File structure matches expected layout

## 🎉 Success!

Once deployed successfully, your Lambda Pro decision-making tool will be accessible worldwide at your Streamlit Community Cloud URL. The app features:

- **Multi-tab workflow** for structured decision analysis
- **Dynamic content** based on time allocation
- **MCDA evaluation** with weighted scoring
- **Scenario planning** with probability distributions
- **Data export/import** functionality
- **Responsive design** for various screen sizes

Your app is now ready to help users make better high-stakes corporate decisions! 🚀

---

*Last updated: November 2024*
*For questions or issues, refer to the troubleshooting section or Streamlit's official documentation.*
