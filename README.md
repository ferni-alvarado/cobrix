# Cobrix

## 🐍 Language

- **Language**: Python
- **Python version**: `3.11.9`

### 🔧 Environment Setup

To install and use the required Python version with [`pyenv`](https://github.com/pyenv/pyenv):

```bash
# Install Python 3.11.9
pyenv install 3.11.9

# Set Python version locally (creates a .python-version file)
pyenv local 3.11.9
```

## ⚙️ Virtual Environment

### 🔹 Activate the virtual environment

```bash
# On macOS / Linux:
source venv/bin/activate

# On Windows (CMD):
venv\Scripts\activate

# On Windows (PowerShell):
.\venv\Scripts\Activate
```

### Verify the environment is active
```bash
which python
```

- **macOS/Linux:** should return something like
`/your-project-path/venv/bin/python`

- **Windows:** should return something like
`...\venv\Scripts\python.exe`


### 📦 Install dependencies
```bash
pip install -r requirements.txt
```


