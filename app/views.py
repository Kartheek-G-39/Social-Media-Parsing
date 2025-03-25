# views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, ProfileUpdateForm
from .models import CustomUser, ActivityLog, ParsedData
import random
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Temporary OTP storage
otp_storage = {}

# Authentication Views (unchanged)
def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'signup.html', {'form': form, 'errors': form.errors})
    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            otp = random.randint(100000, 999999)
            otp_storage[user.username] = otp
            send_mail(
                "Your Login OTP",
                f"Your OTP for login is {otp}.",
                "noreply@example.com",
                [user.email],
                fail_silently=False,
            )
            request.session['username'] = username
            return redirect('verify_otp')
        else:
            messages.error(request, "Invalid username or password")
    return render(request, "login.html")

def verify_otp_view(request):
    if request.method == "POST":
        username = request.session.get('username')
        entered_otp = request.POST.get("otp")
        if username in otp_storage and otp_storage[username] == int(entered_otp):
            user = CustomUser.objects.get(username=username)
            login(request, user)
            del otp_storage[username]
            return redirect('home')
        else:
            messages.error(request, "Invalid OTP")
    return render(request, "verify_otp.html")

def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = CustomUser.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            reset_link = request.build_absolute_uri(reverse('reset_password', kwargs={'uidb64': uidb64, 'token': token}))
            subject = "Password Reset Request"
            message = render_to_string("password_reset_email.html", {"user": user, "reset_link": reset_link})
            send_mail(subject, message, "your-email@example.com", [email])
            messages.success(request, "A password reset link has been sent to your email.")
            return redirect("forgot_password")
        except CustomUser.DoesNotExist:
            messages.error(request, "No user found with that email address.")
    return render(request, "forgot_password.html")

def reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (CustomUser.DoesNotExist, ValueError, TypeError, OverflowError):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            new_password = request.POST.get("new_password")
            confirm_password = request.POST.get("confirm_password")
            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, "Your password has been successfully reset.")
                return redirect("login")
            else:
                messages.error(request, "Passwords do not match. Please try again.")
        return render(request, "reset_password.html", {"uidb64": uidb64, "token": token})
    else:
        messages.error(request, "The reset link is invalid or has expired.")
        return redirect("forgot_password")

# Home and Dashboard
@login_required
def home(request):
    return render(request, "home.html")

@login_required
def web_scrapping(request):
    return render(request, "web_scrapping.html")

# WhatsApp Scraping


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.http import HttpResponse
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
import os
from .models import ActivityLog, ParsedData

# Twilio credentials (store these in settings.py or environment variables)
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

