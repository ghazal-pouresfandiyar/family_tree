import json


class PersistenceManager:
    def save_structure(self, tree, file_path):
        data = {
            "root": {"name": tree.root.name, "id": tree.root.person_id} if tree.root else None,
            "people": [],
        }

        for person in tree.people.values():
            data["people"].append(
                {
                    "name": person.name,
                    "id": person.person_id,
                    "gender": person.gender,
                    "partner": {
                        "name": person.partner.name,
                        "id": person.partner.person_id,
                    }
                    if person.partner
                    else None,
                    "children": [{"name": child.name, "id": child.person_id} for child in person.children],
                }
            )

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_structure(self, tree, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        tree.people = {}
        tree.root = None

        for item in data.get("people", []):
            tree.get_or_create_person_with_gender(item.get("name", ""), item.get("id", 1), item.get("gender"))

        for item in data.get("people", []):
            name = item.get("name")
            person_id = item.get("id", 1)
            partner = item.get("partner")
            if name and partner:
                if isinstance(partner, str):
                    partner_name = partner
                    partner_id = 1
                else:
                    partner_name = partner.get("name")
                    partner_id = partner.get("id", 1)
                tree.set_partner(name, partner_name, person_id, partner_id)

        for item in data.get("people", []):
            parent_name = item.get("name")
            parent_id = item.get("id", 1)
            for child in item.get("children", []):
                if parent_name and child:
                    if isinstance(child, str):
                        child_name = child
                        child_id = 1
                    else:
                        child_name = child.get("name")
                        child_id = child.get("id", 1)
                    tree.add_child(parent_name, child_name, parent_id, child_id)

        root_data = data.get("root")
        if isinstance(root_data, str):
            tree.set_root(root_data, 1)
        elif root_data:
            tree.set_root(root_data.get("name"), root_data.get("id", 1))
