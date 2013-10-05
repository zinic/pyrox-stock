import pyrox.log as logging
import pyrox.filtering as filtering

_LOG = logging.get_logger(__name__)


class BodyInterceptionTest(filtering.HttpFilter):

    @filtering.handles_request_body
    @filtering.handles_response_body
    def on_request_body(self, body_part, output):
        _LOG.debug('Message part size is: {}'.format(len(body_part)))
        output.write(body_part)

