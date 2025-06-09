from django import forms
from .models import BulkCampaign

class ImportRecipientsForm(forms.Form):
    campaign_name = forms.CharField(max_length=100)
    template_choice = forms.ChoiceField(choices=[
        ('finance', 'Finance'),
        ('healthcare', 'Healthcare'),
        ('medtech', 'Medtech'),
        ('logistics', 'Logistics'),
        ('real estate', 'Real Estate'),
        ('restaurant', 'Restaurant'),
        ('retail', 'Retail'),
    ])
    file = forms.FileField(label='Select Excel/CSV file')