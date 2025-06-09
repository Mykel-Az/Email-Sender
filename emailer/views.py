from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from .models import BulkCampaign, Recipient
from .forms import ImportRecipientsForm
import pandas as pd
import csv
import logging
from io import TextIOWrapper

logger = logging.getLogger(__name__)

def process_recipient_file(file, campaign):
    """
    Process CSV or Excel file and create recipient records
    """
    recipients_created = 0
    
    try:
        if file.name.endswith('.csv'):
            # Handle CSV files
            file_wrapper = TextIOWrapper(file.file, encoding='utf-8')
            csv_reader = csv.DictReader(file_wrapper)
            
            for row in csv_reader:
                email = row.get('email', '').strip()
                recipient_name = row.get('recipient_name', '').strip()
                last_name = row.get('last_name', '').strip() 
                
                if email and recipient_name:
                    Recipient.objects.create(
                        campaign=campaign,
                        email=email,
                        recipient_name=recipient_name,
                        last_name=last_name
                    )
                    recipients_created += 1
                    
        elif file.name.endswith(('.xlsx', '.xls')):
            # Handle Excel files
            df = pd.read_excel(file)
            
            for _, row in df.iterrows():
                email = str(row.get('email', '')).strip()
                recipient_name = str(row.get('recipient_name', '')).strip()
                last_name = str(row.get('last_name', '')).strip()
                
                if email and recipient_name and email != 'nan':
                    Recipient.objects.create(
                        campaign=campaign,
                        email=email,
                        recipient_name=recipient_name,
                        last_name=last_name
                    )
                    recipients_created += 1
        else:
            raise ValueError("Unsupported file format. Please use CSV or Excel files.")
            
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise e
    
    return recipients_created



def import_recipients(request):
    """
    Handle file upload and create bulk campaign with recipients
    """
    if request.method == 'POST':
        form = ImportRecipientsForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Create the campaign
                campaign = BulkCampaign.objects.create(
                    name=form.cleaned_data['campaign_name'],
                    template_used=form.cleaned_data['template_choice']
                )
                
                # Process the uploaded file
                file = request.FILES['file']
                recipients_created = process_recipient_file(file, campaign)
                
                messages.success(
                    request, 
                    f'Campaign "{campaign.name}" created successfully with {recipients_created} recipients!'
                )
                return redirect('campaign_detail', campaign_id=campaign.id)
                
            except Exception as e:
                logger.error(f"Error creating campaign: {str(e)}")
                messages.error(request, f'Error processing file: {str(e)}')
    else:
        form = ImportRecipientsForm()
    
    return render(request, 'campaigns/import_recipients.html', {'form': form})


def campaign_list(request):
    """
    Display list of all campaigns
    """
    campaigns = BulkCampaign.objects.all().order_by('-created_at')
    paginator = Paginator(campaigns, 10)
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'campaigns/campaign_list.html', {'page_obj': page_obj})


def campaign_detail(request, campaign_id):
    """
    Display campaign details and recipients
    """
    campaign = get_object_or_404(BulkCampaign, id=campaign_id)
    recipients = campaign.recipients.all()
    
    # Get stats
    total_recipients = recipients.count()
    sent_count = recipients.filter(is_sent=True).count()
    pending_count = recipients.filter(status='pending').count()
    failed_count = recipients.filter(status='failed').count()
    
    stats = {
        'total': total_recipients,
        'sent': sent_count,
        'pending': pending_count,
        'failed': failed_count,
        'completion_rate': (sent_count / total_recipients * 100) if total_recipients > 0 else 0
    }
    
    # Paginate recipients
    paginator = Paginator(recipients, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'campaign': campaign,
        'page_obj': page_obj,
        'stats': stats
    }
    
    return render(request, 'campaigns/campaign_detail.html', context)


