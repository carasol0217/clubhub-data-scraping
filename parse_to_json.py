import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Path to your ChromeDriver
CHROME_DRIVER_PATH = '/usr/local/bin/chromedriver'

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

    # Store the scraped data as a list of dictionaries
    scraped_data = []
    
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
            
            # Scrape the description from the detail page (e.g., all <p> tags)
            try:
                description_elements = driver.find_elements(By.TAG_NAME, "p")
                descriptions = [desc.text for desc in description_elements if desc.text.strip()]
                description = "\n".join(descriptions)
            except:
                description = "No description available"
            
            # Append the data to the list
            scraped_data.append({
                "name": name,
                "link": link,
                "campus": campus,
                "areas_of_interest": areas_of_interest,
                "description": description  # Added the description
            })

            # After scraping the additional details, return to the main page to scrape the next club
            driver.back()

        except Exception as e:
            print(f"Error extracting data: {e}")

    # Close the browser
    driver.quit()

    return scraped_data

# Function to save the scraped data into a JSON file
def save_to_json(clubs, filename='scraped_clubs.json'):
    try:
        with open(filename, 'w') as json_file:
            json.dump(clubs, json_file, indent=4)
        print(f"Data has been saved to {filename}")
    except Exception as e:
        print(f"Error saving to JSON: {e}")

if __name__ == "__main__":
    # Scrape the clubs
    clubs = scrape_clubs()
    
    # If clubs were scraped, save to a JSON file
    if clubs:
        save_to_json(clubs)
    else:
        print("No data was scraped.")
