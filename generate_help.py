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

    docs_start_anchor = "<!--GEN_DOCS_START-->\n"
    docs_start_index = readme_contents.index(docs_start_anchor) + len(docs_start_anchor)
    docs_end_index = readme_contents.index("<!--GEN_DOCS_END-->\n")

    readme_contents = "".join([
        readme_contents[:docs_start_index],
        get_docs_contents(),
        readme_contents[docs_end_index:],
    ])

    toc_start_anchor = "<!--GEN_TOC_START-->\n"
    toc_start_index = readme_contents.index(toc_start_anchor) + len(toc_start_anchor)
    toc_end_index = readme_contents.index("<!--GEN_TOC_END-->\n")

    readme_contents = "".join([
        readme_contents[:toc_start_index],
        get_toc_contents(readme_contents),
        readme_contents[toc_end_index:],
    ])

    with open("README.md", "w") as f:
        f.write(readme_contents)

def get_docs_contents():
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

def get_toc_contents(readme_contents):
    items = [
        # (level, title, fragment),
        # (2, "Version History", "version-history"),
    ]
    for hashes, title in re.findall(r'^(#+) (.+)$', readme_contents, re.MULTILINE):
        level = len(hashes)
        if level == 1:
            # don't need to link to the main title of the page.
            continue

        # if the title is a link, get the text of the link.
        match = re.match(r'^\[(.*?)\]\(.*\)$', title)
        if match != None:
            title = match.group(1)

        # the #something part of the url is derrived from the title.
        fragment = title.lower()
        fragment = re.sub(r'\s+', "-", fragment)
        fragment = re.sub(r'[^0-9A-Za-z_-]', "", fragment)

        items.append((level, title, fragment))

    assert len(items) == len(set(fragment for (_, _, fragment) in items)), "fragment link collision"

    level_stack = []
    lines = []
    for level, title, fragment in items:
        if len(level_stack) == 0 or level_stack[-1] < level:
            level_stack.append(level)
        elif level_stack[-1] == level:
            pass
        else:
            while level_stack[-1] > level:
                level_stack.pop()
            # assert we didn't skip a level on the way down that we didn't skip on the way up.
            # e.g. 1, 3, 2
            assert level_stack[-1] == level, "inconsistent heading level skipping"
        lines.append("{}* [{}](#{})".format("    " * (len(level_stack) - 1), title, fragment))

    return "".join(line + "\n" for line in lines)

if __name__ == "__main__":
    main()
