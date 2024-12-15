@echo off

if NOT EXIST "venv" (
    echo No venv found. Creating...
    python -m venv venv

    if %ERRORLEVEL% GEQ 1 (
        echo Failed to create virtual environment!
        EXIT /B 1
    )
)

call venv\\Scripts\\activate.bat
if %ERRORLEVEL% GEQ 1 (
    echo Failed to activate virtual environment!
    EXIT /B 1
)

if "%VIRTUAL_ENV%" == "" (
    echo Virtual environment not active!
    EXIT /B 1
)

if "%1" == "install" (
    python -m pip install -r requirements.txt
    if %ERRORLEVEL% GEQ 1 (
        echo Failed to install editable libraries!
        EXIT /B 1
    )

    python -m pip install .
    if %ERRORLEVEL% GEQ 1 (
        echo Failed to install project!
        EXIT /B 1
    )
)

:: Changes folders in venv/src from dashes to undescore
python "scripts\\helper\\src_fix.py"
if %ERRORLEVEL% GEQ 1 (
    echo Failed to fix src paths!
    EXIT /B 1
)

:: When pip installs editable modules via setuptools, it applies PEP 503
:: (https://peps.python.org/pep-0503/#normalized-names). This requires modules'
:: names to be "normalized" form for web/system compatibility. Unfortunately,
:: setuptools applies this to the module directory as well, causing python
:: imports to break. Setuptools fixes this via the __editable__.* python hooks
:: in venv, which depends on specific directories contiaining dashes. As such,
:: the renaming above breaks python imports. This is solved by creating another
:: python hook below to fix the search paths.
::
:: NOTE: Assumes nothing else generates sitecustomize.py
set hook_file=%VIRTUAL_ENV%\Lib\site-packages\sitecustomize.py
del /Q "%hook_file%"

:: Create a 'sitecustomize.py' file
:: Python automatically runs this before importing any modules
:: This edits paths to allow module import from workspace root
::
:: NOTE: '^' is used to escape the parenthesis
echo import sys > "%hook_file%"
echo sys.path.insert^(0, f'{sys.prefix}\\src'^) >> "%hook_file%"

if NOT EXIST "%hook_file%" (
    echo Failed to create sitecustomize.py!
    EXIT /B 1
)

echo [ DONE ]
