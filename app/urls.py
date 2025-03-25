from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('reset-password/<uidb64>/<token>/', views.reset_password, name='reset_password'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('login/', views.login_view, name='login'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('signup/', views.signup_view, name='signup'),
    path('home/', views.home, name='home'),
    path('web_scrapping/', views.web_scrapping,name="web_scrapping"),
    path('scrape/whatsapp/', views.fetch_whatsapp_data_view, name='fetch_whatsapp_data'),
    path('scrape/instagram/', views.fetch_instagram_data_view, name='fetch_instagram_data'), 
    path("fetch-result/",views.fetch_result,name="fetch_result"),
   
    path("classify/", views.classify_message, name="classify_message"),
    path("upload-pdf/", views.upload_pdf, name="upload_pdf"),
    path("download-pdf/", views.download_filtered_pdf, name="download_pdf"),
    path("history/", views.history_view, name="history"),
    path('delete-parsed-data/<int:file_id>/', views.delete_parsed_data_view, name="delete_parsed_data"),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('logout/',views.logout,name="logout"),

]
