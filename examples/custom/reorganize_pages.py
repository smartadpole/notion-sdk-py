#!/usr/bin/python3
# encoding: utf-8
'''
@author: 孙昊
@contact: smartadpole@163.com
@file: reorganize_pages.py
@time: 2025/4/11 00:24
@desc: Reorganize subpages in a Notion page based on keyword
'''
import sys
import os
CURRENT_DIR = os.path.dirname(__file__)
sys.path.append(os.path.join(CURRENT_DIR, '../../'))

from notion_client import Client
from notion_client.helpers import get_id
import argparse
import logging

def setup_client():
    """Initialize and configure the Notion client"""
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ModuleNotFoundError:
        logging.warning("python-dotenv not found. Environment variables will not be loaded from .env file")

    # Get Notion Token
    NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")

    while NOTION_TOKEN == "":
        print("NOTION_TOKEN not found.")
        NOTION_TOKEN = input("Enter your integration token: ").strip()

    # Initialize client
    notion = Client(auth=NOTION_TOKEN)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Set Notion client logger to WARNING level to hide successful HTTP requests
    logging.getLogger("notion_client").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    return notion

def get_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Reorganize Notion pages')
    parser.add_argument('page', help='Notion page URL or ID')
    parser.add_argument('keyword', help='Search keyword')
    parser.add_argument('--title', default=None, help='Custom title (optional)')
    parser.add_argument('--dry-run', action='store_true', help='Show pages to be moved without actually moving them')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode for detailed logging')
    return parser.parse_args()

def get_or_create_title_page(notion, parent_page_id, title):
    """Get existing title page or create a new one"""
    try:
        # Search for pages with the title
        search_results = notion.search(query=title,filter={"property": "object", "value": "page"}).get("results", [])

        # Check if any of the search results is a direct child of the parent page and has exact title match
        for page in search_results:
            if (page.get("parent", {}).get("page_id") == parent_page_id and
                page["properties"]["title"]["title"][0]["text"]["content"] == title):
                logging.info(f"Found existing title page: {title}")
                return page["id"]

        # If no existing page found, create a new one
        logging.info(f"Creating new title page: {title}")
        new_page = notion.pages.create(
            parent={"page_id": parent_page_id},
            properties={
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                }
            }
        )
        return new_page["id"]
    except Exception as e:
        logging.error(f"Error getting/creating title page: {e}")
        return None

def get_children_pages(notion, page_id, exclude_page_id=None):
    """Get all child pages of a given page, optionally excluding a specific page"""
    children = []
    start_cursor = None

    try:
        # First verify if the page exists and is accessible
        page = notion.pages.retrieve(page_id=page_id)
        logging.info(f"Successfully accessed page: {page['properties']['title']['title'][0]['text']['content']}")
    except Exception as e:
        print("\n" + "="*80)
        print("ACCESS DENIED: Failed to access the Notion page")
        print("="*80)
        print(f"Error details: {e}")
        print("\nPlease follow these steps to resolve the issue:")

        print("\n1. VERIFY PAGE ID")
        print("   • Get the correct page ID from your Notion URL")
        print("   • Example URL format: https://www.notion.so/your-workspace/page-title-page-id")

        print("\n2. SHARE PAGE WITH INTEGRATION")
        print("   • Open the Notion page in your browser")
        print("   • Click the '...' menu (top right)")
        print("   • Select 'Add connections'")
        print("   • Find and select your integration")

        print("\n3. CHECK INTEGRATION PERMISSIONS")
        print("   • Visit: https://www.notion.so/my-integrations")
        print("   • Verify your integration has:")
        print("     - 'Read content' permission")
        print("     - 'Update content' permission")

        print("\n4. VERIFY INTEGRATION TOKEN")
        print("   • Check your integration token")
        print("   • Token should start with 'secret_'")
        print("   • Ensure token is correctly set in environment")

        print("\n" + "="*80)
        return []

    try:
        while True:
            response = notion.blocks.children.list(
                block_id=page_id,
                start_cursor=start_cursor,
                page_size=100
            )

            for block in response["results"]:
                if block["type"] == "child_page":
                    # Skip the excluded page if specified
                    if exclude_page_id and block["id"] == exclude_page_id:
                        continue
                    children.append(block)

            if not response["has_more"]:
                break

            start_cursor = response["next_cursor"]
    except Exception as e:
        logging.error(f"Error while fetching child pages: {e}")
        return []

    return children

