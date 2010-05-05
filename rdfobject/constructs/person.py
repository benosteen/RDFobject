from rdfobject import RDFobject, URIHelper, NAMESPACES

class Person(object):
    def __init__(self, entity):
        self.t = entity
    
    def create_person_framework(self):
        """Set up the object so that it can support a person model. Don't use on a non-empty object"""
        self.t.set_type("foaf:Person")
        
    def _load_from_entity(self):
        pass
    
    def create_new_persona(self):
        return "new persona rdfobject"
    
    
        
