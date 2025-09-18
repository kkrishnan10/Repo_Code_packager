# main.py
import argparse
import sys
import os
import subprocess
from pygments.lexers import guess_lexer_for_filename
from pygments.util import ClassNotFound

TOOL_VERSION = "0.1.0"

# find the files and directory
# Issue #2 Fix: Return absolute paths [9/14/2025]
def get_all_files(paths):
    all_files = []
    excluded_dirs = {'venv'} # maybe match with .gitignore

    for path in paths:
        # Convert the input path to an absolute path
        abs_path = os.path.abspath(path)
        # if the path leads to file, add it to list
        if os.path.isfile(abs_path):
            if not os.path.basename(abs_path).startswith('.'):
                all_files.append(abs_path)
        # if the path is directory, add all the files under it
        elif os.path.isdir(abs_path):
            for root, dirs, files in os.walk(abs_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in excluded_dirs]
                for file in files:
                    if not file.startswith('.'):
                        all_files.append(os.path.join(root, file))
    return all_files

# execute git commands and get newest commit and branch name
def get_git_info(repo_path):
    try:
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo_path, text=True, stderr=subprocess.PIPE).strip()
        branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=repo_path, text=True, stderr=subprocess.PIPE).strip()
        author = subprocess.check_output(['git', 'log', '-1', '--pretty=format:%an <%ae>'], cwd=repo_path, text=True, stderr=subprocess.PIPE).strip()
        date = subprocess.check_output(['git', 'log', '-1', '--pretty=format:%ad'], cwd=repo_path, text=True, stderr=subprocess.PIPE).strip()
    
        return (
            f"- Commit: {commit}\n"
            f"- Branch: {branch}\n"
            f"- Author: {author}\n"
            f"- Date: {date}")
    
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "Not a git repository"

# create tree structure reflecting depth of file and directories
def create_structure_tree(file_list, base_path):
    tree = {}
    for file_path in file_list:
        relative_path = os.path.relpath(file_path, base_path)
        parts = relative_path.split(os.sep)

        current_level = tree
        for part in parts[:-1]:
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]
        current_level[parts[-1]] = None

    def generate_tree_string(d, indent=''):
        lines = []
        # Sort items to make the output consistent every time.
        items = sorted(d.items())
        for i, (name, content) in enumerate(items):
            is_last = i == len(items) - 1
            prefix = '└── ' if is_last else '├── '
            lines.append(f"{indent}{prefix}{name}")
            if isinstance(content, dict): # If it's a directory, go one level deeper.
                connector = '    ' if is_last else '│   '
                lines.extend(generate_tree_string(content, indent + connector))
        return lines
    return "\n".join(generate_tree_string(tree))

# gather the file contents and merge into a big string block.
def format_file_contents(file_list, base_path):
    all_contents = []
    total_lines = 0
    total_chars = 0
    MAX_FILE_SIZE_KB = 16
    MAX_BYTES = MAX_FILE_SIZE_KB * 1024

    for file_path in sorted(file_list):
        try:
            file_size = os.path.getsize(file_path)
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                relative_path = os.path.relpath(file_path, base_path)
                all_contents.append(f"### File: {relative_path}")
                
                content = f.read()

                if file_size > MAX_BYTES:
                    content = content[:MAX_BYTES]
                    truncation_note = f"\n... (file truncated due to size > {MAX_FILE_SIZE_KB}KB)"
                    content += truncation_note

                lang_name = ""
                try:
                    # find the language from file name
                    lexer = guess_lexer_for_filename(file_path, content)
                    lang_name = lexer.aliases[0] if lexer.aliases else ""
                except ClassNotFound:
                    # if it failes to find language name
                    pass

                # Add the content inside a markdown code block.
                all_contents.append(f"```{lang_name}\n{content}\n```")
                
                # Count lines for the summary later.
                total_lines += content.count('\n') + 1
                total_chars += len(content)

        except Exception as e:
            print(f"Error reading file {file_path}: {e}", file=sys.stderr)
    return "\n\n".join(all_contents), total_lines, total_chars

# calculate entire number of files and number of lines.
def generate_summary(file_list, total_lines):
    file_count = len(file_list)
    summary_string = (
        f"- Total files: {file_count}\n"
        f"- Total lines: {total_lines}"
    )
    return summary_string
from datetime import datetime, timedelta

def is_recently_modified(file_path, days=7):
    try:
        last_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
        return datetime.now() - last_modified <= timedelta(days=days)
    except FileNotFoundError:
        return False

def main():
    # ArgumentParser object creation
    parser = argparse.ArgumentParser(
        description="Repository Context Packager"
    )

    parser.add_argument(
        "-v", "--version",
        action = "version",
        version = f"%(prog)s {TOOL_VERSION}"
    )

    # file or directory argument
    parser.add_argument(
        "paths",
        nargs = "+", # 1 or more
        help = "Paths to files or directories to include in the context."
    )

    # optional feature 1: Output to file
    parser.add_argument(
        "-o", "--output",
        help = "Path to the output file. If not specified, prints to standard output."
    )

    # optional feature 2: Token counting
    parser.add_argument(
        "--tokens",
        action = "store_true", #This makes it a flag, like --version
        help = "Estimate and display the token count for the context."
    )
        parser.add_argument(
        "-r", "--recent",
        action="store_true",
        help="Only include files modified in the last 7 days."
    )

    # pare the argument
    args = parser.parse_args()

    first_path_abs = os.path.abspath(args.paths[0])
    base_path = os.path.dirname(first_path_abs) if os.path.isfile(first_path_abs) else first_path_abs

    # get all the files from provided path
    file_list = get_all_files(args.paths)

    if args.recent:
        file_list = [f for f in file_list if is_recently_modified(f, 7)]


    if not file_list:
        print("Error: No files found in the specified paths.", file=sys.stderr)
        sys.exit(1)

    git_info_str = get_git_info(base_path)
    structure_tree_str = create_structure_tree(file_list, base_path)
    file_contents_str, total_lines, total_chars = format_file_contents(file_list, base_path)
    summary_str = generate_summary(file_list, total_lines)

    final_output = f"""# Repository Context

## File System Location

{base_path}

## Git Info

{git_info_str}

## Structure

{structure_tree_str}

    recent_section = ""
    if args.recent:
        recent_section = "## Recent Changes\n"
        if file_list:
            for f in file_list:
                days_ago = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(f))).days
                recent_section += f"- {os.path.relpath(f, base_path)} (modified {days_ago} days ago)\n"
        else:
            recent_section += "No files modified in the last 7 days.\n"

    final_output = f"""# Repository Context

## File System Location

{base_path}

## Git Info

{git_info_str}

## Structure

{structure_tree_str}

{recent_section}

## File Contents

{file_contents_str}

## Summary

{summary_str}
"""

## File Contents

{file_contents_str}

## Summary

{summary_str}
"""
    
    # optional feature 2: Token counting
    if args.tokens:
        estimated_tokens = total_chars // 4
        print(f"Estimated tokens: {estimated_tokens}", file=sys.stderr)

    # optional feature 1: Output to file
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(final_output.strip())
            print(f"Context successfully written to {args.output}", file=sys.stderr)
        except IOError as e:
            print(f"Error writing to file {args.output}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # If -o is not used, print to stdout as before.
        print(final_output.strip())

if __name__ == "__main__":
    main()
