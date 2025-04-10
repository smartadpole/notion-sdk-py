#!/usr/bin/python3
# encoding: utf-8
'''
@author: sunhao
@contact: smartadpole@gmail.com
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
from util.utils import timeit

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
    parser.add_argument('keywords', nargs='+', help='Search keywords (multiple keywords supported)')
    parser.add_argument('--title', default=None, help='Custom title (optional)')
    parser.add_argument('--dry-run', action='store_true', help='Show pages to be moved without actually moving them')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode for detailed logging')
    return parser.parse_args()

def setup_logging(debug_mode):
    """Setup logging configuration"""
    if debug_mode:
        logging.getLogger().setLevel(logging.DEBUG)

def get_page_id(page_input):
    """Get page ID from URL or direct ID"""
    try:
        if page_input.startswith("http"):
            return get_id(page_input)
        return page_input
    except Exception as e:
        logging.error(f"Invalid page ID or URL: {e}")
        logging.error("Please provide a valid Notion page URL or ID")
        sys.exit(1)

def get_or_create_title_page(notion, parent_page_id, title):
    """Get existing title page or create a new one in parent directory"""
    try:
        # Get parent page info to get its parent directory
        parent_page = notion.pages.retrieve(page_id=parent_page_id)
        parent_directory_id = parent_page["parent"]["page_id"]

        # Search for pages with the title
        search_results = notion.search(query=title,filter={"property": "object", "value": "page"}).get("results", [])

        # Check if any of the search results is a direct child of the parent directory and has exact title match
        for page in search_results:
            if (page.get("parent", {}).get("page_id") == parent_directory_id and
                page["properties"]["title"]["title"][0]["text"]["content"] == title):
                logging.info(f"Found existing title page: {title}")
                return page["id"]

        # If no existing page found, create a new one in parent directory
        logging.info(f"Creating new title page: {title}")
        new_page = notion.pages.create(
            parent={"page_id": parent_directory_id},
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
        print_error_guide("Failed to access the Notion page", e)
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

def is_page_linked(notion, parent_page_id, page_id):
    """Check if a page is already linked in the parent page"""
    try:
        # Get all children blocks of the parent page
        children = notion.blocks.children.list(block_id=parent_page_id)

        # Check if any block is a link_to_page pointing to our page
        for block in children["results"]:
            if (block["type"] == "link_to_page" and
                    block["link_to_page"]["type"] == "page_id" and
                    block["link_to_page"]["page_id"] == page_id):
                return True
        return False
    except Exception as e:
        logging.error(f"Error checking page link: {e}")
        return False

@timeit(5)
def move_page(notion, page, parent_page_id):
    """Move a page to the end of the parent page"""
    try:
        page_title = page["child_page"]["title"]

        # Get current page properties
        current_page = notion.pages.retrieve(page_id=page["id"])

        # Check if the page is an inline page
        is_inline_page = notion.blocks.retrieve(block_id=page['id'])["type"] == "child_page"
        if is_inline_page:
            if is_page_linked(notion, parent_page_id, page['id']):
                return True
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

def print_error_guide(error_type, error_details=None):
    """Print detailed error guide for Notion API errors"""
    print("\n" + "="*80)
    print(f"ACCESS DENIED: {error_type}")
    print("="*80)
    if error_details:
        print(f"Error details: {error_details}")
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

def create_title_pages(notion, parent_page_id, keywords, custom_title=None):
    """Create title pages for each keyword"""
    title_pages = {}
    for keyword in keywords:
        title = custom_title or f"{keyword}"
        dst_page_id = get_or_create_title_page(notion, parent_page_id, title)
        if not dst_page_id:
            print_error_guide(f"Failed to get/create title page for keyword: {keyword}")
            continue
        title_pages[keyword] = dst_page_id
    return title_pages

def filter_matching_pages(children, keywords):
    """Filter pages containing keywords"""
    matching_pages = {keyword: [] for keyword in keywords}
    for child in children:
        title = child["child_page"]["title"]
        for keyword in keywords:
            if keyword.lower() in title.lower():
                matching_pages[keyword].append(child)
    return matching_pages

def display_dry_run_results(matching_pages):
    """Display results in dry run mode"""
    for keyword, pages in matching_pages.items():
        if pages:
            page_titles = [f"- {page['child_page']['title']}" for page in pages]
            logging.info(f"\nMatching pages for keyword '{keyword}':\n" + "\n".join(page_titles))
    logging.info("\nDry run mode: pages will not be moved")

def move_pages_for_keyword(notion, pages, dst_page_id, keyword, keyword_index, total_keywords):
    """Move pages for a specific keyword"""
    if not pages:
        return 0

    total_pages = len(pages)
    logging.info(f"\nMoving {total_pages} pages for keyword '{keyword}' ({keyword_index}/{total_keywords})...")

    moved_count = 0
    for i, page in enumerate(pages, 1):
        page_title = page["child_page"]["title"]
        if not move_page(notion, page, dst_page_id):
            logging.error(f"[{i}/{total_pages}][{keyword_index}/{total_keywords}] Failed to move: {page_title}")
        else:
            logging.info(f"[{i}/{total_pages}][{keyword_index}/{total_keywords}] Successfully moved: {page_title}")
            moved_count += 1

    if moved_count < total_pages:
        logging.error(f"\nOperation completed with errors for keyword '{keyword}' ({keyword_index}/{total_keywords}):")
        logging.error(f"Total pages to move: {total_pages}")
        logging.error(f"Successfully moved: {moved_count}")
        logging.error(f"Failed to move: {total_pages - moved_count}")

    return moved_count

def main():
    # Parse command line arguments
    args = get_args()

    # Setup logging
    setup_logging(args.debug)

    # Initialize client
    notion = setup_client()

    # Get page ID
    org_page_id = get_page_id(args.page)
    logging.info(f"Using page ID: {org_page_id}")
    logging.info(f"Processing page: {org_page_id}")
    logging.info(f"Keywords: {', '.join(args.keywords)}")

    # Create title pages
    title_pages = create_title_pages(notion, org_page_id, args.keywords, args.title)
    if not title_pages:
        print_error_guide("Failed to create any title pages")
        return

    # Get all child pages excluding the title pages
    children = get_children_pages(notion, org_page_id, exclude_page_id=list(title_pages.values()))
    if not children:
        logging.error("No child pages found or access denied")
        sys.exit(1)

    logging.info(f"Found {len(children)} child pages")

    # Filter matching pages
    matching_pages = filter_matching_pages(children, args.keywords)
    if not any(matching_pages.values()):
        logging.warning("No matching pages found")
        return

    # Dry run mode
    if args.dry_run:
        display_dry_run_results(matching_pages)
        return

    # Move pages
    total_moved = 0
    total_keywords = len(matching_pages)
    for keyword_index, (keyword, pages) in enumerate(matching_pages.items(), 1):
        dst_page_id = title_pages[keyword]
        total_moved += move_pages_for_keyword(notion, pages, dst_page_id, keyword, keyword_index, total_keywords)

    if total_moved > 0:
        logging.info(f"\nSuccessfully moved {total_moved} pages in total")

if __name__ == "__main__":
    main()
