"""Short function to send an email on AWS."""

import boto3
from botocore.exceptions import ClientError


def send_email(email_address, subject, message):
    """Send email."""

    # This address must be verified with Amazon SES.
    sender = "<{}>".format(email_address)
    recipient = email_address

    # Might need to change this based on region
    aws_region = "us-west-2"

    body_text = (message)
    charset = "UTF-8"

    client = boto3.client('ses', region_name=aws_region)

    try:
        client.send_email(
            Destination={
                'ToAddresses': [
                    recipient,
                ],
            },
            Message={
                'Body': {
                    'Text': {
                        'Charset': charset,
                        'Data': body_text,
                    },
                },
                'Subject': {
                    'Charset': charset,
                    'Data': subject,
                },
            },
            Source=sender
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
