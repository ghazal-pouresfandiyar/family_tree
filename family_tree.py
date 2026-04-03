from family_models import Person
from family_graph import GraphBuilder
from family_image import ImageManager
from family_parser import RelationshipParser
from family_persistence import PersistenceManager


class FamilyTree:
    def __init__(self, image_folder="img", fallback_image="prof.jpeg"):
        self.people = {}
        self.root = None
        self.image_node_width = 28
        self.image_node_height = 28

        self.image_manager = ImageManager(
            image_folder=image_folder,
            fallback_image=fallback_image,
            image_node_width=self.image_node_width,
            image_node_height=self.image_node_height,
        )
        self.parser = RelationshipParser()
        self.persistence = PersistenceManager()
        self.graph_builder = GraphBuilder(self.image_manager)

    def _key(self, name, person_id=1):
        return (name.strip().lower(), int(person_id))

    def _node_id(self, person):
        return f"{person.name}#{person.person_id}"

    def has_person(self, name, person_id=1):
        return self._key(name, person_id) in self.people

    def get_or_create_person(self, name, person_id=1):
        key = self._key(name, person_id)
        if key not in self.people:
            self.people[key] = Person(name, person_id=person_id)
        return self.people[key]

    def get_or_create_person_with_gender(self, name, person_id=1, gender=None):
        person = self.get_or_create_person(name, person_id=person_id)
        if person.gender is None and gender in ["male", "female"]:
            person.gender = gender
        return person

    def set_root(self, name, person_id=1):
        self.root = self.get_or_create_person(name, person_id=person_id)

    def set_partner(self, person_name, partner_name, person_id=1, partner_id=1):
        person = self.get_or_create_person(person_name, person_id=person_id)
        partner = self.get_or_create_person(partner_name, person_id=partner_id)
        person.partner = partner
        partner.partner = person

    def add_child(self, parent_name, child_name, parent_id=1, child_id=1):
        parent = self.get_or_create_person(parent_name, person_id=parent_id)
        child = self.get_or_create_person(child_name, person_id=child_id)

        if child not in parent.children:
            parent.children.append(child)

        if parent.partner is not None and child not in parent.partner.children:
            parent.partner.children.append(child)

    def add_relation_line(self, line):
        return self.parser.add_relation_line(self, line)

    def parse_relation_line(self, line):
        return self.parser.parse_relation_line(line)

    def save_structure(self, file_path):
        self.persistence.save_structure(self, file_path)

    def load_structure(self, file_path):
        self.persistence.load_structure(self, file_path)

    def build_graph(self):
        return self.graph_builder.build_graph(self)

    def export_png(self, output_name="family_tree"):
        return self.graph_builder.export_png(self, output_name)


if __name__ == "__main__":
    from family_cli import main as cli_main

    cli_main()
