import os
import sys
from pprint import pprint

from notion_client import Client
from time import time

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    print("Could not load .env because python-dotenv not found.")
else:
    load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")

while NOTION_TOKEN == "":
    print("NOTION_TOKEN not found.")
    NOTION_TOKEN = input("Enter your integration token: ").strip()

# Initialize the client
notion = Client(auth=NOTION_TOKEN)


def get_property(query):
    property = None
    property = properties.get(query)
    if property:
        property = property["name"]
        print(f"find {query} property: {property}")
    else:
        print(f"no {query} property, creating...")
        property = query

        notion.databases.update(
            database_id=database_id,
            properties={
                property : {
                    "rich_text": {}
                }
            }
        )
        print("create success.")

    return property

# Search for an item
print("\nSearching for database 'People' ")
results = notion.search(query="People").get("results")
print(len(results))
result = results[0]
print("The result is a", result["object"])
pprint(result["properties"])

database_id = result["id"]  # store the database id in a variable for future use

properties = result["properties"]
title_property = next((name for name, prop in properties.items()
                       if prop["type"] == "title"), None)
if not title_property:
    print("警告: 未找到标题类型属性")
    title_property = list(properties.keys())[0]

print(f"\ndatabase title name is: {title_property}")

github_property = get_property("GitHub")

# Create a new page
your_name = input("\n\nEnter your name: ")
gh_uname = input("Enter your github username: ")
new_page = {
    title_property: {"title": [{"text": {"content": your_name}}]},
    # "Tags": {"type": "multi_select", "multi_select": [{"name": "python"}]},
    github_property : {
        "type": "rich_text",
        "rich_text": [
            {
                "type": "text",
                "text": {"content": gh_uname},
            },
        ],
    },
}

start = time()
notion.pages.create(parent={"database_id": database_id}, properties=new_page)
print(f"You were added to the People database! use time: {(time() - start):.2f}s")


# Query a database
start = time()
name = input("\n\nEnter the name of the title to search in People: ")
results = notion.databases.query(
    **{
        "database_id": database_id,
        "filter": {"property": title_property, "rich_text": {"contains": name}},
    }
).get("results")

no_of_results = len(results)

if no_of_results == 0:
    print("No results found.")
    sys.exit()

print(f"No of results found: {len(results)}, use time: {(time() - start):.2f} s")

result = results[0]

print(f"The first result is a {result['object']} with id {result['id']}.")
print(f"This was created on {result['created_time']}")
