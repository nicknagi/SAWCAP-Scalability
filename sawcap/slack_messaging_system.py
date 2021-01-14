import os
import argparse
# Import smtplib for the actual sending function

def send_slack_message(text, textpath, textfiles, pngpath, pngfiles):
    import os
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError

    client = WebClient(token=os.environ['SLACK_TOKEN'])
    if text != None:
        try:
            response = client.chat_postMessage(channel='#data-collection-notifications', text=text)
        except SlackApiError as e:
            # You will get a SlackApiError if "ok" is False
            assert e.response["ok"] is False
            assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
            print(f"Got an error: {e.response['error']}")
    if textfiles != None:
        for textfile in textfiles:
            try:
                client.files_upload(channels='#data-collection-notifications', file=(textpath+textfile))
            except SlackApiError as e:
                # You will get a SlackApiError if "ok" is False
                assert e.response["ok"] is False
                assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
                print(f"Got an error: {e.response['error']}")
    if pngfiles != None:
        for pngfile in pngfiles:
            try:
                client.files_upload(channels='#data-collection-notifications', file=(pngpath+pngfile))
            except SlackApiError as e:
                # You will get a SlackApiError if "ok" is False
                assert e.response["ok"] is False
                assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
                print(f"Got an error: {e.response['error']}")

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Emailing recepients')
    parser.add_argument('--text', help='Text')
    parser.add_argument('--text_dir_name', help='Directory name with all text files')
    parser.add_argument('--text_files', help='Text files paths to be sent. Commas, no space')
    parser.add_argument('--images_dir_name', help='Directory name with all image files')
    parser.add_argument('--images', help='Images paths to be sent. Commas, no space')
    args = parser.parse_args()

    text_files = None
    images = None
    if args.text_files != None:
        text_files = args.text_files.split(',')
        assert(args.text_dir_name != None)
    if args.images != None:
        images = args.images.split(',')
        assert(args.images_dir_name != None)
    
    send_slack_message(args.text, args.text_dir_name, text_files, args.images_dir_name, images)