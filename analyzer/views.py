import pandas as pd
import os
import matplotlib.pyplot as plt
import chardet
import seaborn as sns
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from .forms import UploadFileForm
from .models import UploadFile


def read_csv_auto(file_path):
    with open(file_path, 'rb') as f:
        rawdata = f.read()
        result = chardet.detect(rawdata)
        encoding = result['encoding']
    return pd.read_csv(file_path, encoding=encoding, on_bad_lines='skip')


def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid():
            uploaded_file = form.save()

            file_path = os.path.join(settings.MEDIA_ROOT, uploaded_file.file.name)
            with open(file_path, 'wb+') as destination:
                for chunk in request.FILES['file'].chunks():
                    destination.write(chunk)

            df = read_csv_auto(file_path)

            # Saving metadata
            uploaded_file.rows = len(df)
            uploaded_file.columns = len(df.columns)
            uploaded_file.save()

            return redirect('analysis', file_id=uploaded_file.id)

    else:
        form = UploadFileForm()

    return render(request, 'upload.html', {'form': form})


def analysis(request, file_id):
    file_obj = get_object_or_404(UploadFile, id=file_id)
    file_path = os.path.join(settings.MEDIA_ROOT, file_obj.file.name)

    df = read_csv_auto(file_path)

    # Descriptive statistics
    stats_html = df.describe().to_html(classes='table table-striped')
    plot_url = None

    # Creating charts folder
    plots_dir = os.path.join(settings.MEDIA_ROOT, 'plots')
    os.makedirs(plots_dir, exist_ok=True)

    plots = []


    numerics_cols = df.select_dtypes(include='number').columns
    if len(numerics_cols) > 0:

        # Histogram
        plt.figure()
        df[numerics_cols[0]].hist(figsize=(8,8))
        hist_path = os.path.join(plots_dir, 'histogram.png')
        plt.savefig(hist_path)
        plt.close()
        plots.append(settings.MEDIA_URL + 'plots/histogram.png')

        # Boxplot
        plt.figure()
        sns.boxplot(x=df[numerics_cols[0]])
        boxpath = os.path.join(plots_dir, 'boxplot.png')
        plt.savefig(boxpath)
        plt.close()
        plots.append(settings.MEDIA_URL + 'plots/boxplot.png')

        # Heatmap
        plt.figure()
        sns.heatmap(df[numerics_cols].corr(), annot=True, cmap='coolwarm')
        heatmap_path = os.path.join(plots_dir, 'heatmap.png')
        plt.savefig(heatmap_path)
        plt.close()
        plots.append(settings.MEDIA_URL + 'plots/heatmap.png')

    return render(request, 'analysis.html', {
        'file': file_obj,
        'head_html': df.head().to_html(classes='table table-bordered'),
        'stats_html': df.describe().to_html(classes='table table-striped'),
        'plots': plots,
    })