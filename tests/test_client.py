from unittest import TestCase
from mock import patch

from pysatisfaction.client import (Endpoint, ResourceEndpoint, Person, Topic,
        CollectionEndpoint)

class EndpointTests(TestCase):
    def test_endpoint_set_as_attr_on_parent(self):
        parent = Endpoint('a', Topic)
        endpoint = Endpoint('b', Topic, parent=parent)

        self.assertEquals(endpoint, parent.b)

    def test_endpoint_customised_for_person(self):
        endpoint = Endpoint('path', Person)
        self.assertTrue(hasattr(endpoint, 'replies'))
        self.assertTrue(hasattr(endpoint, 'topics'))
        self.assertTrue(hasattr(endpoint, 'companies'))

    def test_endpoint_customised_for_topic(self):
        endpoint = Endpoint('path', Topic)
        self.assertTrue(hasattr(endpoint, 'tags'))

    def test_url(self):
        endpoint = Endpoint('path', Topic)
        self.assertEquals('path.json', endpoint.url())

    def test_url_with_parent(self):
        parent = Endpoint('a', Topic)
        endpoint = Endpoint('b', Topic, parent=parent)
        self.assertEquals('a/b.json', endpoint.url())


class ResourceEndpointTests(TestCase):
    @patch('pysatisfaction.client.Endpoint._retrieve', autospec=True)
    def test_get(self, mock_retrieve):
        mock_retrieve.return_value = {}
        endpoint = ResourceEndpoint('path', Topic)
        self.assertTrue(isinstance(endpoint.get(), Topic))


class CollectionEndpointTests(TestCase):
    @patch('pysatisfaction.client.Endpoint._retrieve', autospec=True)
    def test_all(self, mock_retrieve):
        mock_retrieve.return_value = []
        endpoint = CollectionEndpoint('path', Topic)
        self.assertEquals([], endpoint.all())


