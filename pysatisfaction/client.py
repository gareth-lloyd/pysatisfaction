import requests, json

JSON_EXTENSION = '.json'

class Endpoint(object):
    def __init__(self, path, resource_type, parent=None):
        self.path = path
        self.resource_type = resource_type
        self.parent = parent

    def _base_url(self):
        parts = [self.parent._base_url(), self.path] if self.parent else [self.path]
        return u'/'.join(parts)

    def url(self):
        return self._base_url() + JSON_EXTENSION

    def _retrieve(self):
        response = requests.get(self.url())
        response = json.loads(response.content)
        print response
        return response


class ResourceEndpoint(Endpoint):
    def get(self):
        return self.resource_type(self._retrieve)


class CollectionEndpoint(Endpoint):
    """A collection endpoint can be called directly to retrieve multiple
    members of the collection, or narrowed by supplying a resource identifier.
    """
    def __init__(self, path, resource_type, parent=None):
        super(CollectionEndpoint, self).__init__(path, resource_type, parent)
        if parent:
            setattr(parent, self.path, self)

    def narrow(self, resource_id):
        return ResourceEndpoint(resource_id, resource_type=self.resource_type,
                parent=self)

    def all(self):
        return map(self.resource_type, self._retrieve())


class TopLevelCollectionEndpoint(CollectionEndpoint):
    """A 'top level' collection behaves slightly differently when narrowed:
    it customizes the returned ResourceEndpoint with additional attributes.

    This reflects the url structure of the GS API.
    """
    def narrow(self, resource_id):
        endpoint = super(TopLevelCollectionEndpoint, self).narrow(resource_id)
        self.resource_type.customize_endpoint(endpoint)
        return endpoint


class Resource(object):
    def __init__(self, object_dict):
        pass

    @staticmethod
    def customize_endpoint(endpoint, parent):
        """Endpoints are composed with a resource type. This hook allows the
        resource type to add attributes to the endpoint that represent possible
        refinements in the Get Satisfaction API.
        """
        pass

class Company(Resource):
    @staticmethod
    def customize_endpoint(endpoint, parent):
        if parent.is_top_level_collection():
            CollectionEndpoint('employees', resource_type=Person, parent=endpoint)
            CollectionEndpoint('products', resource_type=Product, parent=endpoint)
            CollectionEndpoint('topics', resource_type=Topic, parent=endpoint)
            CollectionEndpoint('tags', resource_type=Tag, parent=endpoint)


class Topic(Resource):
    @staticmethod
    def customize_endpoint(endpoint, parent):
        CollectionEndpoint('tags', resource_type=Tag, parent=endpoint)
        CollectionEndpoint('replies', resource_type=Reply, parent=endpoint)


class Person(Resource):
    @staticmethod
    def customize_endpoint(endpoint, parent):
        CollectionEndpoint('replies', resource_type=Reply, parent=endpoint)
        CollectionEndpoint('topics', resource_type=Topic, parent=endpoint)
        CollectionEndpoint('companies', resource_type=Company, parent=endpoint)


class Product(Resource):
    @staticmethod
    def customize_endpoint(endpoint, parent):
        CollectionEndpoint('topics', resource_type=Topic, parent=endpoint)


class Reply(Resource):
    pass


class Tag(Resource):
    pass


def _build_client():
    gs = Endpoint('https://api.getsatisfaction.com', resource_type=None, parent=None)
    TopLevelCollectionEndpoint('topics', resource_type=Topic, parent=gs)
    TopLevelCollectionEndpoint('people', resource_type=Person, parent=gs)
    TopLevelCollectionEndpoint('replies', resource_type=Reply, parent=gs)
    TopLevelCollectionEndpoint('products', resource_type=Product, parent=gs)
    TopLevelCollectionEndpoint('companies', resource_type=Company, parent=gs)
    TopLevelCollectionEndpoint('tags', resource_type=Tag, parent=gs)
    return gs

