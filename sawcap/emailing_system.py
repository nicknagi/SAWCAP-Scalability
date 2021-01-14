import os
import argparse
# Import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

def send_email(recepients, text_path, textfiles, png_path, pngfiles):
    # Create the container (outer) email message.
    sender = 'polinka.lmb@gmail.com'

    msg = MIMEMultipart()
    msg['Subject'] = 'Digital Ocean: recent workload run stats'
    msg['From'] = sender
    msg['To'] = ','.join(recepients)
    msg.preamble = ""
    
    if textfiles != None:
        os.chdir(text_path) 
        for file in textfiles:
            # Open the files in binary mode.  Let the MIMEImage class automatically
            # guess the specific image type.
            with open(file, 'rb') as fp:
                text = MIMEText(fp.read())
            msg.attach(text)
    if pngfiles != None:
        for file in pngfiles:
            # Open the files in binary mode.  Let the MIMEImage class automatically
            # guess the specific image type.
            with open(file, 'rb') as fp:
                img = MIMEImage(fp.read())
            msg.attach(img)
    s = smtplib.SMTP('localhost')
    s.sendmail(sender, recepients, msg.as_string())
    s.quit()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Emailing recepients')
    parser.add_argument('--recepients', help='Overwrites the recepients list')
    parser.add_argument('--text_dir_name', help='Directory name with all text files')
    parser.add_argument('--text_files', help='Text files paths to be sent. Commas, no space')
    parser.add_argument('--images_dir_name', help='Directory name with all image files')
    parser.add_argument('--images', help='Images paths to be sent. Commas, no space')
    args = parser.parse_args()

    if args.recepients != None:
        recepients = args.recepients.split(',')
    else:
        recepients = ['p.govorkova@mail.utoronto.ca']

    text_files = None
    images = None
    if args.text_files != None:
        text_files = args.text_files.split(',')
        assert(args.text_dir_name != None)
    if args.images != None:
        images = args.images.split(',')
        assert(args.images_dir_name != None)
    
    send_email(recepients, args.text_dir_name, text_files, args.images_dir_name, images)