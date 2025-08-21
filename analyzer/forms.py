from django import forms
from .models import UploadFile

PLOT_TYPES = [
    ('histogram', 'Histogram'),
    ('scatter', 'Scatter Plot'),
    ('line', 'Line Plot'),
    ('box', 'Box Plot'),
]

class PlotForm(forms.Form):
    x_column = forms.ChoiceField(label='Column X')
    y_column = forms.ChoiceField(label='Column Y', required=False)
    plot_types = forms.MultipleChoiceField(
        label='Plot Type',
        choices=PLOT_TYPES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    def __init__(self, *args, **kwargs):
        columns = kwargs.pop('columns', None)
        if columns is None:
            columns = kwargs.pop('cols', None)
        if columns is None:
            columns = []

        super().__init__(*args, **kwargs)

        choices = [(col, col) for col in columns]
        self.fields['x_column'].choices = choices
        self.fields['y_column'].choices = choices


class UploadFileForm(forms.ModelForm):
    class Meta:
        model = UploadFile
        fields = ['file']

    def clean_file(self):
        file = self.cleaned_data['file']
        if not file.name.endswith('.csv'):
            raise forms.ValidationError('Unsupported file type. Only CSV files are supported.')
        return file