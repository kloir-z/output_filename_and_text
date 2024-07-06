@echo off
cd %~dp0
call venv\Scripts\activate

for %%f in (*.py) do (
    python "%%f"
    goto :end
)

:end
pause
