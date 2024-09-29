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

    # Store the scraped data
    scraped_data = []
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
            
            # Scrape description from the <p> tag
            try:
                description_elements = driver.find_elements(By.TAG_NAME, "p")
                descriptions = [desc.text for desc in description_elements if desc.text.strip()]
                description = "\n".join(descriptions)
            except:
                description = "No description available"
            
            # Scrape areas of interest from the <a> tags under "Areas of Interest"
            try:
                areas_elements = driver.find_elements(By.CSS_SELECTOR, "a.bg-slate-200")  # Class for the interest tags
                areas_of_interest = [area.text for area in areas_elements]
                areas_of_interest = ", ".join(areas_of_interest)
            except:
                areas_of_interest = "No areas of interest available"
            
            # After scraping the additional details, return to the main page to scrape the next club
            driver.back()

        except Exception as e:
            print(f"Error extracting data: {e}")
            name = 'N/A'
            link = 'N/A'
            campus = 'N/A'
            description = 'N/A'
            areas_of_interest = 'N/A'

        # Append all collected data
        scraped_data.append((name, link, campus, description, areas_of_interest))

    # Close the browser
    driver.quit()
    return scraped_data

# Save to a text file for review
def save_to_text_file(clubs):
    with open('scraped_clubs.txt', 'w') as file:
        for club in clubs:
            file.write(f"Club Name: {club[0]}\n")
            file.write(f"Link: {club[1]}\n")
            file.write(f"Campus: {club[2]}\n")
            file.write(f"Description: {club[3]}\n")
            file.write(f"Areas of Interest: {club[4]}\n")
            file.write("-" * 50 + "\n")

if __name__ == "__main__":
    clubs = scrape_clubs()
    if clubs:
        save_to_text_file(clubs)
        print("Data has been saved to scraped_clubs.txt for review.")
    else:
        print("No data was scraped.")
