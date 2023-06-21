
from tdw.librarian import SceneLibrarian
lib = SceneLibrarian(library="scenes.json")
for record in lib.records:
    print(record.name)