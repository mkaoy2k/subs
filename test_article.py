# Example usage
from db_utils import get_articles_byDays, get_articles

# Get the latest article in the list of categories
cats = ["Spotlight", "Myth", "Bargain", 
        "焦點", "講古", "好康"]
l_home = {}

for cat in cats:
    print(f"Category: {cat}")
    # articles = get_articles(cat, limit=5)
    # if articles:
    #     for idx, article in enumerate(articles, 1):
    #         print("*" * 20) 
    #         print(f"\tTitle: {article['title']}")
    #         print(f"\tContent: {article['content']}")
    #         print(f"\tCreated at: {article['created_at']}")
    #         print(f"\tUpdated at: {article['updated_at']}")
    # else:
    #     print(f"\tNo articles found in category: {cat}")
    # print("=" * 20)
    
    articles = get_articles_byDays(cat, byDays=7)
    if articles:
        l_home[cat] = {}
        for idx, article in enumerate(articles, 1):
            l_home[cat][str(idx)] = {
                "title": article['title'],
                "content": article['content'],
                "image": article['image_url']
            }
    else:
        print(f"\tNo articles found in category: {cat}")
    print(f"{cat} articles: {l_home[cat]}")
    print("=" * 20)
	
