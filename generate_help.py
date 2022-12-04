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
    common_options = [
        "url",
        "follow-branch", "pin-to-tag", "pin-to-commit",
        "subdir", "include", "exclude",
    ]
    name_to_docs = {}

    output = subprocess.run(
        ["./git-vendor", "add", "--help"],
        env={"GIT_VENDOR_RAW_HELP_FORMATTING":"1", **os.environ},
        check=False, stdout=subprocess.PIPE,
    ).stdout.decode("utf8")

    for option_doc in re.findall(r'^  --.*(?:\n   .*)*', output, re.MULTILINE):
        name = re.search(r'--([a-z-]+) ', option_doc).group(1)
        name_is_done_index = option_doc.index("  ", 2)
        payload_start_index = re.compile(r'\S').search(option_doc, name_is_done_index).span()[0]
        payload_first_line_index = option_doc.rfind("\n", 0, payload_start_index)
        indentation = payload_start_index - (payload_first_line_index + 1)
        indented_payload = option_doc[payload_first_line_index + 1:]
        payload = "\n".join(
            line[indentation:].rstrip()
            for line in indented_payload.split("\n")
        )

        # Word wrapping is not a concern in markdown.
        payload = payload.replace("%2d", "-")
        # Markdown doesn't recognize this kind of sublist.
        payload = payload.replace(" 5a)", " 1) ")
        payload = payload.replace(" 5b)", " 2) ")
        payload = payload.replace(" 5c)", " 3) ")
        payload = payload.replace(" 5d)", " 4) ")
        # These inter-option references are written for cli documentation.
        payload = payload.replace("--include", "`include`")
        payload = payload.replace("--exclude", "`exclude`")

        if name == "subdir":
            # Add more documentation to this one that's specific to config files.
            payload += "".join("\n" + line for line in [
                "",
                "In the config file, this must be a *canonicalized relative path* (see above).",
            ])

        name_to_docs[name] = payload

    return "\n".join(
        "#### `{}`\n\n{}\n".format(name, name_to_docs[name])
        for name in common_options
    )

if __name__ == "__main__":
    main()
