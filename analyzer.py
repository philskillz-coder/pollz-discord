import os
import matplotlib.pyplot as plt

directory = os.getcwd()
_dir = os.walk(directory)

fileCount = 0
line_count = 0
files: dict[str, int] = {}
fileContents: list[str] = []
exclude_dirs = "discord"

for subdir, dirs, dir_files in _dir:
    if "." in subdir:
        continue

    if exclude_dirs in subdir:
        continue

    for filename in dir_files:
        if filename.endswith(".pyc") or filename.endswith(".png") or filename.endswith(".ttf") or filename.endswith(
                ".dll"):
            continue

        fileCount += 1
        subdirectoryPath = os.path.abspath(subdir)  # get the path to your subdirectory

        filePath = os.path.join(subdirectoryPath, filename)  # get the path to your file
        with open(filePath, "r") as f:
            file_content = f.read()
            file_lines = len(file_content.split("\n"))
            files[filename] = file_lines
            line_count += file_lines
            fileContents.append(file_content)

folders: dict[str, int] = {}

for folder in os.listdir(directory):
    lines = 0

    pth = os.path.join(directory, folder)
    if not os.path.isdir(pth):
        continue

    if "." in folder:
        continue

    if exclude_dirs in folder:
        continue

    for subdir, dirs, dir_files in os.walk(pth):
        if "." in subdir:
            continue

        if exclude_dirs in subdir:
            continue

        for filename in dir_files:
            if filename.endswith(".pyc") or filename.endswith(".png") or filename.endswith(".ttf") or filename.endswith(
                    ".dll"):
                continue

            filePath = os.path.join(os.path.abspath(subdir), filename)
            with open(filePath) as f:
                lines += len(f.read().split("\n"))

    folders[folder] = lines

sorted_files = dict(sorted(files.items(), key=lambda _file: _file[1], reverse=True))
sorted_folders = dict(sorted(folders.items(), key=lambda _folder: _folder[1], reverse=True))

p_files: dict[str, float] = {}
p_folders: dict[str, float] = {}

print("%s Total files" % fileCount)
print("%s Total lines of code" % line_count)

for file, lines in sorted_files.items():
    pc = lines / line_count
    p_files[file] = round(pc * 100, 2)

for folder, lines in sorted_folders.items():
    pc = lines / line_count
    p_folders[folder] = round(pc * 100, 2)

mf = len(max(p_files.keys(), key=len))
for file, pc in p_files.items():
    print(f"FILE | {file}:{(mf - len(file)) * ' '} {pc}% \t | {round(pc / 100 * line_count)}")

print()
print()
print()

mfo = len(max(p_folders.keys(), key=len))
for file, pc in p_folders.items():
    print(f"FOLDER | {file}:{(mfo - len(file)) * ' '} {pc}% \t | {round(pc / 100 * line_count)}")


def list_files(base_path):
    for root, drs, fls in os.walk(base_path):
        if exclude_dirs in root:
            continue

        if "__pycache__" in root:
            continue

        level = root.replace(base_path, '').count(os.sep)
        indent = ' ' * 4 * level
        print('{}{}/'.format(indent, os.path.basename(root)))
        sub_indent = ' ' * 4 * (level + 1)
        for fil in fls:
            print('{}{}'.format(sub_indent, fil))


print()
print()
print()
