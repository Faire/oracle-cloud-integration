import io
import os
import json
import logging
import gzip

import requests

logger = logging.getLogger(__name__)

DD_SOURCE = "Oracle Cloud"  # Adding a source name.
DD_SERVICE = "OCI Logs"  # Adding a service name.
DD_TIMEOUT = 10 * 60  # Adding a timeout for the Datadog API call.


def process(body: dict) -> None:

    logger.info(f"Received raw payload: {json.dumps(body, separators=(',', ':'))}")

    # If log is from function invocation, use message from the body as data
    data = body.get("data", {})
    time = body.get("time")
    if "functionId" in data:
        # message format: 01J9S6308T1BT0938ZJ000KAKN - root - ERROR - json_str
        try:
            json_str = data.get("message").split(" - ")[3]
            data = json.loads(json_str)
            time = data.get("time")
        except Exception as e:
            print("function invoked message does not contain json string, skipping the log")
            return

    source = body.get("source")
    oracle = body.get("oracle", {})

    # Get json data, time, and source information
    payload = {}
    payload.update({"source": source})
    payload.update({"time": time})
    payload.update({"data": data})
    payload.update({"oracle": oracle})
    payload.update({"ddsource": DD_SOURCE})
    payload.update({"service": DD_SERVICE})

    # Datadog endpoint URL and token to call the REST interface.
    # These are defined in the func.yaml file.
    try:
        dd_host = os.environ['DATADOG_HOST']
        dd_token = os.environ['DATADOG_TOKEN']
        dd_tags = os.environ.get('DATADOG_TAGS', '')
    except KeyError:
        err_msg = "Could not find environment variables, \
                   please ensure DATADOG_HOST and DATADOG_TOKEN \
                   are set as environment variables."
        logger.error(err_msg)

    if dd_tags:
        payload.update({'ddtags': dd_tags})

    headers = {"Content-type": "application/json",
               "DD-API-KEY": dd_token}
    logs_message = json.dumps(payload)

    logger.info(f"Sending DD message: {json.dumps(payload, separators=(',', ':'))}")

    if _should_compress_payload():
        serialized = gzip.compress(logs_message.encode())
        headers["content-encoding"] = "gzip"
    else:
        serialized = logs_message

    # Invoke Datadog API with the payload.
    # If the payload contains more than one log
    # this will be ingested at once.
    try:
        res = requests.post(dd_host, data=serialized, headers=headers,
                            timeout=DD_TIMEOUT)
        logger.info(res.text)
    except Exception as ex:
        logger.exception(ex)

def _should_compress_payload() -> bool:
    return os.environ.get("DD_COMPRESS", "false").lower() == "true"

def handler(ctx, data: io.BytesIO = None) -> None:
    """
    This function receives the logging json and invokes the Datadog endpoint
    for ingesting logs. https://docs.cloud.oracle.com/en-us/iaas/Content/Logging/Reference/top_level_logging_format.htm#top_level_logging_format
    If this Function is invoked with more than one log the function go over
    each log and invokes the Datadog endpoint for ingesting one by one.
    """
    try:
        body = json.loads(data.getvalue())
        if isinstance(body, list):
            # Batch of CloudEvents format
            for b in body:
                process(b)
        else:
            # Single CloudEvent
            process(body)
    except Exception as ex:
        logger.exception(ex)
