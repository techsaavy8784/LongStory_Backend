from django.utils import timezone
def generateUniqueFileName(name):
    now = timezone.now()  # Get the current datetime in the current timezone
    milliseconds = (now - timezone.datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds() * 1000.0
    milliseconds = int(milliseconds)  # Convert to milliseconds and make it an integer
    return '{0}-{1}'.format(milliseconds, name)

def convertToBoolean(val):
    if val == "true" or val == True:
        return True
    elif val == "false" or val == False:
        return False
    else:
        return None