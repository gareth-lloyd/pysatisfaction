import requests, json
from urlparse import parse_qs
from dateutil import parser as datetime_parser

from oauth_hook import OAuthHook

VERSION = '0.1.3'

DOMAIN = "getsatisfaction.com"
PROTOCOL = "https://"
API_SUBD = "api"

API_ROOT = PROTOCOL + API_SUBD + '.' + DOMAIN
OAUTH_ROOT = PROTOCOL + DOMAIN + '/' + API_SUBD
REQUEST_TOKEN_URL = OAUTH_ROOT + '/request_token'
ACCESS_TOKEN_URL = OAUTH_ROOT + '/access_token'
AUTH_URL = OAUTH_ROOT + '/authorize?oauth_token=%s'

JSON_EXTENSION = '.json'


class Endpoint(object):
    def __init__(self, path, resource_type, parent=None, auth=None):
        self._path = path
        self.resource_type = resource_type
        self.auth = auth
        self.parent = parent
        if parent:
            setattr(parent, path, self)

    @property
    def path(self):
        return self._path

    @property
    def uri(self):
        if self.parent and not self.parent.ok_to_traverse:
            raise ValueError('tried to traverse without enough information')
        return (self.parent.uri + '/' if self.parent else '') + self.path

    @property
    def url(self):
        return self.uri + JSON_EXTENSION

    @property
    def ok_to_traverse(self):
        return True

    def _get_data(self, **kwargs):
        response = requests.get(self.url, params=kwargs)
        response.raise_for_status()
        return json.loads(response.content)

    def __str__(self):
        return self.uri

    def fetch(self, **kwargs):
        return map(self.resource_type, self._get_data(**kwargs)['data'])


class FilterableEndpoint(Endpoint):
    def __init__(self, path, resource_type, parent=None, auth=None):
        super(FilterableEndpoint, self).__init__(path, resource_type, parent)
        self.resource_id = ''

    @property
    def path(self):
        r_id = self.resource_id
        return self._path + '/' + r_id if r_id else self._path

    @property
    def ok_to_traverse(self):
        return bool(self.resource_id)

    def __call__(self, resource_id=''):
        self.resource_id = resource_id
        return self

    def fetch(self, **kwargs):
        if self.ok_to_traverse:
            return self.resource_type(self._get_data(**kwargs))
        else:
            return super(FilterableEndpoint, self).fetch(**kwargs)


no_op_transform = lambda value: value
def datetime_transform(value):
    return datetime_parser.parse(value) if value else None

def resource_transform(resource_type):
    def _do_transform(value):
        return resource_type(value) if value else None
    return _do_transform

def resource_list_transform(resource_type):
    def _do_transform(value_list):
        return map(resource_type, value_list or [])
    return _do_transform

class Resource(object):
    TRANSFORMS = {}
    def __init__(self, object_dict):
        object_dict = object_dict
        for attr_name, value in object_dict.iteritems():
            value = self.TRANSFORMS.get(attr_name, no_op_transform)(value)
            setattr(self, attr_name, value)

        for attr_name in set(self.TRANSFORMS.keys()) - set(object_dict.keys()):
            setattr(self, attr_name, None)

class EmotiTag(Resource):
    pass

class Link(Resource):
    TRANSFORMS = {
        'created_at': datetime_transform,
    }

class Company(Resource):
    pass

class Person(Resource):
    TRANSFORMS = {
        'member_since': datetime_transform,
    }

class Product(Resource):
    TRANSFORMS = {
        'links': resource_list_transform(Link),
        'created_at': datetime_transform,
    }

class Topic(Resource):
    TRANSFORMS = {
        'created_at': datetime_transform,
        'last_active_at': datetime_transform,
        'author': resource_transform(Person),
        'products': resource_list_transform(Product),
        'emotitag': resource_transform(EmotiTag),
    }

class Reply(Resource):
    TRANSFORMS = {
        'created_at': datetime_transform,
        'author': resource_transform(Person),
    }

