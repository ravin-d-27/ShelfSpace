from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password
from .models import UploadedFile, Rating
from .forms import FileUploadForm, RatingForm
from storages.backends.s3boto3 import S3Boto3Storage
from django.db.models import Sum
from django.db.models import Count

from django.shortcuts import render
from django.conf import settings
import google.generativeai as genai

@login_required
def book_list(request):
    files = UploadedFile.objects.all()
    return render(request, 'books/file_list.html', {'files': files})


@login_required
def upload_book(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file_instance = form.save(commit=False)
            file_instance.user = request.user
            file_instance.save()
            files = UploadedFile.objects.filter(user=request.user)
            return redirect('books:file_list')
    else:
        form = FileUploadForm()
    return render(request, 'books/upload_file.html', {'form': form})

@login_required
def download_book(request, unique_token):
    file_instance = get_object_or_404(UploadedFile, unique_token=unique_token)
    response = HttpResponse(file_instance.file, content_type='application/force-download')
    response['Content-Disposition'] = f'attachment; filename={file_instance.file.name}'
    return response


@login_required
def delete_book(request, unique_token):
    
    file_instance = get_object_or_404(UploadedFile, unique_token=unique_token)
    if not file_instance:
        hashed_file_id = unique_token
        try:
            file_instance = UploadedFile.objects.get(hashed_file_id=hashed_file_id)
        except UploadedFile.DoesNotExist:
            return HttpResponse("File not found.", status=404)

    storage = S3Boto3Storage()
    file_path = file_instance.file.name

    if storage.exists(file_path):
        storage.delete(file_path)

    file_instance.delete()

    files = UploadedFile.objects.filter(user=request.user)
    return redirect('books:file_list')



@login_required
def view_book(request, unique_token):
    file_instance = get_object_or_404(UploadedFile, unique_token=unique_token)
    file_path = file_instance.file.name
    file_extension = file_path.split('.')[-1].lower()
    
    if file_extension in ['jpg', 'jpeg', 'png', 'gif']:
        return FileResponse(file_instance.file, content_type='image/'+file_extension)
    elif file_extension == 'pdf':
        response = FileResponse(file_instance.file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename={file_instance.file.name}'
        return response
    else:
        return redirect('books:download_file', file_id=file_instance.id)
    
    
def share_book(request, unique_token):
    file_instance = get_object_or_404(UploadedFile, unique_token=unique_token)
    file_path = file_instance.file.name
    file_extension = file_path.split('.')[-1].lower()
    if file_extension in ['jpg', 'jpeg', 'png', 'gif']:
        return FileResponse(file_instance.file, content_type='image/'+file_extension)
    elif file_extension == 'pdf':
        response = FileResponse(file_instance.file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename={file_instance.file.name}'
        return response
    else:
        return redirect('books:download_file', unique_token=unique_token)


@login_required
def rate_book(request, unique_token):
    file_instance = get_object_or_404(UploadedFile, unique_token=unique_token)

    if request.method == 'POST':
        rate_form = RatingForm(request.POST)
        if rate_form.is_valid():
            rating_value = rate_form.cleaned_data['rating']
            total_ratings = file_instance.ratings.count()  # Total number of ratings
            current_rating = file_instance.rating
            new_total_count = total_ratings + 1
            new_total_rating = current_rating * total_ratings + rating_value
            new_average_rating = new_total_rating / new_total_count

            file_instance.total_count = new_total_count
            file_instance.rating = new_average_rating
            file_instance.save()
            
            print(new_average_rating, current_rating, total_ratings, rating_value, new_total_rating)
            Rating.objects.create(user=request.user, file=file_instance, rating=rating_value)

            return redirect('books:file_list') 
    else:
        rate_form = RatingForm()

    return render(request, 'books/rate_book.html', {'file_instance': file_instance, 'rate_form': rate_form})




genai.configure(api_key=settings.GEM_MODEL)
model = genai.GenerativeModel("gemini-2.0-flash")

@login_required
def ask_me_anything(request):
    if request.method == 'POST':
        input_question = request.POST.get('input_question', '')  
        response = model.generate_content(input_question)
        return render(request, 'books/gemini.html', {'response': response.text})
    return render(request, 'books/gemini.html', {})

@login_required
def recommend(request):
    if request.method == 'POST':
        input_question = request.POST.get('input_question', '') + "\n\nOnly Type the Book Name and Author. Not Any other thing"
        response = model.generate_content(input_question)
        return render(request, 'books/recommender.html', {'response': response.text})
    return render(request, 'books/recommender.html', {})