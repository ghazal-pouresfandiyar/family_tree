import os

from family_tree import FamilyTree


def ask_yes_no(message):
    while True:
        ans = input(message).strip().lower()
        if ans in ["y", "yes"]:
            return True
        if ans in ["n", "no"]:
            return False
        print("Please enter y or n.")


def ask_gender(message):
    while True:
        ans = input(message).strip().lower()
        if ans in ["m", "male"]:
            return "male"
        if ans in ["f", "female"]:
            return "female"
        if ans == "":
            return None
        print("Please enter male/female (or m/f).")


def main():
    print("Family Tree Creator (Simple)")
    print("- Names are saved with first letter capital.")
    print("- Default person id is 1.")
    print("- In quick format, trailing number is id (example: Child 2 f).")
    print("- Quick format: Wife [id] & Husband [id] : Child [id] f, Child [id] m")
    print("- Input is read from tree.txt and the tree is drawn automatically.")

    tree = FamilyTree(image_folder="img", fallback_image="prof.jpeg")
    input_file = "tree.txt"
    data_file = "family_tree_data.json"
    output_name = "family_tree"

    if not os.path.exists(input_file):
        print(f"Could not find input file: {input_file}")
        return

    added_lines = 0
    with open(input_file, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            try:
                result = tree.add_relation_line(line)
                if result is not None:
                    added_lines += 1
                    print(
                        f"Added: {result['woman']} [{result['woman_id']}] & "
                        f"{result['man']} [{result['man_id']}] | "
                        f"children: {result['children_count']}"
                    )
            except Exception as e:
                print(f"Skipped line: {line}")
                print(f"Reason: {e}")

    if not tree.people:
        print("No valid family data was found in tree.txt.")
        return

    try:
        tree.save_structure(data_file)
        print(f"Saved structure to {data_file}")
    except Exception as e:
        print(f"Could not save structure: {e}")

    try:
        file_path = tree.export_png(output_name)
        print(f"Created: {file_path}")
    except Exception as e:
        print("Could not export image.")
        print("Install Graphviz app and Python package.")
        print(f"Error: {e}")

    print(f"Processed lines: {added_lines}")