def send_campaign_emails(request, campaign_id):
    """
    Send emails to all pending recipients in a campaign
    """
    if request.method == 'POST':
        campaign = get_object_or_404(BulkCampaign, id=campaign_id)
        
        # Get pending recipients
        pending_recipients = campaign.recipients.filter(status='pending')
        
        if not pending_recipients.exists():
            return JsonResponse({
                'success': False, 
                'message': 'No pending recipients to send emails to.'
            })
        
        # Calculate flexible batch size based on total recipients (max 50)
        total_recipients = pending_recipients.count()
        if total_recipients <= 10:
            batch_size = 5
        elif total_recipients <= 25:
            batch_size = 10
        elif total_recipients <= 100:
            batch_size = 25
        else:
            batch_size = 50
        
        logger.info(f"Sending {total_recipients} emails in batches of {batch_size}")
        
        sent_count = 0
        failed_count = 0
        
        for i in range(0, pending_recipients.count(), batch_size):
            batch = pending_recipients[i:i + batch_size]
            
            for recipient in batch:
                success = send_industry_email(recipient, campaign.template_used)
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
        
        # Update campaign completion status
        if pending_recipients.filter(status='pending').count() == 0:
            campaign.is_completed = True
            campaign.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Batch sending completed. Sent: {sent_count}, Failed: {failed_count}',
            'sent_count': sent_count,
            'failed_count': failed_count,
            'batch_size_used': batch_size
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


def send_industry_email(recipient, template_choice):
    """
    Send a templated email based on the industry template
    """
    try:
        # Define template mapping
        template_subjects = {
            'finance': 'Transform Your Financial Operations',
            'healthcare': 'Innovative Healthcare Solutions',
            'medtech': 'Elevate Your Digital Presence',
            'logistics': 'Streamline Your Supply Chain',
            'real_estate': 'Transform Your Real Estate Listings Into Lead Magnets',
            'restaurant': 'Boost Your Business',
            'retail': 'Enhance Your Retail Experience'
        }
        
        subject = template_subjects.get(template_choice, 'Business Solutions for You')
        
        # Prepare context for email templates
        context = {
            'recipient_name': recipient.recipient_name,
            'last_name': recipient.last_name,
            'full_name': f"{recipient.recipient_name} {recipient.last_name}".strip(),
            'industry': template_choice.title(),
            'company_name': getattr(settings, 'COMPANY_NAME', 'Your Company'),
            'contact_email': getattr(settings, 'CONTACT_EMAIL', settings.DEFAULT_FROM_EMAIL),
            'website_url': getattr(settings, 'WEBSITE_URL', 'https://yourwebsite.com')
        }
        
        # Load email templates
        text_template = f'emails/industry/{template_choice}.txt'
        html_template = f'emails/industry/{template_choice}.html'
        
        try:
            text_message = render_to_string(text_template, context)
            html_message = render_to_string(html_template, context)
        except Exception as template_error:
            logger.warning(f"Template not found, using default: {template_error}")
            # Fallback to default template
            text_message = render_to_string('emails/industry/default.txt', context)
            html_message = render_to_string('emails/industry/default.html', context)
        
        # Send the email
        send_mail(
            subject,
            text_message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient.email],
            fail_silently=False,
            html_message=html_message
        )

        send_mail(
            subject=f"Notification: Email sent to {recipient.email}",
            message=f"""You successfully sent an email to:
            Recipient: {recipient.recipient_name} {recipient.last_name}
            Email: {recipient.email}
            Campaign: {recipient.campaign.name}
            message: {text_message}
            Time: {timezone.now()}""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],  # Or use settings.DEFAULT_FROM_EMAIL
            fail_silently=True
        )

        # Update recipient status
        recipient.is_sent = True
        recipient.sent_at = timezone.now()
        recipient.status = 'sent'
        recipient.save(update_fields=['is_sent', 'sent_at', 'status'])
        
        logger.info(f"Email sent successfully to {recipient.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {recipient.email}: {str(e)}")
        
        # Update recipient status to failed
        recipient.status = 'failed'
        recipient.save(update_fields=['status'])
        
        return False


def test_single_email(request, recipient_id):
    """
    Send a test email to a single recipient
    """
    if request.method == 'POST':
        recipient = get_object_or_404(Recipient, id=recipient_id)
        success = send_industry_email(recipient, recipient.campaign.template_used)
        
        if success:
            return JsonResponse({
                'success': True, 
                'message': f'Test email sent successfully to {recipient.email}'
            })
        else:
            return JsonResponse({
                'success': False, 
                'message': f'Failed to send test email to {recipient.email}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


def delete_campaign(request, campaign_id):
    """
    Delete a campaign and all its recipients
    """
    if request.method == 'POST':
        campaign = get_object_or_404(BulkCampaign, id=campaign_id)
        campaign_name = campaign.name
        campaign.delete()
        
        messages.success(request, f'Campaign "{campaign_name}" deleted successfully.')
        return redirect('campaign_list')
    
    return redirect('campaign_detail', campaign_id=campaign_id)