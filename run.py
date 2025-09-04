import os
import sys
import subprocess

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(base_dir, "venv")
    main_script = os.path.join(base_dir, "scripts", "main.py")

    # Create venv only if it doesn't exist
    if not os.path.isdir(venv_dir):
        print("Creating virtual environment with system site packages...")
        subprocess.check_call([sys.executable, "-m", "venv", "--system-site-packages", venv_dir])
        print("Virtual environment created.")
    else:
        print("Virtual environment already exists. Using existing one.")

    # Determine the python executable inside the venv
    if os.name == "nt":
        python_executable = os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        python_executable = os.path.join(venv_dir, "bin", "python")

    # Upgrade pip inside venv
    print("Upgrading pip inside virtual environment...")
    subprocess.check_call([python_executable, "-m", "pip", "install", "--upgrade", "pip"])

    # Install requirements if requirements.txt exists
    reqs_path = os.path.join(base_dir, "requirements.txt")
    if os.path.isfile(reqs_path):
        print("Installing Python package requirements...")
        subprocess.check_call([python_executable, "-m", "pip", "install", "-r", reqs_path])

    # Run main.py inside venv
    print("Running main.py inside virtual environment...")
    subprocess.check_call([python_executable, main_script])

if __name__ == "__main__":
    main()
