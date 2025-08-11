from django.db import models

class UploadFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    upload_date = models.DateTimeField(auto_now_add=True)
    rows = models.IntegerField()
    columns = models.IntegerField()


    def __str__(self):
        return f'{self.file.name} ({self.rows}x{self.columns})'
