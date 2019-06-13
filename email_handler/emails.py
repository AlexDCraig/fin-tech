# Requirements: credentials.json file unique to your specific situation.
# For now, must assume the email structures follows that of First Tech Federal Credit Union's daily messaging service.

from __future__ import print_function

import argparse
import base64
import email
import os.path
import pickle
import re
from collections import OrderedDict
import string

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pymongo import MongoClient

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Adapted from Google.
def get_gmail_messages():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    # Get the unique ids of each email in the account.
    response = service.users().messages().list(userId='me',
                                               q='').execute()
    messages = []
    if 'messages' in response:
        messages.extend(response['messages'])

    while 'nextPageToken' in response:
        page_token = response['nextPageToken']
        response = service.users().messages().list(userId='me', q='',
                                                   pageToken=page_token).execute()
        messages.extend(response['messages'])

    # Identify each email by its id. Collect its snippet and body.
    emails = dict()
    for i in range(len(messages)):
        message_info = messages[i]
        message_id = message_info['id']
        message = service.users().messages().get(userId='me', id=message_id, format='raw').execute()
        snippet = message['snippet']
        msg_str = base64.urlsafe_b64decode(message['raw']).decode('utf-8')
        mime_msg = email.message_from_string(msg_str)
        emails[snippet] = mime_msg

    return emails

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('account_to_analyze')
    args = parser.parse_args()

    account_to_analyze = args.account_to_analyze
    emails = get_gmail_messages()

    balance_by_date = OrderedDict()
    for email_header, email_body in emails.items():
        email_header = str(email_header).replace('&#39;', "'")

        if 'Your Balance Summary' in email_header and account_to_analyze in email_header:
            try:
                date = re.findall('(?:[0-9]{1,2}/){1,2}[0-9]{4}', email_header)[0]
                balance = re.findall('\$\d+(?:\.\d+)?', email_header)[0]
                balance_by_date[date] = balance
            except:
                continue

    # Connect to mongodb container.
    client = MongoClient('midas-mongo-deployment:27017')