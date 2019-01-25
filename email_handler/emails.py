from __future__ import print_function

import json
import os.path
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Adapted from Google.
def setup_gmail_boilerplate():
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

    # Call the Gmail API
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    if not labels:
        print('No labels found.')
    else:
        print('Labels:')
        for label in labels:
            print(label['name'])

    return service

# Adapted from Google.
def get_all_gmail_msg_ids(service, user_id, query):
    try:
        response = service.users().messages().list(userId=user_id,
                                                   q=query).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])

        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId=user_id, q=query,
                                                       pageToken=page_token).execute()
            messages.extend(response['messages'])

        return messages
    except Exception as e:
        print('An error occurred: %s' % e)

# Adapted from Google.
def get_msg(service, user_id, msg_id):
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id).execute()

        print('Message snippet: %s' % message['snippet'])
        return message
    except Exception as e:
        print('An error occurred: %s' % e)

def get_msgs(service, user_id, msg_ids):
    for i in range(len(msg_ids)):
        msg_id = msg_ids[i]
        msg = get_msg(service, user_id, msg_id)
        print(msg)
    return

if __name__ == '__main__':
    service = setup_gmail_boilerplate()
    msg_ids = get_all_gmail_msg_ids(service, 'me', '')
    # Problems with API due to log in
    # https://developers.google.com/gmail/api/auth/web-server
    # https://stackoverflow.com/questions/51881430/cant-authenticate-google-service-account-to-gmail
    get_msgs(service, 'me', msg_ids)