@login_required
def fetch_whatsapp_data_view(request):
    if request.method == "POST":
        chat_name = request.POST.get("chat_name")
        num_messages = request.POST.get("num_messages", "10")  # Default to 10 if not specified

        # Validate inputs
        if not chat_name:
            messages.error(request, "Please enter a chat name.")
            return redirect("fetch_whatsapp_data")

        try:
            num_messages = int(num_messages)
            if num_messages <= 0:
                raise ValueError("Number of messages must be a positive integer.")
        except ValueError:
            messages.error(request, "Please enter a valid number of messages.")
            return redirect("fetch_whatsapp_data")

        # Set up the ChromeDriver
        chrome_driver_path = "C://Users//miriy//Projects//sample//chromedriver-win64//chromedriver.exe"
        service = Service(chrome_driver_path)
        driver = webdriver.Chrome(service=service)

        try:
            print("Opening WhatsApp...")
            driver.get('https://web.whatsapp.com/')
            input("Scan the QR code and press Enter to continue...")

            # Search for the chat
            print(f"Searching for chat: {chat_name}...")
            search_box = driver.find_element(By.XPATH, '//div[@contenteditable="true"]')
            search_box.send_keys(chat_name)
            search_box.send_keys(Keys.RETURN)
            time.sleep(3)  # Wait for the chat to load

            # Scroll to load more messages
            print("Scrolling to load messages...")
            for _ in range(5):  # Scroll multiple times to load more messages
                driver.execute_script("window.scrollTo(0, -document.body.scrollHeight);")
                print("hello")
                time.sleep(2)

            # Fetch messages
            print("Fetching messages...")
            messages = driver.find_elements(By.XPATH, '//span[contains(@class, "selectable-text")]')
            total_messages = len(messages)
            print(f"Total messages found: {total_messages}")

            # Determine how many messages to retrieve
            if total_messages < num_messages:
                messages_to_retrieve = messages
                messages_info = f"There are only {total_messages} messages in the chat."
            else:
                messages_to_retrieve = messages[-num_messages:]
                messages_info = f"Retrieved the last {num_messages} messages."

            # Prepare message data
            message_data = []
            for msg in messages_to_retrieve:
                message_text = msg.text
                if message_text.strip():
                    formatted_message = f"{chat_name}: {message_text}  Date: {datetime.now().strftime('%Y-%m-%d')}"
                    message_data.append(formatted_message)

            # Generate PDF
            print("Generating PDF...")
            pdf_filename = f"whatsapp_{chat_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
            pdf_path = os.path.join(settings.MEDIA_ROOT, pdf_filename)
            c = canvas.Canvas(pdf_path, pagesize=letter)
            width, height = letter
            y_position = height - 40

            c.setFont("Helvetica", 12)
            c.drawString(30, y_position, f"WhatsApp Chat: {chat_name} - {datetime.now().strftime('%d/%m/%Y')}")
            y_position -= 20
            c.drawString(30, y_position, messages_info)
            y_position -= 30

            for msg in message_data:
                c.drawString(30, y_position, msg[:100])  # Truncate long messages for display
                y_position -= 20
                if y_position < 40:
                    c.showPage()
                    y_position = height - 40

            c.save()

            # Save to database
            print("Saving to database...")
            fs = FileSystemStorage()
            pdf_file = fs.save(pdf_filename, open(pdf_path, 'rb'))
            parsed_data = ParsedData(
                user=request.user,
                platform="WhatsApp",
                data=str(message_data),
                generated_pdf=pdf_file
            )
            parsed_data.save()

            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action="PARSE",
                details=f"Scraped WhatsApp chat: {chat_name}"
            )

            driver.quit()

            return render(request, "fetch_result.html", {
                "pdf_url": f"/media/{pdf_filename}",
                "platform": "WhatsApp"
            })

        except Exception as e:
            driver.quit()
            messages.error(request, f"Error fetching WhatsApp data: {str(e)}")
            return redirect("fetch_whatsapp_data")

    return render(request, "fetch_form.html")
# Instagram Scraping


from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