def move_page_to_end(notion, page, parent_page_id):
    """Move a page to the end of the parent page"""
    try:
        page_title = page["child_page"]["title"]
        
        # Get current page properties
        current_page = notion.pages.retrieve(page_id=page["id"])
        
        # Check if the page is an inline page
        is_inline_page = notion.blocks.retrieve(block_id=page['id'])["type"] == "child_page"
        if is_inline_page:
            # Append a link to the inline page
            notion.blocks.children.append(
                block_id=parent_page_id,
                children=[
                    {
                        "type": "link_to_page",
                        "link_to_page": {
                            "type": "page_id",
                            "page_id": page["id"]
                        }
                    }
                ]
            )
        else:
            # Move as a regular page
            notion.pages.update(
                page_id=page["id"],
                parent={"page_id": parent_page_id},
                properties=current_page["properties"]
            )
        return True
    except Exception as e:
        logging.error(f"Error moving page: {page_title if 'page_title' in locals() else 'Unknown'}")
        logging.error(f"Error details: {e}")
        return False

def main():
    # Parse command line arguments
    args = get_args()

    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize client
    notion = setup_client()

    # Get page ID
    try:
        if args.page.startswith("http"):
            org_page_id = get_id(args.page)
        else:
            org_page_id = args.page
        logging.info(f"Using page ID: {org_page_id}")
    except Exception as e:
        logging.error(f"Invalid page ID or URL: {e}")
        logging.error("Please provide a valid Notion page URL or ID")
        sys.exit(1)

    logging.info(f"Processing page: {org_page_id}")
    logging.info(f"Keyword: {args.keyword}")

    # Get or create title page
    title = args.title or f"Pages containing {args.keyword}"
    dst_page_id = get_or_create_title_page(notion, org_page_id, title)

    if not dst_page_id:
        logging.error("Failed to get/create title page")
        return

    # Get all child pages excluding the title page
    children = get_children_pages(notion, org_page_id, exclude_page_id=dst_page_id)
    if not children:
        logging.error("No child pages found or access denied")
        sys.exit(1)

    logging.info(f"Found {len(children)} child pages")

    # Filter pages containing keyword
    matching_pages = []
    for child in children:
        title = child["child_page"]["title"]
        if args.keyword.lower() in title.lower():
            matching_pages.append(child)

    if not matching_pages:
        logging.warning("No matching pages found")
        return

    total_pages = len(matching_pages)

    if args.dry_run:
        page_titles = [f"- {page['child_page']['title']}" for page in matching_pages]
        logging.info(f"Matching {total_pages} pages:\n" + "\n".join(page_titles))
        logging.info(f"\nTotal matching pages: {len(matching_pages)}")
        logging.info("Dry run mode: pages will not be moved")
        return

    # Move matching pages to the end of the page
    moved_count = 0
    logging.info(f"\nMoving {total_pages} pages...")

    for i, page in enumerate(matching_pages, 1):
        page_title = page["child_page"]["title"]
        if not move_page_to_end(notion, page, dst_page_id):
            logging.error(f"[{i}/{total_pages}] Failed to move: {page_title}")
        else:
            logging.info(f"[{i}/{total_pages}] Successfully moved: {page_title}")
            moved_count += 1

    if moved_count < total_pages:
        logging.error(f"\nOperation completed with errors:")
        logging.error(f"Total pages to move: {total_pages}")
        logging.error(f"Successfully moved: {moved_count}")
        logging.error(f"Failed to move: {total_pages - moved_count}")
    else:
        logging.info(f"\nSuccessfully moved all {total_pages} pages")

if __name__ == "__main__":
    main()
