from django.db import models
from django.utils import timezone
from members.models import User

class page(models.Model):
    page_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    last_updated = models.DateTimeField(default=timezone.now)
    is_pubished = models.BooleanField(default=False)

    class Meta:
        permissions = (
            ("is_admin", "User is an admin"),
        )
        indexes = [models.Index(fields=["-last_updated"])]
    
    def __str__(self):
        return f"{self.title} - {self.created_by} - {self.last_updated}"
    
class component(models.Model):
    component_id = models.AutoField(primary_key=True)
    parent_page = models.ForeignKey(page, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        indexes = [models.Index(fields=["-created"])]

    def __str__(self):
        return f"{self.title} - {self.created} - {self.created_by}"


class image(models.Model):
    image_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=25, null=False, blank=False)
    parent_component = models.ForeignKey(component, on_delete=models.CASCADE, related_name="image_field")
    image = models.ImageField(upload_to='components/images/')

    def __str__(self):
        return f"{self.image_id}: {self.title} - {self.image.url}"
    
class text(models.Model):
    parent_component = models.ForeignKey(component, on_delete=models.CASCADE, related_name="text_field")
    title = models.CharField(max_length=25, blank=False)
    short_line = models.CharField(max_length=25, blank=True, null=True)
    pargraph = models.TextField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.title}, belongs to  {self.parent_component.title}" 
    


    




