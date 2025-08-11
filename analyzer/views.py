import pandas as pd
import os
import matplotlib.pyplot as plt
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from .forms import UploadFileForm
from .models import UploadFile


def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid():
            uploaded_file = form.save(commit=False)
            df = pd.read_csv(request.FILES['file'])
            uploaded_file.rows, uploaded_file.columns = df.shape
            uploaded_file.save()
            return redirect('analysis', file_id=uploaded_file.id)

        else:
            form = UploadFileForm()

        return render(request, 'upload.html', {'form': form})

def analysis(request, file_id):
    file_obj = get_object_or_404(UploadFile, id=file_id)
    file_path = os.path.join(settings.MEDIA_ROOT, file_obj.file.name)

    df = pd.read_csv(file_path)

    # Descriptive statistics
    stats_html = df.describe().to_html(classes='table table-striped')

    #Example chart (histogram of first numerical column)
    numerics_cols = df.select_dtypes(include='number')
    plot_url = None

    if len(numerics_cols) > 0:
        plt.figure()
        df[numerics_cols[0]].hist()
        plot_path = os.path.join(settings.MEDIA_ROOT, 'plots')
        os.makedirs(plot_path, exist_ok=True)
        plot_file = f'plot_{file_id}.png'
        plt.savefig(os.path.join(plot_path, plot_file))
        plt.close()
        plot_url = settings.MEDIA_URL + f'plots/{plot_file}'

    return render(request, 'analysis.html', {
        'file': file_obj,
        'head_html': df.head().to_html(classes='table table-bordered'),
        'stats_html': stats_html,
        'plot_url': plot_url
    })