@login_required
def fetch_instagram_data_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        target_profile = request.POST.get("target_profile")

        chrome_driver_path = "C://Users//miriy//Projects//sample//chromedriver-win64//chromedriver.exe"
        service = Service(chrome_driver_path)
        driver = webdriver.Chrome(service=service)

        try:
            print("Opening Instagram...")
            driver.get("https://www.instagram.com/")
            time.sleep(3)

            # Login
            print("Logging in...")
            try:
                username_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "username"))
                )
                password_field = driver.find_element(By.NAME, "password")
                username_field.send_keys(username)
                password_field.send_keys(password)
                login_button = driver.find_element(By.XPATH, '//button[@type="submit"]')
                login_button.click()
                time.sleep(5)
            except Exception as e:
                driver.quit()
                messages.error(request, f"Login failed: {str(e)}")
                return redirect("fetch_instagram_data")

            # Handle "Save Your Login Info?" prompt
            try:
                not_now_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[text()="Not Now"]'))
                )
                not_now_button.click()
                time.sleep(2)
            except:
                pass

            # Navigate to target profile
            print(f"Navigating to profile: {target_profile}...")
            driver.get(f"https://www.instagram.com/{target_profile}/")
            time.sleep(3)

            # Extract profile stats (posts, followers, following)
            # After fetching profile stats
            try:
                posts = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//header//section//li[1]//span/span'))
                ).text
                followers = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//header//section//li[2]//span/span'))
                ).text
                following = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//header//section//li[3]//span/span'))
                ).text
                print(f"Scraped stats - Posts: {posts}, Followers: {followers}, Following: {following}")
            except Exception as e:
                driver.quit()
                messages.error(request, f"Error fetching profile stats: {str(e)}")
                return redirect("fetch_instagram_data")

            # Check if posts are zero
            if posts == "0":
                print("No posts found for this profile.")
                comments_data = [{"likes": "0 likes", "comments": ["No posts found."]}]
            else:
                # Proceed with fetching comments/likes
                comments_data = []
                print("Fetching recent posts...")

                try:
                    # Scroll to load posts
                    all_links = set()  # To store unique links
                    for _ in range(2):
                        # Scroll down
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(3)

                        # Fetch links after each scroll
                        post_links = WebDriverWait(driver, 10).until(
                            EC.presence_of_all_elements_located((By.XPATH, '//a[contains(@href, "/p/")]'))
                        )

                        # Add new links to the set to ensure uniqueness
                        all_links.update(link.get_attribute("href") for link in post_links)

                    print(f"Total unique links collected: {len(all_links)}")
                    post_links = list(all_links)

                    post_urls = post_links
                    print(f"Found {len(post_urls)} unique posts to scrape: {post_urls}")

                    for post_url in post_urls:
                        print(f"Navigating to post: {post_url}")
                        driver.get(post_url)
                        time.sleep(3)

                        # Scroll to load all content
                        for _ in range(5):
                            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                            time.sleep(3)

                        # Extract likes
                        try:
                            print("Attempting to scrape likes...")
                            likes_elements = WebDriverWait(driver, 20).until(
                                EC.presence_of_all_elements_located((By.XPATH, '//a[contains(@href, "liked_by")]/span[contains(text(), "likes")]'))
                            )
                            likes = "0 likes"
                            for element in likes_elements:
                                text = element.text.lower()
                                if "like" in text and text.strip():
                                    likes = element.text
                                    break

                            print(f"Successfully scraped likes: {likes}")

                        except Exception as e:
                            print(f"Error fetching likes for {post_url}: {str(e)}")
                            likes = "0 likes"

                        # Extract comments
                        try:
                            print("Attempting to scrape comments...")
                            for i in range(5):
                                try:
                                    load_more = WebDriverWait(driver, 5).until(
                                        EC.element_to_be_clickable((By.XPATH, '//span[contains(text(), "Load more comments") or contains(text(), "View more comments")]'))
                                    )
                                    load_more.click()
                                    time.sleep(3)
                                except:
                                    print("No more 'Load more comments' button found or error occurred")
                                    break

                            comment_elements = driver.find_elements(By.XPATH, '//ul//li//div//span[@dir="auto"]')
                            comments = []
                            for c in comment_elements:
                                comment_text = c.get_attribute("innerText").strip()
                                if comment_text and "like" not in comment_text.lower() and len(comment_text) > 2:
                                    comments.append(comment_text)

                            print(f"Found {len(comments)} comments: {comments}")

                        except Exception as e:
                            print(f"Error fetching comments for {post_url}: {str(e)}")
                            comments = []

                        comments_data.append({"likes": likes, "comments": comments})
                        print(f"Scraped post: {post_url} - Likes: {likes}, Comments: {comments}")
                        driver.back()
                        time.sleep(2)

                except Exception as e:
                    print(f"Error fetching comments/likes: {str(e)}")
                    comments_data.append({"likes": "0 likes", "comments": []})

            driver.quit()

            # Prepare data
            scraped_data = {
                "followers": followers,
                "following": following,
                "posts": posts,
                "comments_data": comments_data
            }

            # Generate PDF
            print("Generating PDF...")
            pdf_filename = f"instagram_{target_profile}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
            pdf_path = os.path.join(settings.MEDIA_ROOT, pdf_filename)

            font_path = os.path.join(settings.BASE_DIR, "fonts", "DejaVuSans.ttf")
            pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))

            c = canvas.Canvas(pdf_path, pagesize=letter)
            c.setFont("DejaVuSans", 12)
            width, height = letter
            y_position = height - 40

            c.drawString(30, y_position, f"Instagram Profile: {target_profile} - {datetime.now().strftime('%d/%m/%Y')}")
            y_position -= 30
            c.drawString(30, y_position, f"Followers: {followers} | Following: {following} | Posts: {posts}")
            y_position -= 30

            # Write comments with emoji support
            if posts == "0":
                c.drawString(30, y_position, "No posts found.")
            else:
                for i, post in enumerate(comments_data, 1):
                    c.drawString(30, y_position, f"Post {i}: {post['likes']}")
                    y_position -= 20
                    for comment in post["comments"]:
                        if y_position < 40:  # New page if space is low
                            c.showPage()
                            c.setFont("DejaVuSans", 12)
                            y_position = height - 40
                        c.drawString(40, y_position, f"- {comment}")
                        y_position -= 20

            c.save()

            # Save to database
            fs = FileSystemStorage()
            pdf_file = fs.save(pdf_filename, open(pdf_path, 'rb'))
            parsed_data = ParsedData(
                user=request.user,
                platform="Instagram",
                data=str(comments_data),
                generated_pdf=pdf_file
            )
            parsed_data.save()

            ActivityLog.objects.create(
                user=request.user,
                action="PARSE",
                details=f"Scraped Instagram profile: {target_profile}"
            )

            return render(request, "fetch_result.html", {"pdf_url": f"/media/{pdf_filename}", "platform": "Instagram"})

        except Exception as e:
            driver.quit()
            messages.error(request, f"Unexpected error: {str(e)}")
            return redirect("fetch_instagram_data")

    return render(request, "fetch_instagram_form.html")

