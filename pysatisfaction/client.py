import requests, json
from urlparse import parse_qs

from oauth_hook import OAuthHook

DOMAIN = "getsatisfaction.com"
PROTOCOL = "https://"
API_SUBD = "api"

API_ROOT = PROTOCOL + API_SUBD + '/' + DOMAIN
OAUTH_ROOT = PROTOCOL + DOMAIN + '/' + API_SUBD
REQUEST_TOKEN_URL = OAUTH_ROOT + '/request_token'
ACCESS_TOKEN_URL = OAUTH_ROOT + '/access_token'
AUTH_URL = OAUTH_ROOT + '/authorize?oauth_token=%s'

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
    root = Endpoint(API_ROOT, None, None)

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
        self.gs = get_satisfaction
        if self.gs.access_token and self.gs.access_token_secret:
            oauth_hook = OAuthHook(
                    access_token=self.gs.access_token,
                    access_token_secret=self.gs.access_token_secret,
                    consumer_key=self.gs.consumer_key,
                    consumer_secret=self.gs.consumer_secret,
                    header_auth=False
            )
            self.requests = requests.session(hooks={'pre_request': oauth_hook})
        else:
            self.requests = requests

    def fetch(self, endpoint, **kwargs):
        response = self.requests.get(endpoint.url, params=kwargs)
        response.raise_for_status()

        if endpoint.single_result:
            return endpoint.resource_type(json.loads(response.content))
        else:
            model_dicts = json.loads(response.content)['data']
            return map(endpoint.resource_type, model_dicts)

    def get_request_token(self):
        if not self.gs.consumer_key or not self.gs.consumer_secret:
            raise ValueError("Can't get request token without consumer key and secret")
        oauth_hook = OAuthHook(consumer_key=self.gs.consumer_key,
                consumer_secret=self.gs.consumer_secret)
        response = requests.post(REQUEST_TOKEN_URL,
                hooks={'pre_request': oauth_hook})

        qs = parse_qs(response.content)
        oauth_token = qs['oauth_token'][0]
        oauth_secret = qs['oauth_token_secret'][0]

        return oauth_token, oauth_secret

    def get_redirect_url(self, oauth_token):
        return AUTH_URL % oauth_token

    def get_access_token(self, oauth_token, oauth_secret, oauth_verifier):
        oauth_hook = OAuthHook(oauth_token, oauth_secret, self.gs.consumer_key,
                self.gs.consumer_secret)
        response = requests.post('http://api.imgur.com/oauth/access_token',
                {'oauth_verifier': oauth_verifier},
                hooks={'pre_request': oauth_hook})

        response = parse_qs(response.content)
        access_token = response['oauth_token'][0]
        access_token_secret = response['oauth_token_secret'][0]

        self.gs.access_token = access_token
        self.gs.access_token_secret = access_token_secret

        return access_token, access_token_secret


class APIManager(object):
    def __init__(self, get_satisfaction):
        self.get_satisfaction = get_satisfaction

    def __enter__(self):
        return build_api(), GSClient(self.get_satisfaction)

    def __exit__(self, exc_type, exc_value, traceback):
        pass


class GetSatisfaction(object):
    def __init__(self, consumer_key=None, consumer_secret=None,
            access_token=None, access_token_secret=None):
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

    def api_call(self):
        return APIManager(self)

