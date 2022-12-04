#!/usr/bin/env python3

import os, sys, subprocess
import re, json

assert os.path.samefile("./generate_help.py", __file__), "you need to run this from the repo root"

def main():
    import argparse
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    with open("README.md") as f:
        readme_contents = f.read()

    start_anchor = "<!--GEN_START-->\n"
    start_index = readme_contents.index(start_anchor) + len(start_anchor)
    end_index = readme_contents.index("<!--GEN_END-->\n")

    readme_contents = "".join([
        readme_contents[:start_index],
        get_generated_contents(),
        readme_contents[end_index:],
    ])
    with open("README.md", "w") as f:
        f.write(readme_contents)

def get_generated_contents():
    return "".join(line + "\n" for line in [
        "#### `something`",
        "",
        "some docs.",
    ])

if __name__ == "__main__":
    main()