# History View (unchanged)
@login_required
def history_view(request):
    activities = ActivityLog.objects.filter(user=request.user).order_by("-timestamp")
    parsed_files = ParsedData.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "history.html", {"activities": activities, "parsed_files": parsed_files})

@login_required
def delete_history(request, history_id):
    try:
        history_entry = ActivityLog.objects.get(id=history_id, user=request.user)
        history_entry.delete()
    except ActivityLog.DoesNotExist:
        pass
    return redirect("history")

@login_required
def update_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'profile_update.html', {'form': form})

# Other views (classify_message, upload_pdf, etc.) remain unchanged



from django.http import JsonResponse
from .hate_offense_model import predict_comment


from .models import ActivityLog

def classify_message(request):
    result = None
    color = "black"  # Default color

    if request.method == "POST":
        text = request.POST.get("message")
        result = predict_comment(text)

        # Assign color based on prediction
        if result == "Hate Speech":
            color = "red"
        elif result == "Offensive":
            color = "orange"
        else:
            color = "green"

        # Log classification activity
        if text:
            ActivityLog.objects.create(
                user=request.user,
                action="CLASSIFY",
                details=f"Classified message: {text[:50]}... ({result})"
            )

    return render(request, "classify.html", {"result": result, "color": color})



import os
import fitz  # PyMuPDF
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.http import FileResponse
from .ai_model import classify_text



from .models import ActivityLog, ParsedData

