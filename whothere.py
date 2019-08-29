# Detects motion, triggers Buzzer, LED and Relay, takes picture from RPi Camera, sends as attachment via Gmail
# Expansion of the Who's at the Door" project from Dexter Industries
#
# Altered project by Mister Ed.
# Added remote archiving via FTP, fixed variable issues, video display after the snapshot is taken,
# timestamps to image names, added email headers, and removal of local image storage.

'''
## License

The MIT License (MIT)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
'''

import grovepi
# Import smtplib for the actual sending function
import smtplib, string, subprocess, time
# added by Mister Ed
import ftplib
import os


# Here are the email package modules we'll need
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from subprocess import call

print("System Working")
#edited by Mister Ed. Original GroovePI port blocked by case column
switch = 6

led_status = 3
relay = 2
buzzer = 5
#Added by Mister Ed. NO values passed from ranger module. caused errors in original.
ultrasonic_ranger = 7

SMTP_USERNAME = 'user@someserver.com'  # Mail id of the sender
SMTP_PASSWORD = 'password here'  # Password of the sender
SMTP_RECIPIENT = 'user@someserver.com' # Mail id of the reciever
SMTP_SERVER = 'mail.myserverhere.com'  # Address of the SMTP server
SSL_PORT = 465
FTP_SITE = 'someserver.com'
FTP_USER = 'usernamehere'
FTP_PASSWORD = 'passwordhere'

while True:     # in case of IO error, restart
    try:
        grovepi.pinMode(switch,"INPUT")
        while True:
            if grovepi.digitalRead(switch) == 1:    # If the system is ON
                # by Mister Ed - added ranger variable to pass, otherwise fatal errors
                if grovepi.ultrasonicRead(ultrasonic_ranger) < 5:  # If a person walks through the door
                    print("Welcome")
                    grovepi.analogWrite(buzzer,100) # Make a sound on the Buzzer
                    time.sleep(.5)
                    grovepi.analogWrite(buzzer,0)       # Turn off the Buzzer
                    grovepi.digitalWrite(led_status,1)  # Turn on the status LED to indicate that someone has arrived
                    grovepi.digitalWrite(relay,1)       # turn on the Relay to activate an electrical device

                    # Take a picture from the Raspberry Pi camera
                    # Mister Ed -- edited delay to take snap shot to lowest value but still reliable
                    # also added timestamp to picture name so that uploads to remote location are unique
                    # and archived in order
                    myTime = str(int(time.time() * 1000))
                    imageName = 'snap' + myTime + '.jpg'
                    call (["raspistill -t 1 -o " + imageName + " -w 640 -h 480"], shell=True)
                    print("Image Shot")
                    # added by Mister Ed - 30 second live feed to attached monitor
                    call(["raspistill -v -t 30000"], shell=True)

                    p = subprocess.Popen(["runlevel"], stdout=subprocess.PIPE)
                    out, err=p.communicate()    # Connect to the mail server
                    if out[2] == '0':
                        print('Halt detected')
                        exit(0)
                    if out [2] == '6':
                        print('Shutdown detected')
                        exit(0)
                    print("Connected to mail")

                    # Create the container (outer) email message
                    TO = SMTP_RECIPIENT
                    FROM = SMTP_USERNAME
                    msg = MIMEMultipart()

                    # added by Mister Ed - add additional mail header info so emails don't appear blank while listed in email client
                    msg['FROM'] = 'Raspberry Pi'
                    msg['To'] = TO
                    msg['Subject'] = "Subject: Who's at the Door " + imageName


                    # Attach the image
                    fp = open(imageName, 'rb')
                    img = MIMEImage(fp.read())
                    fp.close()
                    msg.attach(img)

                    # Send the email -- now goes to user config'd mail server
                    print("Sending the mail")
                    server = smtplib.SMTP_SSL(SMTP_SERVER, SSL_PORT)
                    server.login(SMTP_USERNAME, SMTP_PASSWORD)
                    server.sendmail(FROM, [TO], msg.as_string())
                    server.quit()
                    print("Mail sent")

                    # transfer file to server
                    ###### section added by Mister Ed
                    print("Transfering file via FTP")
                    ftp = ftplib.FTP_TLS(FTP_SITE)
                    ftp.login(user=FTP_USER, passwd=FTP_PASSWORD)
                    ftp.cwd('public_html/piwho')

                    # print out list of files on destination FTP server
                    #print(ftp.retrlines("LIST")) # uncomment to test FTP connection

                    # uncomment to test ASCII file upload
                    #filename2 = 'test.txt'
                    #ftp.storlines('STOR ' + filename2, open(filename2))

                    # binary file upload
                    ftp.storbinary('STOR ' + imageName, open(imageName, 'rb'))

                    ftp.quit()
                    ftp.close()

                    print("FTP Done")

                    # remove local file to save space
                    os.remove(imageName)
                    print("removed " + imageName)

                    ##### end of section added by Mister Ed


                    grovepi.digitalWrite(led_status,0)  # Turn off the LED
                    grovepi.digitalWrite(relay,0)       # Turn off the Relay
    except IOError:
        print("Error")
