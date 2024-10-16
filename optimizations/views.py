from django.shortcuts import render
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from .models import Subscription
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import render, get_object_or_404,redirect
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login
from django.utils import timezone
from .models import Subscription
from .models import OptimizationData
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
import pandas as pd
from django.contrib.auth import logout
from django.http import HttpResponse

def home(request):
    return render(request, 'home.html')

def pricing(request):
    return render(request, 'pricing.html')

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        errors = {}

        if User.objects.filter(username=username).exists():
            errors['username'] = 'Username already taken'
        if User.objects.filter(email=email).exists():
            errors['email'] = 'Email already registered'

        if errors:
            return JsonResponse({'status': 'error', 'errors': errors}, status=400)

        # Create user and return success message
        user = User.objects.create_user(username=username, email=email, password=password)
        return JsonResponse({'status': 'success', 'user_id': user.id})  # Include the user ID in the response

    return JsonResponse({'status': 'error', 'errors': {'form': 'Invalid request'}}, status=400)

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)
            # Redirect to the dashboard page with the user ID
            return redirect('dashboard', user_id=user.id)
        else:
            return JsonResponse({'status': 'error', 'errors': {'form': 'Invalid username or password'}}, status=400)
    
    return render(request, 'login.html')

def subscription_payment(request):
    # Get the user from the query parameter (user_id)
    user_id = request.GET.get('user_id')
    
    if user_id:
        user = get_object_or_404(User, id=user_id)  # Get the user created during registration
    else:
        return JsonResponse({'status': 'error', 'message': 'User not found'}, status=400)

    if request.method == 'POST':
        country = request.POST.get('country')
        is_company = request.POST.get('isCompany') == 'on'
        payment_method = request.POST.get('paymentMethod')
        subscription_type = request.POST.get('subscription_type')
        
        # Set payment details based on the method
        card_number = request.POST.get('cardNumber') if payment_method == 'creditCard' else None
        expiry_date = request.POST.get('expiryDate') if payment_method == 'creditCard' else None
        cvv = request.POST.get('cvv') if payment_method == 'creditCard' else None

        # Calculate amount and tax based on subscription type
        if subscription_type == 'free':
            amount = 0
            taxes = 0
        elif subscription_type == 'monthly':
            amount = 99
            taxes = amount * 0.03  # 3% tax
        else:  # yearly
            amount = 999
            taxes = amount * 0.06  # 6% tax

        total_amount = amount + taxes

        # Calculate expiration date based on subscription type
        today = timezone.now().date()
        if subscription_type == 'monthly':
            expiration_date = today + timezone.timedelta(days=30)
        elif subscription_type == 'yearly':
            expiration_date = today + timezone.timedelta(days=365)
        else:  # free
            expiration_date = today + timezone.timedelta(days=14)  # 2 weeks for free tier

        # Create a Subscription record in the database
        subscription = Subscription.objects.create(
            user=user,
            country=country,
            is_company=is_company,
            payment_method=payment_method,
            card_number=card_number,
            expiry_date=expiry_date,
            cvv=cvv,
            subscription_type=subscription_type,
            amount=amount,
            taxes=taxes,
            total_amount=total_amount,
            expiration_date=expiration_date
        )

        return redirect(f'/dashboard/{user.id}/')  # Redirect to the dashboard or a success page

    # Render the subscription form for GET requests
    return render(request, 'subscription.html', {'user': user})


def analyze_file(file_path):
    # Load the Excel file and perform analysis (example using pandas)
    df = pd.read_excel(file_path)
    analysis_result = df.describe().to_string()  # Example: descriptive statistics of the file
    return analysis_result

@login_required
def dashboard(request, user_id):
    # Fetch the user based on the user_id from the URL
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST' and 'file' in request.FILES:
        # Handle file upload
        file = request.FILES['file']
        fs = FileSystemStorage()

        # Save the uploaded file to the media folder
        file_path = fs.save(file.name, file)

        # Perform analysis on the uploaded file
        analysis_result = analyze_file(fs.path(file_path))

        # Save the file and analysis result to the database
        optimization_data = OptimizationData.objects.create(
            user=user,
            file=file,  # Assuming you have a FileField in your model
            analysis_result=analysis_result  # Store the result of the analysis
        )
        optimization_data.save()

        # Redirect to the same dashboard after handling the POST request
        return redirect('dashboard', user_id=user.id)

    # Fetch optimization data for the current user to display on the dashboard
    optimization_data = OptimizationData.objects.filter(user=user)

    # Get the analysis count
    analysis_count = optimization_data.count()

    # Fetch the user's subscription data
    subscription = Subscription.objects.filter(user=user).first()

    context = {
        'optimization_data': optimization_data,
        'user': user,
        'subscription': subscription,  # Add subscription to the context
        'analysis_count': analysis_count,  # Add analysis count to the context
    }

    return render(request, 'dashboard.html', context)


def submit_data(request):
    # Logic for submitting data
    return HttpResponse("Data submitted successfully")

def logout_view(request):
    logout(request)
    return redirect('home')