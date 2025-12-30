# -*- coding: utf-8 -*-
"""
Performance monitoring utilities for Lambda Pro.
Simple performance tracking and optimization helpers.
"""

import time
import streamlit as st
from functools import wraps
from typing import Dict, Any, Callable, Optional
import logging


class PerformanceMonitor:
    """Simple performance monitoring for Lambda Pro."""
    
    @staticmethod
    def time_function(func_name: str = None):
        """
        Decorator to time function execution.
        
        Args:
            func_name: Optional custom name for the function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                
                execution_time = end_time - start_time
                name = func_name or func.__name__
                
                # Store timing in session state for debugging
                if "_performance_log" not in st.session_state:
                    st.session_state["_performance_log"] = []
                
                st.session_state["_performance_log"].append({
                    "function": name,
                    "execution_time": execution_time,
                    "timestamp": time.time()
                })
                
                # Keep only last 50 entries to avoid memory bloat
                if len(st.session_state["_performance_log"]) > 50:
                    st.session_state["_performance_log"] = st.session_state["_performance_log"][-50:]
                
                # Log slow functions (> 100ms)
                if execution_time > 0.1:
                    st.warning(f"⚠️ Slow function detected: {name} took {execution_time:.3f}s")
                
                return result
            return wrapper
        return decorator
    
    @staticmethod
    def get_performance_stats() -> Dict[str, Any]:
        """
        Get performance statistics from session state.
        
        Returns:
            Dictionary with performance statistics
        """
        log = st.session_state.get("_performance_log", [])
        if not log:
            return {"message": "No performance data available"}
        
        # Calculate statistics
        execution_times = [entry["execution_time"] for entry in log]
        function_counts = {}
        function_times = {}
        
        for entry in log:
            func_name = entry["function"]
            exec_time = entry["execution_time"]
            
            if func_name not in function_counts:
                function_counts[func_name] = 0
                function_times[func_name] = []
            
            function_counts[func_name] += 1
            function_times[func_name].append(exec_time)
        
        # Calculate averages
        function_averages = {
            func: sum(times) / len(times) 
            for func, times in function_times.items()
        }
        
        return {
            "total_calls": len(log),
            "average_time": sum(execution_times) / len(execution_times),
            "max_time": max(execution_times),
            "min_time": min(execution_times),
            "function_counts": function_counts,
            "function_averages": function_averages,
            "slowest_functions": sorted(
                function_averages.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
        }
    
    @staticmethod
    def clear_performance_log():
        """Clear the performance log."""
        if "_performance_log" in st.session_state:
            del st.session_state["_performance_log"]
    
    @staticmethod
    def show_cache_stats():
        """Show Streamlit cache statistics if available."""
        try:
            # This is a simple way to show cache info
            cache_stats = {}
            
            # Check if we have any cached functions
            if hasattr(st, '_cache_data_cache'):
                cache_stats["cache_data_entries"] = len(st._cache_data_cache)
            
            if cache_stats:
                st.info(f"📊 Cache Statistics: {cache_stats}")
            else:
                st.info("📊 Cache statistics not available")
                
        except Exception as e:
            st.info(f"📊 Cache statistics unavailable: {str(e)}")


def monitor_performance(func_name: str = None):
    """
    Convenience decorator for performance monitoring.
    
    Args:
        func_name: Optional custom name for the function
    """
    return PerformanceMonitor.time_function(func_name)


def show_performance_debug():
    """Show performance debugging information in sidebar."""
    with st.sidebar:
        if st.checkbox("🔍 Performance Debug", key="_perf_debug"):
            st.subheader("Performance Stats")
            
            stats = PerformanceMonitor.get_performance_stats()
            
            if "message" in stats:
                st.info(stats["message"])
            else:
                st.metric("Total Function Calls", stats["total_calls"])
                st.metric("Average Execution Time", f"{stats['average_time']:.3f}s")
                st.metric("Max Execution Time", f"{stats['max_time']:.3f}s")
                
                if stats["slowest_functions"]:
                    st.subheader("Slowest Functions")
                    for func, avg_time in stats["slowest_functions"]:
                        st.text(f"{func}: {avg_time:.3f}s avg")
                
                if st.button("Clear Performance Log"):
                    PerformanceMonitor.clear_performance_log()
                    st.rerun()
            
            # Show cache stats
            PerformanceMonitor.show_cache_stats()


def optimize_session_state():
    """
    Perform session state optimizations.
    Call this periodically to clean up memory.
    """
    from utils.session_manager import cleanup_session, validate_session
    
    # Clean up empty lists and temporary data
    cleanup_session()
    
    # Validate data integrity (silent - no user-facing warnings)
    errors = validate_session()
    
    # Clear old performance logs
    if "_performance_log" in st.session_state:
        log = st.session_state["_performance_log"]
        if len(log) > 100:  # Keep only recent entries
            st.session_state["_performance_log"] = log[-50:]
