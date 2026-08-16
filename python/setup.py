from setuptools import setup, find_packages

setup(
    name="code-alarm",
    version="1.0.0",
    description="Laptop Code-Completion Alarm: Physical USB buzzer notifier for VS Code and terminal.",
    packages=find_packages(),
    install_requires=[
        "pyserial>=3.5",
    ],
    entry_points={
        "console_scripts": [
            "code-alarm=code_alarm.cli:main",
        ],
    },
    python_requires=">=3.8",
)
