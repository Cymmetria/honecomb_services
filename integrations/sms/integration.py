# -*- coding: utf-8 -*-
"""SMS integration."""
from __future__ import unicode_literals

import twilio
import twilio.rest

from integrationmanager.exceptions import IntegrationSendEventError
from integrationmanager.error_messages import TEST_CONNECTION_REQUIRED
from integrationmanager.integration_utils import BaseIntegration

MAX_SMS_LEN = 140


class SMSIntegration(BaseIntegration):
    """An integration to send SMS messages to a defined phone number on Honeycomb alerts."""

    def test_connection(self, data):
        """Verify that we are able to connect to the defined twilio account."""
        errors = {}
        fields = ["from_phone", "to_phone", "twilio_account_sid", "twilio_auth_token"]
        for field in fields:
            if not data.get(field):
                errors[field] = [TEST_CONNECTION_REQUIRED]
        if len(errors) > 0:
            return False, errors

        from_phone = data.get("from_phone")
        to_phone = data.get("to_phone")
        twilio_account_sid = data.get("twilio_account_sid")
        twilio_auth_token = data.get("twilio_auth_token")
        extra = data.get("extra")

        try:
            client = twilio.rest.Client(twilio_account_sid, twilio_auth_token)
            body = "Test Alert! Hello World!"
            if extra:
                body = "{} {}".format(body, extra)
            client.messages.create(to=to_phone, from_=from_phone, body=body)
            return True, {}
        except Exception as exc:
            response = {"non_field_errors": [str(exc)]}
            return False, response

    def send_event(self, alert_fields):
        """Trigger sending an SMS via Twilio for the given event."""
        from_phone = self.integration_data.get("from_phone")
        to_phone = self.integration_data.get("to_phone")
        twilio_account_sid = self.integration_data.get("twilio_account_sid")
        twilio_auth_token = self.integration_data.get("twilio_auth_token")
        extra = self.integration_data.get("extra")

        try:
            body = "{} alert".format(alert_fields.get("event_type"))
            if extra:
                body = '{} {}'.format(body, extra)
            if alert_fields.get("originating_ip"):
                body = "{} from {}".format(body, alert_fields.get("originating_ip"))
            if alert_fields.get("cmd"):
                body = "{} cmd: {}".format(body, alert_fields.get("cmd"))
            if len(body) > MAX_SMS_LEN:
                body = body[:MAX_SMS_LEN]

            body = body.encode('ascii', 'replace')

            client = twilio.rest.Client(twilio_account_sid, twilio_auth_token)
            client.messages.create(to=to_phone, from_=from_phone, body=body)
            return {}, None
        except Exception as exc:
            raise IntegrationSendEventError(exc)

    def format_output_data(self, output_data):
        """No special formatting needed."""
        return output_data


IntegrationActionsClass = SMSIntegration
