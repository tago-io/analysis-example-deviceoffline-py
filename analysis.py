"""
Analysis Example
Device Offline Alert

This analysis must run by Time Interval. It checks if devices with given Tags
had communication in the past minutes. If not, it sends an email or sms alert.

Environment Variables
In order to use this analysis, you must setup the Environment Variable table.

check_in_time: Minutes between the last input of the device before sending the notification.
tag_key: Device tag Key to filter the devices.
tag_value: Device tag Value to filter the devices.
email_list: Email list comma separated.
sms_list: Phone number list comma separated. The phone number must include the country code. Example: +5511999999999
"""
from datetime import datetime

from tagoio_sdk import Resources, Analysis, Services
from tagoio_sdk.modules.Utils.envToJson import envToJson


def my_analysis(context, scope: list = None):
    # Transform all Environment Variable to JSON.
    env = envToJson(context.environment)

    if not env.get("check_in_time"):
        return print("You must setup a check_in_time in the Environment Variables.")
    # You can remove the comments bellow and line 59 to use the Tag Filter.
    # elif not env.get("tag_key"):
    #     return print("You must setup a tag_key in the Environment Variables.")
    # elif not env.get("tag_value"):
    #     return print("You must setup a tag_value in the Environment Variables.")
    elif not env.get("email_list") and not env.get("sms_list"):
        return print(
            "You must setup an email_list or a sms_list in the Environment Variables."
        )

    check_in_time = int(env.get("check_in_time"))
    if check_in_time == 0:
        return print("The check_in_time must be a number.")

    resources = Resources()

    devices = resources.devices.listDevice(queryObj={
        "page": 1,
        "amount": 1000,
        "fields": ["id", "name", "last_input"],
        "filter": {'tags': [{'key': "org_id", 'value': "123"}]},
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
    services = Services()

    message = f"Hi!\nYou're receiving this alert because the following devices didn't send data in the last {check_in_time} minutes.\n\nDevices:"
    message += "\n".join(alert_devices)

    if env.get("email_list"):
        # Remove space in the string
        emails = env["email_list"].replace(" ", "")

        try:
            services.email.send(email={
                "to": emails,
                "subject": "Device Offline Alert",
                "message": message,
            })
        except Exception as error:
            print(error)

    if env.get("sms_list"):
        # Remove space in the string and convert to an Array.
        smsNumbers = env["sms_list"].replace(" ", "").split(",")

        for phone in smsNumbers:
            try:
                services.sms.send(sms={
                    "to": phone,
                    "message": message,
                })
            except Exception as error:
                print(error)


# The analysis token in only necessary to run the analysis outside TagoIO
Analysis.use(my_analysis, params={"token": "MY-ANALYSIS-TOKEN-HERE"})
