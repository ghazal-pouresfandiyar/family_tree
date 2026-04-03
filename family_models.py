class Person:
    def __init__(self, name, person_id=1, gender=None):
        self.name = self.format_name(name)
        self.person_id = person_id
        self.gender = gender
        self.partner = None
        self.children = []

    @staticmethod
    def format_name(name):
        words = name.strip().split()
        return " ".join(word.capitalize() for word in words)
