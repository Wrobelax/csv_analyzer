import matplotlib
import pandas as pd
import os

from django.contrib.auth.decorators import login_required

matplotlib.use('Agg')
import chardet
import plotly.express as px
import plotly.io as pio
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from .forms import UploadFileForm
from .forms import PlotForm
from .models import UploadFile

PLOTLY_DARK = pio.templates['plotly_dark'] if 'plotly_dark' in pio.templates else None


def read_csv_auto(file_path):
    with open(file_path, 'rb') as f:
        rawdata = f.read()
        result = chardet.detect(rawdata)
        encoding = result['encoding']
    return pd.read_csv(file_path, encoding=encoding, on_bad_lines='skip')


@login_required
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


@login_required
def upload_history(request):
    uploads = UploadFile.objects.filter(user=request.user).order_by('-upload_date')
    return render(request, 'history.html', {'uploads': uploads})


@login_required
def analysis(request, file_id):
    file_obj = get_object_or_404(UploadFile, id=file_id)
    if file_obj.user != request.user:
        messages.error(request, "You don't have permissions to view this file.")
        return redirect('upload_file')

    file_path = os.path.join(settings.MEDIA_ROOT, file_obj.file.name)

    df = read_csv_auto(file_path)

    # Descriptive statistics
    stats_html = df.describe().to_html(classes='table table-striped')
    plot_url = None

    # Creating charts folder
    plots_dir = os.path.join(settings.MEDIA_ROOT, 'plots')
    os.makedirs(plots_dir, exist_ok=True)

    plots = []

    numerics_cols = df.select_dtypes(include='number').columns.tolist()

    if request.method == 'POST':
        form = PlotForm(request.POST, cols=numerics_cols)
        if form.is_valid():
            x = form.cleaned_data['x_column']
            y = form.cleaned_data.get('y_column')
            plot_types = form.cleaned_data['plot_types']

            for plot_type in plot_types:
                if plot_type == 'histogram':
                    fig = px.histogram(df, x=x, template="plotly_dark", color_discrete_sequence=["#ff7f0e"])
                elif plot_type == 'box':
                    fig = px.box(df, y=x, template="plotly_dark", color_discrete_sequence=["#ff7f0e"])
                elif plot_type == 'scatter' and y:
                    fig = px.scatter(df, x=x, y=y, template="plotly_dark", color_discrete_sequence=["#2ca02c"], opacity=0.7)
                elif plot_type == 'line' and y:
                    fig = px.line(df, x=x, y=y, template="plotly_dark",color_discrete_sequence=["#d62728"])
                else:
                    fig = None

                if fig:
                    if PLOTLY_DARK is not None:
                        fig.update_layout(template=PLOTLY_DARK)

                    else:
                        fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="plotly_white")
                        )

                    include_js = 'cdn'
                    plots.append(fig.to_html(full_html=False, include_plotlyjs=include_js))



    else:
        form = PlotForm(cols=numerics_cols)

    return render(request, 'analysis.html', {
        'file' : file_obj,
        'head_html' : df.head().to_html(classes='table table-bordered'),
        'stats_html' : df.describe().to_html(classes='table table-striped'),
        'plots' : plots,
        'form' : form,
    })