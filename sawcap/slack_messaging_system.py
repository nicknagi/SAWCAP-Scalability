import os
import argparse
# Import smtplib for the actual sending function

def send_slack_message(text, files):
    import os
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError

    client = WebClient(token=os.environ['SLACK_TOKEN'])
    if text != None:
        try:
            client.chat_postMessage(channel='#data-collection-notifications', text=text)
        except SlackApiError as e:
            # You will get a SlackApiError if "ok" is False
            assert e.response["ok"] is False
            assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
            print(f"Got an error: {e.response['error']}")
    if files != None:
        for one_file in files:
            print(one_file)
            try:
                client.files_upload(channels='#data-collection-notifications', file=os.path.expanduser(one_file))
            except SlackApiError as e:
                # You will get a SlackApiError if "ok" is False
                assert e.response["ok"] is False
                assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
                print(f"Got an error: {e.response['error']}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Slacking channel')
    parser.add_argument('--text', help='Text')
    parser.add_argument('--files', help='List of file path of files to be sent. Commas, no space')
    args = parser.parse_args()

    if args.files != None:
        files = args.files.split(',')
    print(files)
    
    send_slack_message(args.text, files)