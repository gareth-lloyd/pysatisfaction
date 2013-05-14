"""
c = Client()
c.topics.all() # RC
c.topics.narrow(<topic name>).get() # RC/R
c.companies.narrow(<company name>).products.narrow(<product name>).topics.all() # RC/R/RC/R/RC
c.people.narrow(<user id>).topics.all() # RC/R/RC
c.people.narrow(<user id>).followed.topics.all() # RC/R/Subset?/RC
c.products.narrow(<product name>).topics.all() # RC/R/RC
c.replies.all() # RC
c.topics.narrow(<topic name>).replies.all() # RC/R/RC
c.people.narrow(<user id>).replies.all() # RC/R/RC
"""
import requests, json

JSON_EXTENSION = '.json'

class Endpoint(object):
    def __init__(self, path, resource_type, parent=None):
        self.path = path

        self.resource_type = resource_type
        resource_type.customize_endpoint(self)

        self.parent = parent
        if self.parent:
            setattr(self.parent, self.path, self)

    def _base_url(self):
        parts = [self.parent._base_url(), self.path] if self.parent else [self.path]
        return u'/'.join(parts)

    def url(self):
        return self._base_url() + JSON_EXTENSION

    def _retrieve(self):
        return json.loads(requests.get(self.url()).content)

class ResourceEndpoint(Endpoint):
    def get(self):
        return self.resource_type(self._retrieve)


class CollectionEndpoint(Endpoint):
    def narrow(self, resource_id):
        return ResourceEndpoint(resource_id, resource_type=self.resource_type,
                parent=self)

    def all(self):
        return map(self.resource_type, self._retrieve())


class Resource(object):
    def __init__(self, object_dict):
        pass

    @staticmethod
    def customize_endpoint(endpoint):
        pass


class GetSatisfaction(Resource):
    @staticmethod
    def customize_endpoint(endpoint):
        CollectionEndpoint('topics', resource_type=Topic, parent=endpoint)
        CollectionEndpoint('people', resource_type=Person, parent=endpoint)
        CollectionEndpoint('replies', resource_type=Reply, parent=endpoint)
        CollectionEndpoint('products', resource_type=Product, parent=endpoint)
        CollectionEndpoint('companies', resource_type=Company, parent=endpoint)
        CollectionEndpoint('tags', resource_type=Tag, parent=endpoint)


class Company(Resource):
    @staticmethod
    def customize_endpoint(endpoint):
        CollectionEndpoint('products', resource_type=Product, parent=endpoint)


class Topic(Resource):
    @staticmethod
    def customize_endpoint(endpoint):
        CollectionEndpoint('tags', resource_type=Tag, parent=endpoint)


class Person(Resource):
    @staticmethod
    def customize_endpoint(endpoint):
        CollectionEndpoint('replies', resource_type=Reply, parent=endpoint)
        CollectionEndpoint('topics', resource_type=Topic, parent=endpoint)
        CollectionEndpoint('companies', resource_type=Company, parent=endpoint)


class Product(Resource):
    @staticmethod
    def customize_endpoint(endpoint):
        CollectionEndpoint('topics', resource_type=Topic, parent=endpoint)


class Reply(Resource):
    pass


class Tag(Resource):
    pass


client = Endpoint('https://api.getsatisfaction.com', resource_type=GetSatisfaction, parent=None)

