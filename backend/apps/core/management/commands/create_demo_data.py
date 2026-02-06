"""
Management command to create demo/test data
"""
from django.core.management.base import BaseCommand
from apps.core.models import User
from apps.inventory.models import Brand, Category, Model, Product
from apps.agents.models import Agent


class Command(BaseCommand):
    help = 'Create demo data for testing'
    
    def handle(self, *args, **options):
        # Get owner user
        try:
            owner = User.objects.filter(role=User.OWNER).first()
            if not owner:
                self.stdout.write(self.style.ERROR('No owner found. Run setup_shop first.'))
                return
        except:
            self.stdout.write(self.style.ERROR('Run setup_shop first.'))
            return
        
        self.stdout.write('Creating demo data...\n')
        
        # Create categories
        categories_data = [
            {'name': 'Screens & Displays', 'description': 'LCD, OLED, and touchscreens'},
            {'name': 'Batteries', 'description': 'Phone batteries'},
            {'name': 'Charging Ports', 'description': 'USB-C, Lightning, Micro-USB ports'},
            {'name': 'Cameras', 'description': 'Front and back cameras'},
            {'name': 'Speakers & Microphones', 'description': 'Audio components'},
        ]
        
        categories = {}
        for cat_data in categories_data:
            cat, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            categories[cat.name] = cat
            if created:
                self.stdout.write(f'  ✓ Category: {cat.name}')
        
        # Create brands
        brands_data = ['Samsung', 'Apple', 'Tecno', 'Infinix', 'Xiaomi', 'Oppo']
        brands = {}
        for brand_name in brands_data:
            brand, created = Brand.objects.get_or_create(name=brand_name)
            brands[brand_name] = brand
            if created:
                self.stdout.write(f'  ✓ Brand: {brand_name}')
        
        # Create phone models
        models_data = [
            {'brand': 'Samsung', 'name': 'Galaxy A54', 'year': 2023},
            {'brand': 'Samsung', 'name': 'Galaxy S23', 'year': 2023},
            {'brand': 'Apple', 'name': 'iPhone 13', 'year': 2021},
            {'brand': 'Apple', 'name': 'iPhone 14', 'year': 2022},
            {'brand': 'Tecno', 'name': 'Camon 20', 'year': 2023},
            {'brand': 'Tecno', 'name': 'Spark 10', 'year': 2023},
            {'brand': 'Infinix', 'name': 'Note 30', 'year': 2023},
            {'brand': 'Infinix', 'name': 'Hot 30', 'year': 2023},
        ]
        
        phone_models = {}
        for model_data in models_data:
            model, created = Model.objects.get_or_create(
                brand=brands[model_data['brand']],
                name=model_data['name'],
                defaults={'release_year': model_data['year']}
            )
            phone_models[f"{model_data['brand']} {model_data['name']}"] = model
            if created:
                self.stdout.write(f'  ✓ Model: {model_data["brand"]} {model_data["name"]}')
        
        # Create products
        products_data = [
            # Samsung Galaxy A54 parts
            {'sku': 'SA54-LCD-001', 'name': 'Galaxy A54 LCD Screen', 'model': 'Samsung Galaxy A54', 'category': 'Screens & Displays', 'cost': 45000, 'price': 65000, 'stock': 15},
            {'sku': 'SA54-BAT-001', 'name': 'Galaxy A54 Battery', 'model': 'Samsung Galaxy A54', 'category': 'Batteries', 'cost': 15000, 'price': 25000, 'stock': 25},
            {'sku': 'SA54-CHG-001', 'name': 'Galaxy A54 Charging Port', 'model': 'Samsung Galaxy A54', 'category': 'Charging Ports', 'cost': 8000, 'price': 15000, 'stock': 30},
            
            # iPhone 13 parts
            {'sku': 'IP13-LCD-001', 'name': 'iPhone 13 OLED Screen', 'model': 'Apple iPhone 13', 'category': 'Screens & Displays', 'cost': 120000, 'price': 180000, 'stock': 8},
            {'sku': 'IP13-BAT-001', 'name': 'iPhone 13 Battery', 'model': 'Apple iPhone 13', 'category': 'Batteries', 'cost': 35000, 'price': 55000, 'stock': 12},
            {'sku': 'IP13-CAM-001', 'name': 'iPhone 13 Back Camera', 'model': 'Apple iPhone 13', 'category': 'Cameras', 'cost': 45000, 'price': 70000, 'stock': 6},
            
            # Tecno Camon 20 parts
            {'sku': 'TC20-LCD-001', 'name': 'Camon 20 LCD Screen', 'model': 'Tecno Camon 20', 'category': 'Screens & Displays', 'cost': 25000, 'price': 40000, 'stock': 20},
            {'sku': 'TC20-BAT-001', 'name': 'Camon 20 Battery', 'model': 'Tecno Camon 20', 'category': 'Batteries', 'cost': 8000, 'price': 15000, 'stock': 35},
            {'sku': 'TC20-CHG-001', 'name': 'Camon 20 Charging Port', 'model': 'Tecno Camon 20', 'category': 'Charging Ports', 'cost': 5000, 'price': 10000, 'stock': 40},
        ]
        
        for prod_data in products_data:
            model_key = prod_data['model']
            prod, created = Product.objects.get_or_create(
                sku=prod_data['sku'],
                defaults={
                    'name': prod_data['name'],
                    'category': categories[prod_data['category']],
                    'phone_model': phone_models[model_key],
                    'brand': phone_models[model_key].brand,
                    'cost_price': prod_data['cost'],
                    'selling_price': prod_data['price'],
                    'quantity_in_stock': prod_data['stock'],
                    'reorder_level': 5,
                    'created_by': owner
                }
            )
            if created:
                self.stdout.write(f'  ✓ Product: {prod.name} ({prod.sku})')
        
        # Create demo agents
        agents_data = [
            {'name': 'Jean Claude', 'phone': '+250788111222', 'area': 'Kigali CBD', 'credit': 500000},
            {'name': 'Marie Rose', 'phone': '+250788333444', 'area': 'Nyabugogo', 'credit': 300000},
            {'name': 'Patrick Tech', 'phone': '+250788555666', 'area': 'Remera', 'credit': 400000},
        ]
        
        for agent_data in agents_data:
            agent, created = Agent.objects.get_or_create(
                phone_number=agent_data['phone'],
                defaults={
                    'full_name': agent_data['name'],
                    'area': agent_data['area'],
                    'credit_limit': agent_data['credit'],
                    'is_active': True,
                    'created_by': owner
                }
            )
            if created:
                self.stdout.write(f'  ✓ Agent: {agent.full_name} ({agent.area})')
        
        self.stdout.write(self.style.SUCCESS('\n✓ Demo data created successfully!'))
        self.stdout.write('\nSummary:')
        self.stdout.write(f'  Categories: {Category.objects.count()}')
        self.stdout.write(f'  Brands: {Brand.objects.count()}')
        self.stdout.write(f'  Phone Models: {Model.objects.count()}')
        self.stdout.write(f'  Products: {Product.objects.count()}')
        self.stdout.write(f'  Agents: {Agent.objects.count()}')
