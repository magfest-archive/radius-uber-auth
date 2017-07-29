import os

UBER_URL = os.environ.get("UBER_URL", "https://staging3.uber.magfest.org:4444/jsonrpc/")
UBER_CERT = os.environ.get("UBER_CERT", "./client.crt")
UBER_KEY = os.environ.get("UBER_KEY", "./client.key")

service = None

STAFF_WIFI     = True
VOLUNTEER_WIFI = True
GUEST_WIFI     = True
BAND_WIFI      = True
VENDOR_WIFI    = True
PANELIST_WIFI  = True
# ;)
ATTENDEE_WIFI  = False

RLM_MODULE_REJECT   =  0 #  immediately reject the request
RLM_MODULE_FAIL     =  1 #  module failed, don't reply
RLM_MODULE_OK       =  2 #  the module is OK, continue
RLM_MODULE_HANDLED  =  3 #  the module handled the request, so stop.
RLM_MODULE_INVALID  =  4 #  the module considers the request invalid.
RLM_MODULE_USERLOCK =  5 #  reject the request (user is locked out)
RLM_MODULE_NOTFOUND =  6 #  user not found
RLM_MODULE_NOOP     =  7 #  module succeeded without doing anything
RLM_MODULE_UPDATED  =  8 #  OK (pairs modified)
RLM_MODULE_NUMCODES =  9 #  How many return codes there are

# TODO make it configurable which fields correspond to username/password

def instantiate():
    from rpctools.jsonrpc import ServerProxy
    global service
    service = ServerProxy(
        uri=UBER_URL,
        cert_file=UBER_CERT,
        key_file=UBER_KEY,
    )


def authorize(attrs):
    # a tuple of key-value tuples = a dict, yay!
    attr_dict = dict(attrs)

    if 'User-Name' in attr_dict and 'User-Password' in attr_dict:
        username = attr_dict['User-Name']
        password = attr_dict['User-Password']

        if username.startswith('"') and username.endswith('"'):
            username = username[1:-1]

        if password.startswith('"') and password.endswith('"'):
            password = password[1:-1]

        email = username
        badge = password

        try:
            badge_num = int(badge)
        except NumberParseException:
            return RLM_MODULE_REJECT

        res = service.attendee.search("email:{}".format(email))

        if len(res):
            for attendee in res:
                if attendee['email'] == email and attendee['badge_num'] == badge_num:

                    badge_type = attendee['badge_type_label']
                    ribbons = attendee['ribbon_labels']

                    can_wifi = (
                        ATTENDEE_WIFI
                        or PANELIST_WIFI and 'Panelist' in ribbons
                        or VENDOR_WIFI and 'Shopkeep' in ribbons
                        or BAND_WIFI and 'RockStar' in ribbons
                        or GUEST_WIFI and 'Guest' in ribbons
                        or VOLUNTEER_WIFI and 'Volunteer' in ribbons
                        or STAFF_WIFI and attendee.get('staffing', False)
                    )

                    if can_wifi:
                        return (
                            RLM_MODULE_OK,
                            (('Reply-Message', 'Success'),
                             ('Tech-Ops', 'Best-Ops')),
                            (('Cleartext-Password', badge),),
                        )
                    else:
                        return RLM_MODULE_REJECT
                    break

    return RLM_MODULE_NOTFOUND
