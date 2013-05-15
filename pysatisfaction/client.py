import requests, json

JSON_EXTENSION = '.json'

class Endpoint(object):
    def __init__(self, path, resource_type, parent=None):
        self._path = path
        self.resource_type = resource_type
        self.parent = parent
        if parent:
            setattr(parent, path, self)

    @property
    def path(self):
        return self._path

    @property
    def url(self):
        base = self.parent._parent_url() if self.parent else ''
        path = self.path + JSON_EXTENSION
        parts = [base, path] if base else [path]
        return '/'.join(parts)

    @property
    def single_result(self):
        return True

    def _parent_url(self):
        if not self.single_result:
            raise ValueError('tried to traverse without enough information')
        parts = [self.parent._parent_url(), self.path] if self.parent else [self.path]
        return u'/'.join(parts)


class FilterableEndpoint(Endpoint):
    def __init__(self, path, resource_type, parent=None):
        super(FilterableEndpoint, self).__init__(path, resource_type, parent)
        self.resource_id = ''

    @property
    def path(self):
        r_id = self.resource_id
        return self._path + '/' + r_id if r_id else self._path

    @property
    def single_result(self):
        return bool(self.resource_id)

    def __call__(self, resource_id):
        self.resource_id = resource_id
        return self


class Resource(object):
    def __init__(self, object_dict):
        pass

class Company(Resource):
    pass

class Topic(Resource):
    pass

class Person(Resource):
    pass

class Product(Resource):
    pass

class Reply(Resource):
    pass

class Comment(Resource):
    pass

class Tag(Resource):
    pass


def build_api():
    root = Endpoint('https://api.getsatisfaction.com', None, None)

    FilterableEndpoint('companies', Company, parent=root)
    FilterableEndpoint('products', Product, parent=root)
    FilterableEndpoint('topics', Topic, parent=root)
    FilterableEndpoint('people', Person, parent=root)
    FilterableEndpoint('replies', Reply, parent=root)
    FilterableEndpoint('tags', Tag, parent=root)

    Endpoint('employees', Person, parent=root.companies)
    FilterableEndpoint('products', Product, parent=root.companies)
    Endpoint('topics', Topic, parent=root.companies.products)
    Endpoint('tags', Tag, parent=root.companies)
    Endpoint('topics', Topic, parent=root.companies.tags)
    FilterableEndpoint('topics', Topic, parent=root.companies)
    Endpoint('people', Person, parent=root.companies)

    Endpoint('products', Product, parent=root.people)
    Endpoint('followed/topics', Topic, parent=root.people)
    Endpoint('replies', Reply, parent=root.people)
    Endpoint('topics', Topic, parent=root.people)
    Endpoint('companies', Company, parent=root.people)

    Endpoint('companies', Company, parent=root.products)
    Endpoint('topics', Topic, parent=root.products)

    Endpoint('comments', Company, parent=root.replies)

    Endpoint('people', Person, parent=root.topics)
    Endpoint('products', Product, parent=root.topics)
    Endpoint('comments', Comment, parent=root.topics)
    Endpoint('replies', Reply, parent=root.topics)

    return root


class GSClient(object):
    def __init__(self, get_satisfaction):
        self.get_satisfaction = get_satisfaction

    def fetch(self, endpoint, **kwargs):
        response = requests.get(endpoint.url, params=kwargs)
        response.raise_for_status()

        if endpoint.single_result:
            return endpoint.resource_type(json.loads(response.content))
        else:
            model_dicts = json.loads(response.content)['data']
            return map(endpoint.resource_type, model_dicts)


class APIManager(object):
    def __init__(self, get_satisfaction):
        self.get_satisfaction = get_satisfaction

    def __enter__(self):
        return build_api(), GSClient(self.get_satisfaction)

    def __exit__(self, exc_type, exc_value, traceback):
        pass


class GetSatisfaction(object):
    def __init__(self):
        pass

    def api_call(self):
        return APIManager(self)

