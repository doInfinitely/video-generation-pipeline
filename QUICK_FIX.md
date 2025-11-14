# Quick Fix for OpenAI Version Issue

You're getting the error because the OpenAI library version is outdated.

## Fix Steps

### Option 1: Use Virtual Environment (Recommended)

```bash
# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-minimal.txt

# Now run the test
python test_play_by_play.py
```

### Option 2: Upgrade in Conda Environment

```bash
# Upgrade just the OpenAI package
pip install --upgrade openai

# Now run the test
python test_play_by_play.py
```

### Option 3: Use Conda Environment

```bash
# Deactivate base and create a new environment
conda deactivate
conda create -n video-gen python=3.10
conda activate video-gen

# Install dependencies
pip install -r requirements-minimal.txt

# Run the test
python test_play_by_play.py
```

## What Happened?

The OpenAI SDK had breaking changes between versions. The old version (1.3.7) used different initialization parameters than newer versions. I've updated the requirements to use version 1.40.0+.

## Verify Installation

After upgrading, check the version:

```bash
python -c "import openai; print(openai.__version__)"
```

Should show version 1.40.0 or higher.

