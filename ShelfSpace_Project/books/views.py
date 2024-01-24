from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import UploadedFile
from .forms import FileUploadForm
from storages.backends.s3boto3 import S3Boto3Storage

def homepage(request):
    return render(request,"books/homepage.html")

@login_required
def file_list(request):
    files = UploadedFile.objects.filter(user=request.user)
    return render(request, 'books/book_list.html', {'files': files})

@login_required
def upload_file(request):
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
def download_file(request, file_id):
    file = get_object_or_404(UploadedFile, id=file_id)
    response = HttpResponse(file.file, content_type='application/force-download')
    response['Content-Disposition'] = f'attachment; filename={file.file.name}'
    return response


@login_required
def delete_file(request, file_id):
    file_instance = get_object_or_404(UploadedFile, id=file_id)
    storage = S3Boto3Storage()
    file_path = file_instance.file.name

    if storage.exists(file_path):
        storage.delete(file_path)
    file_instance.delete()
    
    
    files = UploadedFile.objects.filter(user=request.user)
    return redirect('books:book_list')

from django.http import FileResponse

@login_required
def view_file(request, file_id):
    file_instance = get_object_or_404(UploadedFile, id=file_id)
    file_path = file_instance.file.name
    file_extension = file_path.split('.')[-1].lower()
    if file_extension in ['jpg', 'jpeg', 'png', 'gif']:
        return FileResponse(file_instance.file, content_type='image/'+file_extension)
    elif file_extension == 'pdf':
        response = FileResponse(file_instance.file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename={file_instance.file.name}'
        return response
    else:
        return redirect('books:download_file', file_id=file_id)
    