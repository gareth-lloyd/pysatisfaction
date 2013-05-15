from unittest import TestCase

from mock import Mock, patch

from pysatisfaction.client import (Endpoint, FilterableEndpoint, Person, Topic,
        GetSatisfaction, GSClient)

class EndpointTests(TestCase):
    def test_endpoint_set_as_attr_on_parent(self):
        parent = Endpoint('a', Topic)
        endpoint = Endpoint('b', Topic, parent=parent)

        self.assertEquals(endpoint, parent.b)

    def test_url(self):
        endpoint = Endpoint('path', Topic)
        self.assertEquals('path.json', endpoint.url)

    def test_url_with_parent(self):
        parent = Endpoint('a', Topic)
        endpoint = Endpoint('b', Topic, parent=parent)
        self.assertEquals('a/b.json', endpoint.url)

    def test_endpoint_always_single_result(self):
        self.assertTrue(Endpoint('a', Topic).single_result)

    def test_endpoint_path(self):
        self.assertEquals('a', Endpoint('a', Topic).path)


class FilterableEndpointTests(TestCase):
    def test_use_non_filtered_endpoint_as_parent(self):
        parent = FilterableEndpoint('a', Topic)
        endpoint = Endpoint('b', Topic, parent=parent)

        with self.assertRaises(ValueError):
            endpoint.url

    def test_use_non_filtered_endpoint_as_parent_with_filtering(self):
        parent = FilterableEndpoint('a', Topic)
        endpoint = Endpoint('b', Topic, parent=parent)

        parent('fun')

        self.assertEquals('a/fun/b.json', endpoint.url)

    def test_filterable_endpoint_is_single_result_when_filtered(self):
        endpoint = FilterableEndpoint('a', Topic)
        self.assertFalse(endpoint.single_result)

        endpoint('fun')

        self.assertTrue(endpoint.single_result)

    def test_filterable_endpoint_path_without_filtering(self):
        endpoint = FilterableEndpoint('a', Topic)
        self.assertEquals('a', endpoint.path)

    def test_filterable_endpoint_path_with_filtering(self):
        endpoint = FilterableEndpoint('a', Topic)
        endpoint('fun')
        self.assertEquals('a/fun', endpoint.path)

class GetSatisfactionTests(TestCase):
    def test_api_call_builds_api_and_client(self):
        gs = GetSatisfaction()
        with gs.api_call() as (api, client):
            self.assertTrue(hasattr(api, 'companies'))
            self.assertTrue(hasattr(client, 'fetch'))
            self.assertEquals(gs, client.get_satisfaction)

@patch('pysatisfaction.client.requests.get', autospec=True)
class GSClientTests(TestCase):
    def setUp(self):
        self.gs_client = GSClient(GetSatisfaction())

    def test_fetch_single_result(self, mock_get):
        mock_response = Mock()
        mock_response.content = '{}'
        mock_get.return_value = mock_response

        endpoint = Endpoint('a', Topic)

        self.gs_client.fetch(endpoint)

        mock_get.assert_called_once_with('a.json', params={})

    def test_fetch_multiple_results(self, mock_get):
        mock_response = Mock()
        mock_response.content = '{"data": []}'
        mock_get.return_value = mock_response

        endpoint = FilterableEndpoint('a', Topic)

        self.assertEquals([], self.gs_client.fetch(endpoint))

        mock_get.assert_called_once_with('a.json', params={})


