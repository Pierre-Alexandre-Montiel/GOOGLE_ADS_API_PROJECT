from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .models import User
from .models import Post
from django.views.generic import DetailView, ListView, FormView, CreateView
from django.contrib.auth import authenticate, login, logout
from .log_in import LogForm
from .log_in import UpdateUser
from .log_in import PostForm
from django.contrib import auth
from .models import CustomUserCreationForm
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
import sys
from .make_client import make_client

from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v8 import GoogleAdsServiceClient
from dotenv import dotenv_values

import csv
import os
import datetime
import uuid

def get_search_terms_and_save_to_csv(account_id, mcc_id="", filename="search_terms.csv"):
    full_file_name = os.path.join("./query_cache", filename)

    client = make_client(mcc_id)
    ga_service: GoogleAdsServiceClient = client.get_service("GoogleAdsService")

    query = """
    SELECT 
        search_term_view.search_term, 
        campaign.name, metrics.cost_micros, 
        metrics.conversions, 
        metrics.ctr, 
        metrics.clicks, 
        metrics.average_cpc, 
        metrics.top_impression_percentage, 
        metrics.absolute_top_impression_percentage, 
        metrics.impressions, 
        metrics.cost_per_conversion 
    FROM 
        search_term_view 
    WHERE 
        metrics.clicks > 2
    ORDER BY 
        metrics.clicks DESC
        """

    search_request = client.get_type("SearchGoogleAdsStreamRequest")
    search_request.customer_id = account_id
    search_request.query = query
    stream = ga_service.search_stream(search_request)
    with open(full_file_name, mode='w', encoding="utf-8") as results:
        results_writer = csv.writer(results, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        results_writer.writerow(
            ['search_term', 'name', 'cost', 'conversions', 'ctr', 'clicks', 'cpc', 'top_is', 'abs_top_is',
             'impressions',
             'date', 'cpa'])
        for batch in stream:
            for row in batch.results:
                metrics = row.metrics
                segments = row.segments
                campaign = row.campaign
                search_term_view = row.search_term_view
                results_writer.writerow(
                    [search_term_view.search_term, campaign.name, metrics.cost_micros, metrics.conversions, metrics.ctr,
                     metrics.clicks, metrics.average_cpc,
                     metrics.top_impression_percentage, metrics.absolute_top_impression_percentage, metrics.impressions,
                     segments.date, metrics.cost_per_conversion])
        return client

def get_campaigns_list(client, customer_id):
    ga_service = client.get_service("GoogleAdsService")
    query = """
        SELECT
          campaign.id,
          campaign.name
        FROM campaign
        ORDER BY campaign.id"""
    stream = ga_service.search_stream(customer_id=customer_id, query=query)
    for batch in stream:
        for row in batch.results:
            print(
                f"Campaign with ID {row.campaign.id} and name "
                f'"{row.campaign.name}" was found.'
            )
_DATE_FORMAT = "%Y%m%d"
def _handle_googleads_exception(exception):
    print(
        f'Request with ID "{exception.request_id}" failed with status '
        f'"{exception.error.code().name}" and includes the following errors:'
    )
    for error in exception.failure.errors:
        print(f'\tError with message "{error.message}".')
        if error.location:
            for field_path_element in error.location.field_path_elements:
                print(f"\t\tOn field: {field_path_element.field_name}")
    sys.exit(1)


def main(client, customer_id, name, date, status, budget, bidding, spending, targeting):

    campaign_budget_service = client.get_service("CampaignBudgetService")
    campaign_service = client.get_service("CampaignService")
    campaign_budget_operation = client.get_type("CampaignBudgetOperation")
    campaign_budget = campaign_budget_operation.create
    campaign_budget.name = f"Interplanetary Budget {uuid.uuid4()}"
    campaign_budget.delivery_method = (
        client.enums.BudgetDeliveryMethodEnum.STANDARD
    )
    campaign_budget.amount_micros = 500000
    try:
        campaign_budget_response = (
            campaign_budget_service.mutate_campaign_budgets(
                customer_id=customer_id, operations=[campaign_budget_operation]
            )
        )
    except GoogleAdsException as ex:
        _handle_googleads_exception(ex)
    campaign_operation = client.get_type("CampaignOperation")
    campaign = campaign_operation.create
    campaign.name = name
    campaign.advertising_channel_type = (
        client.enums.AdvertisingChannelTypeEnum.SEARCH
    )
    if status == "pause":
        campaign.status = client.enums.CampaignStatusEnum.PAUSED
    else:
        campaign.status = client.enums.CampaignStatusEnum.ENABLED
    campaign.manual_cpc.enhanced_cpc_enabled = True
    campaign.campaign_budget = campaign_budget_response.results[0].resource_name
    campaign.network_settings.target_google_search = True
    campaign.network_settings.target_search_network = True
    campaign.network_settings.target_partner_search_network = False
    campaign.network_settings.target_content_network = True
    start_time = datetime.date.today() + datetime.timedelta(days=1)
    campaign.start_date = datetime.date.strftime(start_time, _DATE_FORMAT)
    end_time = start_time + datetime.timedelta(weeks=4)
    campaign.end_date = datetime.date.strftime(end_time, _DATE_FORMAT)
    try:
        campaign_response = campaign_service.mutate_campaigns(
            customer_id=customer_id, operations=[campaign_operation]
        )
        print(f"Created campaign {campaign_response.results[0].resource_name}.")
    except GoogleAdsException as ex:
        _handle_googleads_exception(ex)

class RegisterPost(FormView):
    model = Post
    template_name =  "home_login.html"
    form_class = PostForm
    def get(self, request):
        form = PostForm()
        return render(request, "home_login.html", {"form":form})

    def post(self, request):
        form = PostForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['campaign_name']
            date = form.cleaned_data['date']
            status = form.cleaned_data['status']
            budget = form.cleaned_data['budget']
            bidding = form.cleaned_data['biding_strategy']
            spending = form.cleaned_data['spending']
            targeting = form.cleaned_data['targeting']
            type = form.cleaned_data['campaign_type']
            save = Post(
            campaign_name = name,
            date =  date,
            budget =  budget,
            biding_strategy  = bidding,
            spending = spending,
            targeting = targeting,
            campaign_type = type
            )
            save.save()
            config = dotenv_values(".env")
            print("CONFIGGGG+>", config["account_id"])
            try:
                client = make_client(config["mcc_id"])
                # client = get_search_terms_and_save_to_csv(config["account_id"], config["mcc_id"])
                main(client, config["account_id"], name, date, status, budget, bidding, spending, targeting)
                get_campaigns_list(client, config["account_id"])
            except GoogleAdsException as ex:
                for error in ex.failure.errors:
                    print(f'\tError with message "{error.message}".')
                    if error.location:
                        for field_path_element in error.location.field_path_elements:
                            print(f"\t\tOn field: {field_path_element.field_name}")
            print(targeting)
            return render(request, "home_login.html", {"form":form})

def is_login(request):
    id = request.user.id
    len = User.objects.all()
    for i in len:
        res = i.id
    user = User.objects.get(id=res)
    auth.login(request, user)
    return render(request, "home_login.html")

class Login(FormView):
    form_class = LogForm
    template_name = 'log_in.html'
    success_url ="/"
    def form_valid(self, form):
        form = LogForm(self.request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = auth.authenticate(username=username, password=password)
            if user and user.is_active:
                auth.login(self.request, user)
                return redirect("/log")
        return redirect("/Login")

class Register(CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = "registration.html"
    success_url="/log"

class Logout(DetailView):
    def get(self,request): 
        auth.logout(request)
        return redirect('/')