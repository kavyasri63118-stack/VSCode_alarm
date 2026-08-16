"""
Demo: VS Code Interactive Python / Jupyter Notebook Alarm.
This file can be opened directly in VS Code as an Interactive Python Script (using `# %%` cells).
"""

# %% [markdown]
# # 🔔 Laptop Code-Alarm in VS Code Interactive & Jupyter
# Load the extension with `%load_ext code_alarm`

# %%
import time
import sys
import os

# Load the Code-Alarm extension into this interactive session
get_ipython().run_line_magic('load_ext', 'code_alarm')

# %%
# Example 1: Use %%alarm on a specific cell
# It will only trigger the audio chime and desktop notification when the cell execution completes!

%%alarm -t "Data Loading"
print("⏳ Loading dataset into memory...")
time.sleep(2)
print("✅ Dataset loaded (10,000 rows).")

# %%
# Example 2: %%alarm with Spoken Voice Announcement
%%alarm -v -t "Model Training"
print("🧠 Training neural network...")
time.sleep(3)
print("🎯 Training converged with 99.2% accuracy!")

# %%
# Example 3: Global Auto-Alarm for the whole notebook
# Automatically alerts you for ANY cell taking >= 2 seconds!
%alarm_on --min 2

# %%
# This cell runs for 2.5s and automatically chimes & notifies upon completion:
print("🔄 Running long calculation...")
time.sleep(2.5)
print("✨ Done!")

# %%
# To turn off global auto-alarm:
%alarm_off
