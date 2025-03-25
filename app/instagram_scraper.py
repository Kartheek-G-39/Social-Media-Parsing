import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from reportlab.pdfgen import canvas
from PIL import Image
from io import BytesIO
from django.core.files.storage import FileSystemStorage
from django.conf import settings

def scrape_instagram(username, password, target_profile):
    # Setup Chrome WebDriver
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(5)  # Allow time for page to load

        # Enter username and password
        username_input = driver.find_element(By.NAME, "username")
        password_input = driver.find_element(By.NAME, "password")

        username_input.send_keys(username)
        password_input.send_keys(password)
        password_input.send_keys(Keys.RETURN)
        time.sleep(5)  # Wait for login

        # Navigate to target profile
        driver.get(f"https://www.instagram.com/{target_profile}/")
        time.sleep(5)

        # Extract profile details
        followers = driver.find_element(By.XPATH, '//a[contains(@href, "/followers/")]/span').text
        following = driver.find_element(By.XPATH, '//a[contains(@href, "/following/")]/span').text
        posts = driver.find_element(By.XPATH, '//span[contains(text(), "posts")]/preceding-sibling::span').text

        # Capture profile screenshot
        profile_screenshot_path = os.path.join(settings.MEDIA_ROOT, f"{target_profile}_profile.png")
        driver.save_screenshot(profile_screenshot_path)

        # Scrape first 5 posts (image screenshots)
        post_images = []
        post_elements = driver.find_elements(By.XPATH, '//article//img')[:5]

        for i, post in enumerate(post_elements):
            image_url = post.get_attribute("src")
            driver.get(image_url)  # Open image in browser
            time.sleep(2)

            screenshot_path = os.path.join(settings.MEDIA_ROOT, f"{target_profile}_post_{i+1}.png")
            driver.save_screenshot(screenshot_path)
            post_images.append(screenshot_path)

        driver.quit()

        # Generate PDF report
        pdf_filename = f"{target_profile}_report.pdf"
        pdf_path = os.path.join(settings.MEDIA_ROOT, pdf_filename)
        if not os.path.exists(settings.MEDIA_ROOT):
            os.makedirs(settings.MEDIA_ROOT)

        c.save()
        create_instagram_pdf(pdf_path, target_profile, followers, following, posts, profile_screenshot_path, post_images)
        print("Saving PDF at:", pdf_path)

        return pdf_filename

    except Exception as e:
        driver.quit()
        return str(e)

def create_instagram_pdf(pdf_path, profile, followers, following, posts, profile_screenshot, post_images):
    c = canvas.Canvas(pdf_path)
    c.setFont("Helvetica", 14)
    c.drawString(100, 800, f"Instagram Report for {profile}")

    c.setFont("Helvetica", 12)
    c.drawString(100, 780, f"Followers: {followers}")
    c.drawString(100, 760, f"Following: {following}")
    c.drawString(100, 740, f"Total Posts: {posts}")

    # Add Profile Screenshot
    c.drawString(100, 700, "Profile Screenshot:")
    c.drawImage(profile_screenshot, 100, 500, width=200, height=200)

    # Add Post Screenshots
    y_position = 450
    for i, img_path in enumerate(post_images):
        c.drawString(100, y_position, f"Post {i+1} Screenshot:")
        c.drawImage(img_path, 100, y_position - 200, width=200, height=200)
        y_position -= 220
        if y_position < 100:
            c.showPage()
            y_position = 800

    c.save()
    
scrape_instagram("pravallikagudikandula","Insta@4250","mounikagudikandula")
