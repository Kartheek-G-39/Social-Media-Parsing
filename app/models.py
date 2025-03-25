from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.timezone import now

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    username=models.CharField(unique=True,max_length=25)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):   
        return self.username

    groups = models.ManyToManyField(
        Group,
        related_name="customuser_set",
        blank=True,
        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="customuser_set",
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
    )
    
class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ("UPLOAD", "Uploaded a PDF"),
        ("PARSE", "Parsed social media data"),
        ("CLASSIFY", "Classified message"),
        ("DELETE", "Deleted a history entry"),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    details = models.TextField(blank=True, null=True)  # Additional details (optional)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"



class ParsedData(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    platform = models.CharField(max_length=50)
    data = models.TextField()
    generated_pdf = models.FileField(upload_to='parsed_data/')
    created_at = models.DateTimeField(auto_now_add=True)




class UserPhoneMapping(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, unique=True)  # e.g., whatsapp:+1234567890
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.phone_number}"