"""
Analysis Example
Device Offline Alert

This analysis must run by Time Interval. It checks if devices with given Tags
had communication in the past minutes. If not, it sends an email or sms alert.

Environment Variables
In order to use this analysis, you must setup the Environment Variable table.

account_token: Your account token
check_in_time: Minutes between the last input of the device before sending the notification.
tag_key: Device tag Key to filter the devices.
tag_value: Device tag Value to filter the devices.
email_list: Email list comma separated.
sms_list: Phone number list comma separated. The phone number must include the country code

Steps to generate an account_token:
1 - Enter the following link: https://admin.tago.io/account/
2 - Select your Profile.
3 - Enter Tokens tab.
4 - Generate a new Token with Expires Never.
5 - Press the Copy Button and place at the Environment Variables tab of this analysis.
"""
from datetime import datetime

from tagoio_sdk import Account, Analysis, Services
from tagoio_sdk.modules.Utils.envToJson import envToJson


def my_analysis(context, scope: list = None):
    # Transform all Environment Variable to JSON.
    env = envToJson(context.environment)

    if not env.get("account_token"):
        return print("You must setup an account_token in the Environment Variables.")
    elif not env.get("check_in_time"):
        return print("You must setup a check_in_time in the Environment Variables.")
    elif not env.get("tag_key"):
        return print("You must setup a tag_key in the Environment Variables.")
    elif not env.get("tag_value"):
        return print("You must setup a tag_value in the Environment Variables.")
    elif not env.get("email_list") and not env.get("sms_list"):
        return print(
            "You must setup an email_list or a sms_list in the Environment Variables."
        )

    check_in_time = int(env.get("check_in_time"))
    if check_in_time == 0:
        return print("The check_in_time must be a number.")

    account = Account(params={"token": env["account_token"]})

    # You can remove the comments on line 51 and 57 to use the Tag Filter.
    # filter = {'tags': [{'key': env['tag_key'], 'value': env['tag_value']}]}

    devices = account.devices.listDevice(queryObj={
        "page": 1,
        "amount": 1000,
        "fields": ["id", "name", "last_input"],
        # "filter": filter,
    })

    if not devices:
        return print(
            f"No device found with given tags. Key: {env['tag_key']}, Value: {env['tag_value']} "
        )

    print("Checking devices: ", ", ".join(x["name"] for x in devices))

    alert_devices = []
    for device in devices:
        now = datetime.utcnow()

        # Check the difference in minutes.
        diff = (now - device["last_input"]).total_seconds() // 60
        if diff > check_in_time:
            alert_devices.append(device["name"])

    if not alert_devices:
        return print("All devices are okay.")

    print("Sending notifications")
    email_service = Services(params={"token": context.token}).email
    sms_service = Services(params={"token": context.token}).sms

    message = f"Hi!\nYou're receiving this alert because the following devices didn't send data in the last {check_in_time} minutes.\n\nDevices:"
    message += "\n".join(alert_devices)

    if env.get("email_list"):
        # Remove space in the string
        emails = env["email_list"].replace(" ", "")

        email_service.send(email={
            "to": emails,
            "subject": "Device Offline Alert",
            "message": message,
        })

    if env.get("sms_list"):
        # Remove space in the string and convert to an Array.
        smsNumbers = env["sms_list"].replace(" ", "").split(",")

        for phone in smsNumbers:
            sms_service.send(sms={
                "to": phone,
                "message": message,
            })


# The analysis token in only necessary to run the analysis outside TagoIO
Analysis(params={"token": "MY-ANALYSIS-TOKEN-HERE"}).init(my_analysis)
