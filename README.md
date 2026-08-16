# 🔔 Code Alarm V2

### Intelligent Developer Execution & Alert System

**Code Alarm** is a Windows-based developer productivity tool that monitors code and command execution in the background and alerts you when a task finishes, fails, crashes, or is terminated.

Instead of repeatedly checking the terminal to see whether a long-running program has completed, Code Alarm lets you continue working on other tasks while it monitors the execution for you.

> **Run your code. Get on with your work. Code Alarm tells you when it's done.**

---

## 🎯 Problem

Developers frequently run tasks that take seconds, minutes, or even hours:

- Machine learning training
- Flutter builds
- Large C/C++ compilations
- Data processing
- Python scripts
- npm builds
- Rust compilation
- Testing pipelines

The common workflow is:

```text
Start program
     ↓
Wait
     ↓
Check terminal
     ↓
"Is it finished?"
     ↓
Continue waiting
     ↓
Check again


On the Terminal:
n <your command>
       ↓
Code Alarm starts monitoring
       ↓
Command executes normally
       ↓
Code Alarm detects the result
       ↓
┌──────────┬──────────┬──────────┐
│ SUCCESS  │  FAILED  │  CRASHED │
└──────────┴──────────┴──────────┘
       ↓
Alert + Job History
       ↓
Failure Intelligence (if applicable)
