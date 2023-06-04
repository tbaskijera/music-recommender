import random

def getRandomCategory(sp):
    categories = sp.categories()
    random_category = random.choice(categories['categories']['items'])
    category_name = random_category['name']
    return category_name
