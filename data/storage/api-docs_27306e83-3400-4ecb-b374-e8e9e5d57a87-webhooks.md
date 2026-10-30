# Webhooks

## Retries
Failed webhook deliveries are retried up to 5 times with exponential backoff, starting at 30 seconds.
To trigger a manual redelivery, call POST /v1/webhooks/{id}/redeliver.

## Signatures
Each webhook request includes an X-Signature header containing an HMAC-SHA256 signature of the raw payload.
Verify the signature using your webhook secret before processing the event.

