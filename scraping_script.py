import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from pymongo import MongoClient

def scrape_website(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract metadata
        metadata = {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source_url": url
        }

        # Extract titles and their associated paragraphs
        title_paragraphs = {}
        current_title = None

        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
            if element.name.startswith('h'):
                current_title = element.get_text()
                title_paragraphs[current_title] = []
            elif current_title is not None:
                title_paragraphs[current_title].append(element.get_text())

        return {"metadata": metadata, "sections": title_paragraphs}

    except requests.exceptions.RequestException as e:
        return {'error': f"Error during request: {e}"}

def save_to_mongodb(data, mongodb_uri, database_name, collection_name):
    client = MongoClient(mongodb_uri)
    db = client[database_name]

    # Remove existing collections with the same prefix
    for collection in db.list_collection_names():
        if collection.startswith(collection_name):
            db[collection].drop()
            print(f"Collection '{collection}' dropped.")

    # Insert the data into the MongoDB collection
    collection = db[collection_name]
    collection.insert_one(data)
    print(f"New data saved to MongoDB collection '{collection_name}'.")


def main():
    urls = [
        "https://www.usherbrooke.ca/etudiants/vie-etudiante/associations-et-regroupements-etudiants/associations-departementales",
        "https://www.usherbrooke.ca/etudiants/vie-etudiante/associations-et-regroupements-etudiants/regroupements-etudiants",
        "https://www.usherbrooke.ca/etudiants/vie-etudiante/associations-et-regroupements-etudiants/associations-etudiantes-et-etudiants-internationaux",
        "https://www.usherbrooke.ca/etudiants/vie-etudiante/associations-et-regroupements-etudiants/associations-de-cycles-superieurs",
        "https://www.usherbrooke.ca/etudiants/vie-etudiante/associations-et-regroupements-etudiants/associations-de-premier-cycle",
        "https://www.usherbrooke.ca/etudiants/vie-etudiante/associations-et-regroupements-etudiants/feus-et-remdus"
    ]

    mongodb_uri = "mongodb+srv://mohamedlaamari1998:hb9hndFafkXYFBO8@cluster0.oim5xrt.mongodb.net/?retryWrites=true&w=majority"
    database_name = "Sherbrook"
    collection_name_prefix = "website_data"

    for url in urls:
        result = scrape_website(url)

        if 'error' in result:
            print(f"Error for {url}: {result['error']}")
        else:
            # Extract title from the first h1 tag or use the full URL as a fallback
            title = result['sections'].get('h1', [url])[0]

            # Use the URL as part of the collection name for uniqueness
            collection_name = f"{collection_name_prefix}_{url.replace('https://', '').replace('/', '_')}"

            # Save data to MongoDB
            save_to_mongodb(result, mongodb_uri, database_name, collection_name)

if __name__ == "__main__":
    main()