def upload_pdf(request):
    if request.method == "POST" and request.FILES.get("pdf_file"):
        pdf_file = request.FILES["pdf_file"]

        # Save uploaded PDF
        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
        filename = fs.save(pdf_file.name, pdf_file)
        file_path = os.path.join(settings.MEDIA_ROOT, filename)

        # Log file upload activity
        ActivityLog.objects.create(
            user=request.user,
            action="UPLOAD",
            details=f"Uploaded PDF: {filename}"
        )

        # Extract text from PDF
        extracted_text = extract_text_from_pdf(file_path)

        # Process and generate filtered PDF (contains only offensive content)
        filtered_content = []
        for line in extracted_text.split("\n"):
            if line.strip():
                label = classify_text(line)
                if label in ["Hate Speech", "Offensive"]:
                    filtered_content.append(f"{label}: {line}")

        # Generate extracted PDF
        extracted_pdf_path = generate_filtered_pdf(filtered_content, filename)

        classifications = []
        for line in extracted_text.split("\n"):
            if line.strip():
                label = classify_text(line)
                classifications.append((line, label))

        # Save parsed file details in ParsedData model
        parsed_entry = ParsedData.objects.create(
            user=request.user,
            platform="Uploaded PDF",
            data=f"Extracted from {filename}",
            generated_pdf=extracted_pdf_path
        )

        # Log extracted PDF generation
        ActivityLog.objects.create(
            user=request.user,
            action="PARSE",
            details=f"Extracted PDF Generated: {parsed_entry.generated_pdf.name}"
        )

        return render(request, "result.html", {"filtered_pdf": extracted_pdf_path})

    return render(request, "upload.html")



def extract_text_from_pdf(pdf_path):
    """Extracts text from a given PDF file."""
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text() + "\n"
    return text


def generate_filtered_pdf(filtered_content, original_filename):
    """Creates a new PDF containing only detected offensive/hate speech content."""
    if not filtered_content:
        return None  # No offensive content found

    new_pdf_path = os.path.join(settings.MEDIA_ROOT, f"filtered_{original_filename}")
    
    # Create a new PDF
    doc = fitz.open()
    page = doc.new_page()
    text = "\n".join(filtered_content)
    
    # Add text to the PDF
    page.insert_text((50, 50), text, fontsize=12)
    
    # Save the PDF
    doc.save(new_pdf_path)
    doc.close()

    return new_pdf_path


def download_filtered_pdf(request):
    """Serves the generated filtered PDF for download."""
    pdf_path = request.GET.get("file")
    
    if pdf_path and os.path.exists(pdf_path):
        return FileResponse(open(pdf_path, "rb"), as_attachment=True, filename=os.path.basename(pdf_path))
    
    return render(request, "error.html", {"message": "File not found!"})




from .models import ActivityLog, ParsedData

@login_required
def history_view(request):
    """Display user's past activities and parsed data."""
    activities = ActivityLog.objects.filter(user=request.user).order_by("-timestamp")
    parsed_files = ParsedData.objects.filter(user=request.user).order_by("-created_at")

    return render(request, "history.html", {"activities": activities, "parsed_files": parsed_files})

@login_required
def delete_parsed_data_view(request, file_id):
    try:
        # Get the ParsedData object
        parsed_data = ParsedData.objects.get(id=file_id, user=request.user)
    except ParsedData.DoesNotExist:
        messages.error(request, "File not found or you do not have permission to delete it.")
        return redirect("history")

    if request.method == "POST":
        # Get the path to the PDF file
        pdf_path = parsed_data.generated_pdf.path

        # Delete the file from the filesystem
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            print(f"Deleted file: {pdf_path}")
        else:
            print(f"File not found on filesystem: {pdf_path}")

        # Log the deletion activity
        ActivityLog.objects.create(
            user=request.user,
            action="DELETE",
            details=f"Deleted parsed data for platform: {parsed_data.platform}"
        )

        # Delete the ParsedData entry
        parsed_data.delete()
        messages.success(request, "File deleted successfully.")
        return redirect("history")

    # If not a POST request, redirect back to history
    return redirect("history")

from .forms import ProfileUpdateForm

@login_required
def update_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('dashboard')  # Redirect back to dashboard
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'profile_update.html', {'form': form})



def index(request):
    return render(request, "index.html")


@login_required
def fetch_result(request):
    return render(request, "fetch_result.html")


def logout(request):
    return render(request,"index.html")