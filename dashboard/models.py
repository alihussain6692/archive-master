from django.db import models

# Create your models here.
class Domain(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class FileURL(models.Model):
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name='file_urls')
    file_type = models.CharField(max_length=50)
    url = models.URLField()

    def __str__(self):
        return f"{self.file_type}: {self.url}"
    
    

class FileExtension(models.Model):
    extension = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.extension

class SensitiveJSFile(models.Model):
    filename = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.filename