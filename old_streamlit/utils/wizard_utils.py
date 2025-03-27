"""Utilities for the step-by-step wizard interface."""

import streamlit as st
import time
from typing import List, Callable, Dict, Any

class WizardStep:
    def __init__(self, title: str, description: str, render_func: Callable):
        """
        Initialize a step in the wizard.
        
        Args:
            title: Step title
            description: Step description
            render_func: Function that renders the step content
        """
        self.title = title
        self.description = description
        self.render_func = render_func
        self.is_complete = False
        self.validation_error = None

class Wizard:
    def __init__(self, name: str, steps: List[WizardStep]):
        """
        Create a wizard with multiple steps.
        
        Args:
            name: Wizard name
            steps: List of WizardStep objects
        """
        self.name = name
        self.steps = steps
        
        # Initialize wizard state in session if not exists
        if f"wizard_{name}_current_step" not in st.session_state:
            st.session_state[f"wizard_{name}_current_step"] = 0
        
        if f"wizard_{name}_data" not in st.session_state:
            st.session_state[f"wizard_{name}_data"] = {}
    
    @property
    def current_step_index(self) -> int:
        """Get the current step index."""
        return st.session_state.get(f"wizard_{self.name}_current_step", 0)
    
    @current_step_index.setter
    def current_step_index(self, value: int):
        """Set the current step index."""
        st.session_state[f"wizard_{self.name}_current_step"] = value
    
    @property
    def current_step(self) -> WizardStep:
        """Get the current step."""
        return self.steps[self.current_step_index]
    
    @property
    def is_first_step(self) -> bool:
        """Check if wizard is at the first step."""
        return self.current_step_index == 0
    
    @property
    def is_last_step(self) -> bool:
        """Check if wizard is at the last step."""
        return self.current_step_index == len(self.steps) - 1
    
    def get_data(self) -> Dict[str, Any]:
        """Get all wizard data."""
        return st.session_state.get(f"wizard_{self.name}_data", {})
    
    def set_data(self, key: str, value: Any):
        """Set a wizard data value."""
        if f"wizard_{self.name}_data" not in st.session_state:
            st.session_state[f"wizard_{self.name}_data"] = {}
        st.session_state[f"wizard_{self.name}_data"][key] = value
    
    def next_step(self):
        """Move to the next step."""
        if not self.is_last_step:
            self.current_step_index += 1
    
    def previous_step(self):
        """Move to the previous step."""
        if not self.is_first_step:
            self.current_step_index -= 1
    
    def go_to_step(self, index: int):
        """Go to a specific step by index."""
        if 0 <= index < len(self.steps):
            self.current_step_index = index
    
    def render(self):
        """Render the wizard interface."""
        # Display progress bar
        progress = self.current_step_index / (len(self.steps) - 1)
        st.progress(progress)
        
        # Display step number and title
        st.header(f"{self.current_step_index + 1}. {self.current_step.title}")
        st.write(self.current_step.description)
        
        # Render step content
        self.current_step.render_func()
        
        # Navigation buttons
        col1, col2, spacer, col3 = st.columns([1, 1, 3, 1])
        
        with col1:
            if not self.is_first_step:
                if st.button("⬅️ Önceki", key=f"prev_{self.name}"):
                    self.previous_step()
                    st.experimental_rerun()
        
        with col2:
            if not self.is_first_step and not self.is_last_step:
                if st.button("🏠 Ana Sayfa", key=f"home_{self.name}"):
                    self.current_step_index = 0
                    st.experimental_rerun()
        
        with col3:
            if not self.is_last_step:
                next_button = st.button("Sonraki ➡️", key=f"next_{self.name}")
                if next_button:
                    # Attempt to go to next step - validation should happen in the render_func
                    if not self.current_step.validation_error:
                        self.next_step()
                        st.experimental_rerun()
                    else:
                        st.error(self.current_step.validation_error)
            else:
                if st.button("🎉 Tamamla", key=f"finish_{self.name}", type="primary"):
                    st.balloons()
                    st.success("Tüm adımlar tamamlandı!")
                    # Additional completion logic can be added here

def show_step_indicator(wizard: Wizard):
    """
    Show a horizontal step indicator for the wizard.
    
    Args:
        wizard: The wizard object
    """
    cols = st.columns(len(wizard.steps))
    
    for i, step in enumerate(wizard.steps):
        with cols[i]:
            if i < wizard.current_step_index:
                # Completed step
                st.markdown(f"<div style='text-align: center; color: green;'>✓<br>{step.title}</div>", 
                           unsafe_allow_html=True)
            elif i == wizard.current_step_index:
                # Current step
                st.markdown(f"<div style='text-align: center; font-weight: bold;'>● <br>{step.title}</div>", 
                           unsafe_allow_html=True)
            else:
                # Future step
                st.markdown(f"<div style='text-align: center; color: gray;'>○<br>{step.title}</div>", 
                           unsafe_allow_html=True)
