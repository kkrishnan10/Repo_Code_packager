REPO_CODE_PACKAGER (Repository Context Packager)

REPO_CODE_PACKAGER is a command-line tool (CLI) that analyzes a local Git repository and generates a single, clean text file optimized for sharing with Large Language Models (LLMs). No more manually copy-pasting files when asking ChatGPT for help with your code!

The Problem

When developers ask LLMs for help with their code, the biggest challenge is providing enough context. Sharing snippets of code without the project's file structure, dependencies, and file relationships often leads to generic or unhelpful answers.

REPO_CODE_PACKAGER solves this by packaging all the essential information about your repository into one well-structured file, helping the LLM understand your project's architecture much more effectively.

Key Features
- Simple CLI Interface: Analyze your entire project, specific directories, or individual files with a single command.

- Project Structure Visualization: Automatically generates a tree view of your project's directory and file structure.

- Git Integration: Includes key Git metadata like the current branch and latest commit information.

- Save to File: Print the context directly to the console or use the -o option to save it to a .txt or .md file.

🛠️ Installation
Clone the repository:

```
git clone https://github.com/jongwan93/REPO_CODE_PACKAGER
cd REPO_CODE_PACKAGER
pip install Pygments
Set up and activate a virtual environment:
```

# Create a virtual environment
python -m venv venv

# Usage
The Basic command structure is 
```
python src/main.py [options] <paths>
```
- To analyze the entire current directory:
```
python src/main.py .
```
- To analyze specific directories or files:
```
python src/main.py [directory]
```

- To save the output to a file:
```
python src/main.py . -o output.txt
```

- For "help"
```
python src/main.py --help
```

- command may be updated later

- To only include files modified in the last 7 days:
  
python src/main.py . --recent

- Can be combined with `-o` to save output:
  
python src/main.py . -r -o recent.txt



# License
This project is licensed under the MIT License.

