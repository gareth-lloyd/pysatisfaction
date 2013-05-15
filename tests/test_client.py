from datetime import datetime
from unittest import TestCase

import pytz
from mock import Mock, patch

from pysatisfaction import (Endpoint, FilterableEndpoint, Topic,
        GetSatisfactionAPI, Resource, datetime_transform,
        resource_transform, no_op_transform, resource_list_transform)



class ResourceTests(TestCase):
    def test_datetime_transform(self):
        self.assertEquals(datetime(2013, 05, 15, 15, 56, 42, tzinfo=pytz.UTC),
                datetime_transform('2013/05/15 15:56:42 +0000'))

    def test_resource_transform(self):
        self.assertTrue(isinstance(resource_transform(Topic)({}), Topic))

    def test_resource_list_transform_empty_list(self):
        trans = resource_list_transform(Topic)
        self.assertEquals([], trans([]))

    def test_resource_list_transform(self):
        trans = resource_list_transform(Topic)
        results = trans([{}, {}])
        self.assertEquals(2, len(results))
        for value in results:
            self.assertTrue(isinstance(value, Topic))

    def test_no_op_transform(self):
        self.assertEquals('a', no_op_transform('a'))

    def test_no_op_if_not_in_transforms(self):
        r = Resource({'attr_name': 'value'})
        self.assertEquals(r.attr_name, 'value')

    def test_transforms_executed(self):
        class MyResource(Resource):
            TRANSFORMS = {'attr_name': resource_transform(Topic)}

        mr = MyResource({'attr_name': {}})
        self.assertTrue(isinstance(mr.attr_name, Topic))

    def test_absent_keys_get_set_to_none(self):
        class MyResource(Resource):
            TRANSFORMS = {'attr_name': resource_transform(Topic)}

        mr = MyResource({})
        self.assertEquals(None, mr.attr_name)


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

    @patch('pysatisfaction.client.requests.get')
    def test_fetch_single_result(self, mock_get):
        mock_response = Mock()
        mock_response.content = '{}'
        mock_get.return_value = mock_response

        Endpoint('a', Topic).fetch()

        mock_get.assert_called_once_with('a.json', params={})

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

    @patch('pysatisfaction.client.requests.get')
    def test_fetch_single_result(self, mock_get):
        mock_response = Mock()
        mock_response.content = '{}'
        mock_get.return_value = mock_response

        FilterableEndpoint('a', Topic)('fun').fetch()

        mock_get.assert_called_once_with('a/fun.json', params={})

    @patch('pysatisfaction.client.requests.get')
    def test_fetch_multiple_results(self, mock_get):
        mock_response = Mock()
        mock_response.content = '{"data": []}'
        mock_get.return_value = mock_response

        endpoint = FilterableEndpoint('a', Topic)

        self.assertEquals([], endpoint.fetch())

        mock_get.assert_called_once_with('a.json', params={})


class GetSatisfactionTests(TestCase):
    def setUp(self):
        self.gs = GetSatisfactionAPI(
                access_token='a',
                access_token_secret='b',
                consumer_key='c',
                consumer_secret='d')

    def test_api_call_builds_api(self):
        with self.gs.api_call() as api:
            self.assertTrue(hasattr(api, 'companies'))
            self.assertEquals(self.gs.get_auth(), api.auth)

    def test_get_request_token_without_cons_key(self):
        self.gs.consumer_key = None
        with self.assertRaises(ValueError):
            self.gs.get_request_token()

    def test_get_request_token_without_cons_secret(self):
        self.gs.consumer_secret = None
        with self.assertRaises(ValueError):
            self.gs.get_request_token()