class Comment(Resource):
    TRANSFORMS = {
        'created_at': datetime_transform,
        'author': resource_transform(Person),
    }

class Tag(Resource):
    pass

def build_api(get_satisfaction):
    auth = get_satisfaction.get_auth()
    root = Endpoint(API_ROOT, None, parent=None, auth=auth)

    FilterableEndpoint('companies', Company, parent=root, auth=auth)
    FilterableEndpoint('products', Product, parent=root, auth=auth)
    FilterableEndpoint('topics', Topic, parent=root, auth=auth)
    FilterableEndpoint('people', Person, parent=root, auth=auth)
    FilterableEndpoint('replies', Reply, parent=root, auth=auth)
    FilterableEndpoint('tags', Tag, parent=root, auth=auth)

    Endpoint('employees', Person, parent=root.companies, auth=auth)
    FilterableEndpoint('products', Product, parent=root.companies, auth=auth)
    Endpoint('topics', Topic, parent=root.companies.products, auth=auth)
    Endpoint('tags', Tag, parent=root.companies, auth=auth)
    Endpoint('topics', Topic, parent=root.companies.tags, auth=auth)
    FilterableEndpoint('topics', Topic, parent=root.companies, auth=auth)
    Endpoint('people', Person, parent=root.companies, auth=auth)

    Endpoint('products', Product, parent=root.people, auth=auth)
    Endpoint('followed/topics', Topic, parent=root.people, auth=auth)
    Endpoint('replies', Reply, parent=root.people, auth=auth)
    Endpoint('topics', Topic, parent=root.people, auth=auth)
    Endpoint('companies', Company, parent=root.people, auth=auth)

    Endpoint('companies', Company, parent=root.products, auth=auth)
    Endpoint('topics', Topic, parent=root.products, auth=auth)

    Endpoint('comments', Comment, parent=root.replies, auth=auth)

    Endpoint('people', Person, parent=root.topics, auth=auth)
    Endpoint('products', Product, parent=root.topics, auth=auth)
    Endpoint('comments', Comment, parent=root.topics, auth=auth)
    Endpoint('replies', Reply, parent=root.topics, auth=auth)

    return root


class GetSatisfactionAPI(object):
    def __init__(self, consumer_key=None, consumer_secret=None,
            access_token=None, access_token_secret=None):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret

    def get_auth(self):
        if not (self.access_token and self.access_token_secret):
            return None
        else:
            OAuthHook(access_token=self.access_token,
                    access_token_secret=self.access_token_secret,
                    consumer_key=self.consumer_key,
                    consumer_secret=self.consumer_secret,
                    header_auth=False)

    def api_call(self):
        return self

    def __enter__(self):
        return build_api(self)

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def get_request_token(self):
        if not (self.consumer_key and self.consumer_secret):
            raise ValueError("Can't get request token without consumer key and secret")

        oauth_hook = OAuthHook(consumer_key=self.consumer_key,
                consumer_secret=self.consumer_secret)
        response = requests.post(REQUEST_TOKEN_URL,
                hooks={'pre_request': oauth_hook})

        qs = parse_qs(response.content)
        oauth_token = qs['oauth_token'][0]
        oauth_secret = qs['oauth_token_secret'][0]

        return oauth_token, oauth_secret

    def get_redirect_url(self, oauth_token):
        return AUTH_URL % oauth_token

    def get_access_token(self, oauth_token, oauth_secret, oauth_verifier):
        oauth_hook = OAuthHook(oauth_token, oauth_secret, self.consumer_key,
                self.consumer_secret)
        response = requests.post('http://api.imgur.com/oauth/access_token',
                {'oauth_verifier': oauth_verifier},
                hooks={'pre_request': oauth_hook})

        response = parse_qs(response.content)
        access_token = response['oauth_token'][0]
        access_token_secret = response['oauth_token_secret'][0]
        self.access_token = access_token
        self.access_token_secret = access_token_secret

        return access_token, access_token_secret

