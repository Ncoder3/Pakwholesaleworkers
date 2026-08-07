from pathlib import Path

# Folders you don't want to expand
IGNORE = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
}

def print_tree(directory, prefix=""):
    directory = Path(directory)

    if not directory.exists():
        print(f"Directory not found: {directory}")
        return

    items = sorted(
        [item for item in directory.iterdir() if item.name not in IGNORE],
        key=lambda x: (x.is_file(), x.name.lower())
    )

    for index, item in enumerate(items):
        connector = "└── " if index == len(items) - 1 else "├── "
        print(prefix + connector + item.name)

        if item.is_dir():
            extension = "    " if index == len(items) - 1 else "│   "
            print_tree(item, prefix + extension)


# Your project folder
project_path = r"C:\Users\HB LAPTOP POINT\OneDrive\Desktop\KStore\AlBarakaCatalogGenerator"

print(project_path)
print_tree(project_path)