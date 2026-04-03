import re


class RelationshipParser:
    @staticmethod
    def parse_gender_tag(token):
        value = token.strip().lower()
        if value in ["f", "female"]:
            return "female"
        if value in ["m", "male"]:
            return "male"
        return None

    @staticmethod
    def parse_name_with_id(value):
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Name cannot be empty.")

        parts = cleaned.split()
        if len(parts) >= 2 and parts[-1].isdigit():
            person_id = int(parts[-1])
            name = " ".join(parts[:-1]).strip()
            if not name:
                raise ValueError("Name before id is required.")
            if person_id < 1:
                raise ValueError("Id must be >= 1.")
            return name, person_id

        return cleaned, 1

    def parse_relation_line(self, line):
        raw = line.strip()
        if not raw:
            return None

        match = re.match(r"^(.+?)\s+&\s+(.+?)\s*:\s*(.*)$", raw, flags=re.IGNORECASE)
        if not match:
            raise ValueError("Invalid format. Use: Wife [id] & Husband [id] : Child [id] f, Child [id] m")

        woman_raw = match.group(1).strip()
        man_raw = match.group(2).strip()
        children_raw = match.group(3).strip()

        if not woman_raw or not man_raw:
            raise ValueError("Woman and man names are required.")

        woman_name, woman_id = self.parse_name_with_id(woman_raw)
        man_name, man_id = self.parse_name_with_id(man_raw)

        children = []
        if children_raw and children_raw != "0":
            parts = [p.strip() for p in children_raw.split(",") if p.strip()]
            for part in parts:
                words = part.split()
                gender = None
                child_text = part
                if len(words) >= 2:
                    last_gender = self.parse_gender_tag(words[-1])
                    if last_gender is not None:
                        gender = last_gender
                        child_text = " ".join(words[:-1]).strip()

                if not child_text:
                    continue
                child_name, child_id = self.parse_name_with_id(child_text)
                children.append((child_name, child_id, gender))

        return woman_name, woman_id, man_name, man_id, children

    def add_relation_line(self, tree, line):
        parsed = self.parse_relation_line(line)
        if parsed is None:
            return None

        woman_name, woman_id, man_name, man_id, children = parsed

        woman = tree.get_or_create_person_with_gender(woman_name, woman_id, "female")
        man = tree.get_or_create_person_with_gender(man_name, man_id, "male")
        tree.set_partner(woman.name, man.name, woman.person_id, man.person_id)

        for child_name, child_id, child_gender in children:
            child = tree.get_or_create_person_with_gender(child_name, child_id, child_gender)
            tree.add_child(woman.name, child.name, woman.person_id, child.person_id)

        if tree.root is None:
            tree.root = woman

        return {
            "woman": woman.name,
            "woman_id": woman.person_id,
            "man": man.name,
            "man_id": man.person_id,
            "children_count": len(children),
        }
