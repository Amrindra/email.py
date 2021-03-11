#changeImage.py

#!/usr/bin/env python3

import os
from PIL import Image

path = os.path.expanduser('~') + '/supplier-data/images/'
		
for image in os.listdir(path):
	if '.tiff' in image and '.' not in image[0]:
		img = Image.open(path + image)
		img.resize((600, 400)).convert("RGB").save(path + image.split('.')[0] + '.jpeg' , 'jpeg')
		img.close()

#emails.py
#!/usr/bin/env python3

import email.message
import mimetypes
import os.path
import smtplib

def generate_email(sender, recipient, subject, body, attachment_path):
  """Creates an email with an attachement."""
  # Basic Email formatting
  message = email.message.EmailMessage()
  message["From"] = sender
  message["To"] = recipient
  message["Subject"] = subject
  message.set_content(body)

  # Process the attachment and add it to the email
  attachment_filename = os.path.basename(attachment_path)
  mime_type, _ = mimetypes.guess_type(attachment_path)
  mime_type, mime_subtype = mime_type.split('/', 1)

  with open(attachment_path, 'rb') as ap:
    message.add_attachment(ap.read(),
                           maintype=mime_type,
                           subtype=mime_subtype,
                           filename=attachment_filename)

  return message

def send_email(message):
  """Sends the message to the configured SMTP server."""
  mail_server = smtplib.SMTP('localhost')
  mail_server.send_message(message)
  mail_server.quit()

def generate_error_report(sender, recipient, subject, body):

  message = email.message.EmailMessage()
  message["From"] = sender
  message["To"] = recipient
  message["Subject"] = subject
  message.set_content(body)

  return message

#health_check.py

#! /usr/bin/env python3

import os
import shutil
import psutil
import socket
from emails import generate_error_report, send_email

def check_cpu_usage():
    """Verifies that there's enough unused CPU"""
    usage = psutil.cpu_percent(1)
    return usage > 80

def check_disk_usage(disk):
    """Verifies that there's enough free space on disk"""
    du = shutil.disk_usage(disk)
    free = du.free / du.total * 100
    return free > 20

def check_available_memory():
    """available memory in linux-instance, in byte"""
    available_memory = psutil.virtual_memory().available/(1024*1024)
    return available_memory > 500

def check_localhost():
    """check localhost is correctly configured on 127.0.0.1"""
    localhost = socket.gethostbyname('localhost')
    return localhost == '127.0.0.1'

if check_cpu_usage():
    error_message = "CPU usage is over 80%"
elif not check_disk_usage('/'):
    error_message = "Available disk space is less than 20%"
elif not check_available_memory():
    error_message = "Available memory is less than 500MB"
elif not check_localhost():
    error_message = "localhost cannot be resolved to 127.0.0.1"
else:
    pass

# send email if any error reported
if __name__ == "__main__":
    try:
        sender = "automation@example.com"
        receiver = "{}@example.com".format(os.environ.get('USER'))
        subject = "Error - {}".format(error_message)
        body = "Please check your system and resolve the issue as soon as possible"
        message = generate_error_report(sender, receiver, subject, body)
        send_email(message)
    except NameError:
        pass

#report_email.py

#!/usr/bin/env python3

import reports
import emails
import os 
from datetime import date


BASEPATH_SUPPLIER_TEXT_DES = os.path.expanduser('~') + '/supplier-data/descriptions/'
list_text_files = os.listdir(BASEPATH_SUPPLIER_TEXT_DES)

report = []

def process_data(data):
	for item in data:
		report.append("name: {}<br/>weight: {}\n".format(item[0], item[1]))
	return report

text_data = []
for text_file in list_text_files:
	with open(BASEPATH_SUPPLIER_TEXT_DES + text_file, 'r') as f:
		text_data.append([line.strip() for line in f.readlines()])
		f.close()

if __name__ == "__main__":

	summary = process_data(text_data)

	# Generate a paragraph that contains the necessary summary
	paragraph = "<br/><br/>".join(summary)

	# Generate the PDF report
	title = "Processed Update on {}\n".format(date.today().strftime("%B %d, %Y"))
	attachment = "/tmp/processed.pdf"

	reports.generate_report(attachment, title, paragraph)

	# Send the email
	subject = "Upload Completed - Online Fruit Store"
	sender = "automation@example.com"
	receiver = "{}@example.com".format(os.environ.get('USER'))
	body = "All fruits are uploaded to our website successfully. A detailed list is attached to this email."
	message = emails.generate_email(sender, receiver, subject, body, attachment)
	emails.send_email(message)

#reports.py


#!/usr/bin/env python3

from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def generate_report(filename, title, additional_info):
  styles = getSampleStyleSheet()
  report = SimpleDocTemplate(filename)
  report_title = Paragraph(title, styles["h1"])
  report_info = Paragraph(additional_info, styles["Normal"])
  empty_line = Spacer(1,20)
  report.build([report_title, empty_line, report_info])

#run.py

  
#! /usr/bin/env python3

import os 
import requests


BASEPATH_SUPPLIER_TEXT_DES = os.path.expanduser('~') + '/supplier-data/descriptions/'
list_text_files = os.listdir(BASEPATH_SUPPLIER_TEXT_DES)

BASEPATH_SUPPLIER_IMAGE = os.path.expanduser('~') + '/supplier-data/images/'
list_image_files = os.listdir(BASEPATH_SUPPLIER_IMAGE)
list_images = [image_name for image_name in list_image_files if '.jpeg' in image_name]


list = []
for text_file in list_text_files:
	with open(BASEPATH_SUPPLIER_TEXT_DES + text_file, 'r') as f:
		data = {"name":f.readline().rstrip("\n"),
                "weight":int(f.readline().rstrip("\n").split(' ')[0]),
                "description":f.readline().rstrip("\n")}

		for image_file in list_images:
			if image_file.split('.')[0] in text_file.split('.')[0]:
				data['image_name'] = image_file

		list.append(data)
            
for item in list:
    resp = requests.post('http://127.0.0.1:80/fruits/', json=item)
    if resp.status_code != 201:	
        raise Exception('POST error status={}'.format(resp.status_code))
    print('Created feedback ID: {}'.format(resp.json()["id"]))

#supplier_image_upload.py


#!/usr/bin/env python3

import requests
import os


# This example shows how a file can be uploaded using
# The Python Requests module
url = "http://localhost/upload/"
IMAGE_DIR = os.path.expanduser('~') + '/supplier-data/images/'
list_image = os.listdir(IMAGE_DIR)
jpeg_images = [image_name for image_name in list_image if '.jpeg' in image_name]

for image in jpeg_images:
  with open(IMAGE_DIR + image, 'rb') as opened:
    r = requests.post(url, files={'file': opened})

