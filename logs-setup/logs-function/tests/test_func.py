import os

from io import BytesIO
from func import handler
from unittest import TestCase, mock


def to_BytesIO(str):
    """ Helper function to turn string test data into expected BytesIO asci encoded bytes """
    return BytesIO(bytes(str, 'ascii'))


class TestLogForwarderFunction(TestCase):
    """ Test simple and batch format json CloudEvent payloads """

    def setUp(self):
        # Set env variables expected by function
        os.environ['DATADOG_HOST'] = "http://datadog.woof"
        os.environ['DATADOG_TOKEN'] = "VERY-SECRET-TOKEN-2000"
        return super().setUp()

    @mock.patch("requests.post")
    def testSimpleData(self, mock_post, ):
        """ Test single CloudEvent payload """

        payload = """
        {
            "specversion" : "1.0",
            "type" : "com.example.someevent",
            "source" : "/mycontext",
            "id" : "C234-1234-1234",
            "time" : "2018-04-05T17:31:00Z",
            "comexampleextension1" : "value",
            "comexampleothervalue" : 5,
            "datacontenttype" : "application/json",
            "data" : {
                "appinfoA" : "abc",
                "appinfoB" : 123,
                "appinfoC" : true
            }
        }
        """
        handler(ctx=None, data=to_BytesIO(payload))
        mock_post.assert_called_once()
        self.assertEqual(mock_post.mock_calls[0].kwargs['data'],
                         '{"source": "/mycontext", "time": "2018-04-05T17:31:00Z", "data": '
                         '{"appinfoA": "abc", "appinfoB": 123, "appinfoC": true}, "ddsource": '
                         '"oracle_cloud", "service": "OCI Logs"}'
                         )

    @mock.patch("requests.post")
    def testSimpleDataTags(self, mock_post, ):
        """ Test single CloudEvent payload with Tags enabled """

        payload = """
        {
            "specversion" : "1.0",
            "type" : "com.example.someevent",
            "source" : "/mycontext",
            "id" : "C234-1234-1234",
            "time" : "2018-04-05T17:31:00Z",
            "comexampleextension1" : "value",
            "comexampleothervalue" : 5,
            "datacontenttype" : "application/json",
            "data" : {
                "appinfoA" : "abc",
                "appinfoB" : 123,
                "appinfoC" : true
            }
        }
        """
        os.environ['DATADOG_TAGS'] = "prod:true"
        handler(ctx=None, data=to_BytesIO(payload))
        mock_post.assert_called_once()
        self.assertEqual(mock_post.mock_calls[0].kwargs['data'],
                         '{"source": "/mycontext", "time": "2018-04-05T17:31:00Z", "data": '
                         '{"appinfoA": "abc", "appinfoB": 123, "appinfoC": true}, "ddsource": '
                         '"oracle_cloud", "service": "OCI Logs", "ddtags": "prod:true"}'
                         )

    @mock.patch("requests.post")
    def testBatchFormat(self, mock_post):
        """ Test batch format case, where we get an array of 'CloudEvents' """
        batch = """
        [
            {
                "specversion" : "1.0",
                "type" : "com.example.someevent",
                "source" : "/mycontext/4",
                "id" : "B234-1234-1234",
                "time" : "2018-04-05T17:31:00Z",
                "comexampleextension1" : "value",
                "comexampleothervalue" : 5,
                "datacontenttype" : "application/vnd.apache.thrift.binary",
                "data_base64" : "... base64 encoded string ..."
            },
            {
                "specversion" : "1.0",
                "type" : "com.example.someotherevent",
                "source" : "/mycontext/9",
                "id" : "C234-1234-1234",
                "time" : "2018-04-05T17:31:05Z",
                "comexampleextension1" : "value",
                "comexampleothervalue" : 5,
                "datacontenttype" : "application/json",
                "data" : {
                    "appinfoA" : "potatoes",
                    "appinfoB" : 123,
                    "appinfoC" : true
                }
            }
        ]
        """
        handler(ctx=None, data=to_BytesIO(batch))
        self.assertEqual(mock_post.call_count, 2, "Data was not successfully submitted for entire batch")
        self.assertEqual([arg.kwargs['data'] for arg in mock_post.call_args_list],
                         ['{"source": "/mycontext/4", "time": "2018-04-05T17:31:00Z", "data": {}, '
                          '"ddsource": "oracle_cloud", "service": "OCI Logs"}',
                          '{"source": "/mycontext/9", "time": "2018-04-05T17:31:05Z", "data": '
                          '{"appinfoA": "potatoes", "appinfoB": 123, "appinfoC": true}, "ddsource": '
                          '"oracle_cloud", "service": "OCI Logs"}'])

    @mock.patch("requests.post")
    def testForwardFunctionInvokeLogs(self, mock_post):
        payload = """
            {
                "oracle": {
                    "compartmentid": "ocid1.tenancy.oc1..aaaaaaaadoqhu6c734qwoafixbkpk6x3emsz4do76gjhu7ezhc7jqquvlmsq",
                    "ingestedtime": "2024-10-09T17:45:12.328Z",
                    "loggroupid": "ocid1.loggroup.oc1.ca-toronto-1.amaaaaaaqh5iwviav3rpyzlc5efsjkjgeer7bzd5ba665qxihrhf23p52e2q",
                    "tenantid": "ocid1.tenancy.oc1..aaaaaaaadoqhu6c734qwoafixbkpk6x3emsz4do76gjhu7ezhc7jqquvlmsq",
                    "logid": "ocid1.log.oc1.ca-toronto-1.amaaaaaaqh5iwviaoxnmwsfb6u72ohqpqmmfmomlzn2bxrzyzgab5aknv7ra"
                },
                "data": {
                    "functionId": "ocid1.fnfunc.oc1.ca-toronto-1.aaaaaaaas756ii24melahgcps6wjwjqzfi5otkrdywdyai3laboacosi2oaa",
                    "opcRequestId": "/01J9S630870000000000018Y0V/01J9S630870000000000018Y0W",
                    "src": "STDERR",
                    "requestId": "/01J9S630870000000000018Y0V/01J9S630870000000000018Y0W",
                    "applicationId": "ocid1.fnapp.oc1.ca-toronto-1.aaaaaaaaxru5cehs5b6inghow3idjisuk6qxqryqaxjjnm6dp4m7cdkxgdvq",
                    "containerId": "01J9S63BFW00000000000000Y1",
                    "message": "01J9S6308T1BT0938ZJ000KAKN - root - ERROR - {\\"error\\": \\"abc\\", \\"time\\": \\"2024-10-09T17:45:01.298Z\\"}"
                },
                "service": "OCI Logs",
                "logger": {
                    "name": "work-request-exporter"
                },
                "source": "work-request-exporter",
                "time": "2024-10-09T17:45:01.298Z"
            }
        """
        handler(ctx=None, data=to_BytesIO(payload))
        mock_post.assert_called_once()
        self.assertEqual('{"source": "work-request-exporter", "time": "2024-10-09T17:45:01.298Z", '
                          '"data": {"error": "abc", "time": "2024-10-09T17:45:01.298Z"}, "oracle": '
                          '{"compartmentid": '
                          '"ocid1.tenancy.oc1..aaaaaaaadoqhu6c734qwoafixbkpk6x3emsz4do76gjhu7ezhc7jqquvlmsq", '
                          '"ingestedtime": "2024-10-09T17:45:12.328Z", "loggroupid": '
                          '"ocid1.loggroup.oc1.ca-toronto-1.amaaaaaaqh5iwviav3rpyzlc5efsjkjgeer7bzd5ba665qxihrhf23p52e2q", '
                          '"tenantid": '
                          '"ocid1.tenancy.oc1..aaaaaaaadoqhu6c734qwoafixbkpk6x3emsz4do76gjhu7ezhc7jqquvlmsq", '
                          '"logid": '
                          '"ocid1.log.oc1.ca-toronto-1.amaaaaaaqh5iwviaoxnmwsfb6u72ohqpqmmfmomlzn2bxrzyzgab5aknv7ra"}, '
                          '"ddsource": "Oracle Cloud", "service": "OCI Logs"}',
                        mock_post.mock_calls[0].kwargs['data'])
