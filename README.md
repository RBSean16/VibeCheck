# VibeCheck: A Journal for Your Mind, A Map for Your Mood

## Project Description

VibeCheck is a desktop mental health tracker designed to help users improve self-awareness and emotional wellness through mood logging, structured journaling, and personalized feedback. It empowers individuals to develop healthy mental habits and easily visualize their emotional trends over time, while also providing access to verified local support resources.

## Setup Instructions

Getting VibeCheck up and running is straightforward\! Follow these steps to set up the application on your computer.

### Step 1: Get the VibeCheck Code

First, you need to download the VibeCheck project files.

#### Clone the Repository

Open your terminal (or Command Prompt on Windows) and use Git to clone the repository:

```bash
git clone https://github.com/RBSean16/VibeCheck.git
```

#### Navigate to the Project Directory

Once cloned (or extracted), move into the VibeCheck project folder in your terminal:

```bash
cd VibeCheck
```

### Step 2: Set Up Your Python Environment

It's best practice to use a virtual environment for Python projects. This keeps VibeCheck's dependencies separate from other Python projects on your system, preventing potential conflicts.

#### Create a Virtual Environment

In your `VibeCheck` directory, run this command:

```bash
python -m venv venv
```

This creates a new folder named `venv` inside your project directory.

#### Activate the Virtual Environment

  * **On Ubuntu/macOS:**
    ```bash
    source venv/bin/activate
    ```
  * **On Windows (Command Prompt/PowerShell):**
    ```bash
    .\venv\Scripts\activate
    ```

*You'll know your virtual environment is active when you see `(venv)` at the beginning of your terminal prompt.*

### Step 3: Install Dependencies

With your virtual environment activated, you can now install all the Python libraries VibeCheck needs to run.

#### Install Python Dependencies

Run the following command in your activated terminal:

```bash
pip install flet fastapi "uvicorn[standard]" matplotlib seaborn pandas numpy
```

This command will download and install all the necessary packages.

## Running the Application

VibeCheck consists of two parts: a backend server and a frontend application. You'll need to run both simultaneously in separate terminal windows.

### Step 1: Start the Backend Server

Open a **new** terminal window. Navigate to your VibeCheck project directory, activate your virtual environment, and then run the backend server:

```bash
uvicorn UI:app --reload
```

### Step 2: Start the Frontend Application

Open **another separate** terminal window. Navigate to your VibeCheck project directory, activate your virtual environment, and then run the frontend:

```bash
python back.py
```

Once both the backend and frontend are running, the VibeCheck application window should appear, and you can start logging your moods and insights\!

## Team members and roles
   Joebert Axel Diana - Backend, Debugging
   
   Harvey Sean Siazon - Frontend, Backend, Documentation
   
   Zultan Sultan - Frontend, Debugging
