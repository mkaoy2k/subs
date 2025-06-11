# Example usage
from db_utils import get_article

# Get the latest article in the list of categories
cats = ["spotlight", "myth", "bargain", "焦點", "講古", "好康"]
for cat in cats:
    print(f"Category: {cat}")
    article = get_article(cat)
    if article:
        print(f"\tTitle: {article['title']}")
        print(f"\tContent: {article['content']}")
        print(f"\tPublished at: {article['created_at']}")
    else:
        print(f"\tNo articles found in category: {cat}")
    print("-" * 80)
	
