import psycopg2
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Path to your ChromeDriver
CHROME_DRIVER_PATH = '/usr/local/bin/chromedriver'

# Function to connect to PostgreSQL
def connect_db():
    try:
        conn = psycopg2.connect(
            dbname="clubhub",   # Replace with your database name
            user="postgres",  # Replace with your username
            password="0501",  # Replace with your password
            host="localhost",  # Replace if hosted elsewhere
            port="5432"  # Default PostgreSQL port
        )
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

# Function to insert club data into the PostgreSQL table (excluding description)
def insert_club_data(conn, name, link, campus, areas_of_interest):
    with conn.cursor() as cur:
        try:
            cur.execute("""
                INSERT INTO clubs (name, link, campus, areas_of_interest)
                VALUES (%s, %s, %s, %s);
            """, (name, link, campus, areas_of_interest))
            conn.commit()
        except Exception as e:
            print(f"Error inserting data: {e}")
            conn.rollback()

def scrape_clubs():
    # Set up the browser using Service
    service = Service(executable_path=CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service)

    driver.get("https://sop.utoronto.ca/groups/")
    
    # Wait for the club links to load
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "flex-1"))  # Correct class for <a> tags
        )
    except:
        print("The club data did not load in time.")
        driver.quit()
        return []

    # Scroll down to load all clubs
    SCROLL_PAUSE_TIME = 2
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Find all <li> elements that contain the club details
    clubs = driver.find_elements(By.CSS_SELECTOR, "li.flex.gap-8")  # Updated with more specific CSS selector

    # Connect to PostgreSQL
    conn = connect_db()
    if not conn:
        driver.quit()
        return []

    # Iterate through the clubs and extract relevant data
    for club in clubs:
        try:
            # Extract club name from the <a> tag
            name = club.find_element(By.CSS_SELECTOR, "a.flex-1.font-bold.text-primary").text
            
            # Extract link from the <a> tag
            link = club.find_element(By.TAG_NAME, "a").get_attribute("href")
            
            # Extract campus information from <span> tag
            campus = club.find_element(By.TAG_NAME, "span").text
            
            # Now access the club's detail page using the extracted link
            driver.get(link)
            time.sleep(2)  # Wait for the page to load
            
            # Scrape areas of interest from the <a> tags under "Areas of Interest"
            try:
                areas_elements = driver.find_elements(By.CSS_SELECTOR, "a.bg-slate-200")  # Class for the interest tags
                areas_of_interest = [area.text for area in areas_elements]
                areas_of_interest = ", ".join(areas_of_interest)
            except:
                areas_of_interest = "No areas of interest available"
            
            # Insert the club's data into PostgreSQL, excluding the description
            insert_club_data(conn, name, link, campus, areas_of_interest)

            # After scraping the additional details, return to the main page to scrape the next club
            driver.back()

        except Exception as e:
            print(f"Error extracting data: {e}")

    # Close the PostgreSQL connection and the browser
    conn.close()
    driver.quit()

if __name__ == "__main__":
    scrape_clubs()
    print("Scraping and data insertion completed.")
