import names
import random


class Student:
    def __init__(self):
        self.name = names.get_full_name()
        self.year = random.randint(1, 5)
