import os

from twilio.rest import Client
import os

account_sid = os.environ['ACCOUNT_SID']
auth_token = os.environ['AUTH_TOKEN']
verify_sid = os.environ['VERIFY_SID']

def otp_send_code(phone : str):
    #Create a Twilio client
    client = Client(account_sid, auth_token)

# Send verification code via SMS # pending
    verification = client.verify.v2.services(verify_sid) \
    .verifications \
    .create(to='+213'+phone, channel="sms")


def otp_verify_twilio_code(phone, otp_code):
    #   Create a Twilio client
    client = Client(account_sid, auth_token)
    # Check the entered OTP
    verification_check = client.verify.v2.services(verify_sid) \
        .verification_checks \
        .create(to='+213' + phone, code=otp_code)

    # Print verification check status
    print(f"Verification Check Status: {verification_check.status}")  # approved
    return verification_check.status