from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from dotenv import dotenv_values

def make_client(mcc_id="") -> GoogleAdsClient:
    config = dotenv_values(".env")
    print("CONFIGGGG+>!!!!", config["account_id"])
    credentials = {
        "developer_token": config["developer_token"],
        "refresh_token": config["refresh_token"],
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "use_proto_plus": True
    }
    google_ads_client = GoogleAdsClient.load_from_dict(credentials, version="v10")
    if mcc_id != "":
        google_ads_client.login_customer_id = mcc_id
    return google_ads_client