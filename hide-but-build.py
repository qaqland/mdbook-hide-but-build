import json
import sys
import glob
import os


def parse_book(items) -> dict[str, str]:
    """
    parse book['sections'] to dict.
    here we use source_path as key to find other file
    """
    chapters: dict[str, str] = {}
    for c_item in items:
        if type(c_item) != dict:
            continue
        if "Chapter" not in c_item.keys():
            continue
        item = c_item["Chapter"]
        chapters[item["source_path"]] = item["name"]
        if item["sub_items"] is not None:
            chapters |= parse_book(item["sub_items"])
    return chapters


def parse_ctx(context) -> tuple[str, str]:
    src = context["config"]["book"]["src"]
    title = context["config"]["book"]["title"]
    return src, title


def find_md_in(src_path: str) -> list[str]:
    """
    find all md files in src_path and its subdir
    excluding files from SUMMARY.md
    """
    chapter_hides: list[str] = []
    for file in glob.glob(src_path + "/**/*.md", recursive=True):
        file_path = file[len(src_path) + 1 :].replace("\\", "/")
        if file_path not in chapters:
            chapter_hides.append(file_path)
    return chapter_hides


def chapter_new(path: str, book_title: str, book_src: str = "src"):
    """
    create a new hiden chapter and add its source_path to chapters:dict
    """
    # page content
    with open(book_src + "/" + path, "r", encoding="utf-8") as f:
        content = f.read()

    # page title
    page_h1 = "No Title"
    for line in content.split("\n"):
        if line.startswith("#"):
            page_h1 = line.strip("#").strip()
            break
    page_title = f"{{{{#title {page_h1} - {book_title}}}}}\n"

    # page to chapter
    chapters[path] = page_h1

    # page new
    return {
        "name": "",
        "content": page_title + content,
        "number": None,
        "sub_items": [],
        "source_path": path,
        "path": path,
        "parent_names": [],
    }


def all_pages():
    alpha = sorted(chapters.items(), key=lambda s: s[1].lower())
    content = "# ALL PAGES\n"
    for item in alpha:
        (path, title) = item
        if os.path.basename(path) == "README.md":
            path = os.path.dirname(path) + "/index.md"
        content += f"- [{title}]({path})\n"
    return {
        "name": "ALL PAGES",
        "content": content,
        "number": None,
        "sub_items": [],
        "source_path": "",
        "path": "allpages.md",
        "parent_names": [],
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:  # we check if we received any argument
        if sys.argv[1] == "supports":
            sys.exit(0)

    context, book = json.load(sys.stdin)

    src, book_title = parse_ctx(context)
    chapters = parse_book(book["sections"])
    chapter_hides = find_md_in(src)

    if chapter_hides is None:
        print(json.dumps(book))
        sys.exit(0)

    new_chapter = []

    for item_path in chapter_hides:
        new_chapter.append({"Chapter": chapter_new(item_path, book_title)})

    book["sections"].append({"Chapter": all_pages()})
    book["sections"].extend(new_chapter)

    with open("debug.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(book, indent=4))

    # we are done with the book's modification, we can just print it to stdout,
    print(json.dumps(book))
