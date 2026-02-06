"""
Factory for creating realistic test data
Simulates a real electronics shop with hundreds of products
"""
from decimal import Decimal
from apps.core.models import User, Shop
from apps.inventory.models import Category, Brand, Model, Product
from apps.agents.models import Agent


class TestDataFactory:
    """Generate realistic test data for electronics shop"""
    
    # Realistic Rwandan phone repair shop data
    CATEGORIES = [
        ("Screens & Displays", "LCD, OLED, and touch screens"),
        ("Batteries", "Original and compatible batteries"),
        ("Charging Ports", "USB-C, Lightning, Micro-USB ports"),
        ("Cameras", "Front and back camera modules"),
        ("Speakers & Microphones", "Audio components"),
        ("Flex Cables", "Power, volume, and connector cables"),
        ("Back Covers", "Phone back panels and housing"),
        ("SIM Trays", "SIM card holders"),
        ("Tools & Accessories", "Repair tools and supplies"),
    ]
    
    BRANDS = [
        "Samsung", "Apple", "Tecno", "Infinix", "Xiaomi", 
        "Oppo", "Vivo", "Huawei", "Nokia", "Itel"
    ]
    
    PHONE_MODELS = {
        "Samsung": ["Galaxy A54", "Galaxy S23", "Galaxy A14", "Galaxy M13"],
        "Apple": ["iPhone 13", "iPhone 14", "iPhone 12", "iPhone 11"],
        "Tecno": ["Camon 20", "Spark 10", "Pova 5", "Pop 7"],
        "Infinix": ["Note 30", "Hot 30", "Smart 7", "Zero 30"],
        "Xiaomi": ["Redmi Note 12", "Redmi 12", "Poco X5", "Mi 11"],
        "Oppo": ["A78", "A57", "Reno 8", "A17"],
    }
    
    @staticmethod
    def create_shop():
        """Create test shop"""
        return Shop.objects.create(
            name="Aguka Electronics Test Shop",
            owner_name="Test Owner",
            phone_number="+250788999000",
            license_key="TEST-SHOP-KEY",
            device_id="test-device-001",
            currency="RWF",
            timezone="Africa/Kigali"
        )
    
    @staticmethod
    def create_users():
        """Create owner and cashier users"""
        owner = User.objects.create(
            username="testowner",
            full_name="Test Owner",
            role=User.OWNER,
            is_active=True
        )
        owner.set_password("test123")
        owner.save()
        
        cashier = User.objects.create(
            username="testcashier",
            full_name="Test Cashier",
            role=User.CASHIER,
            is_active=True
        )
        cashier.set_password("test123")
        cashier.save()
        
        return owner, cashier
    
    @staticmethod
    def create_categories():
        """Create product categories"""
        categories = []
        for name, desc in TestDataFactory.CATEGORIES:
            cat = Category.objects.create(
                name=name,
                description=desc
            )
            categories.append(cat)
        return categories
    
    @staticmethod
    def create_brands_and_models():
        """Create brands and phone models"""
        brands_dict = {}
        models_dict = {}
        
        for brand_name in TestDataFactory.BRANDS:
            brand = Brand.objects.create(name=brand_name)
            brands_dict[brand_name] = brand
            
            if brand_name in TestDataFactory.PHONE_MODELS:
                models_dict[brand_name] = []
                for model_name in TestDataFactory.PHONE_MODELS[brand_name]:
                    model = Model.objects.create(
                        brand=brand,
                        name=model_name,
                        release_year=2023
                    )
                    models_dict[brand_name].append(model)
        
        return brands_dict, models_dict
    
    @staticmethod
    def create_realistic_inventory(owner, categories, brands_dict, models_dict):
        """Create hundreds of realistic products"""
        products = []
        sku_counter = 1000
        
        # Pricing ranges for different categories (in RWF)
        pricing = {
            "Screens & Displays": (45000, 180000),  # Cheap to premium
            "Batteries": (8000, 55000),
            "Charging Ports": (5000, 25000),
            "Cameras": (15000, 85000),
            "Speakers & Microphones": (3000, 15000),
        }
        
        for brand_name, models_list in models_dict.items():
            for model in models_list:
                # Create parts for each phone model
                for category in categories[:5]:  # Main categories
                    if category.name in pricing:
                        cost_min, cost_max = pricing[category.name]
                        
                        # Vary prices within range
                        cost = Decimal(str(cost_min))
                        selling = cost * Decimal("1.5")  # 50% markup
                        
                        sku = f"{brand_name[:3].upper()}-{model.name[:3].upper()}-{category.name[:3].upper()}-{sku_counter:04d}"
                        name = f"{model.name} {category.name.split()[0]}"
                        
                        # Realistic stock levels
                        if category.name == "Screens & Displays":
                            stock = 15  # Higher value items, lower stock
                        elif category.name == "Batteries":
                            stock = 50  # Fast movers, higher stock
                        else:
                            stock = 30  # Medium stock
                        
                        product = Product(
                            sku=sku,
                            name=name,
                            category=category,
                            brand=brands_dict[brand_name],
                            phone_model=model,
                            cost_price=cost,
                            selling_price=selling,
                            quantity_in_stock=stock,
                            reorder_level=5 if stock < 20 else 10,
                            created_by=owner
                        )
                        products.append(product)
                        sku_counter += 1
        
        Product.objects.bulk_create(products)
        return products
    
    @staticmethod
    def create_agents(owner, count=10):
        """Create field technician agents"""
        areas = ["Kigali CBD", "Nyabugogo", "Remera", "Kimironko", "Gikondo", 
                 "Nyamirambo", "Kicukiro", "Kanombe", "Kabuga", "Kimihurura"]
        
        agents = []
        for i in range(count):
            agent = Agent.objects.create(
                full_name=f"Agent {i+1}",
                phone_number=f"+25078800{i:04d}",
                business_name=f"Tech Repair {i+1}",
                area=areas[i % len(areas)],
                credit_limit=Decimal(str(300000 + (i * 50000))),
                is_active=True,
                created_by=owner
            )
            agents.append(agent)
        
        return agents
    
    @staticmethod
    def setup_full_test_shop():
        """Create complete realistic shop setup"""
        shop = TestDataFactory.create_shop()
        owner, cashier = TestDataFactory.create_users()
        categories = TestDataFactory.create_categories()
        brands, models = TestDataFactory.create_brands_and_models()
        products = TestDataFactory.create_realistic_inventory(owner, categories, brands, models)
        agents = TestDataFactory.create_agents(owner)
        
        return {
            'shop': shop,
            'owner': owner,
            'cashier': cashier,
            'categories': categories,
            'brands': brands,
            'models': models,
            'products': products,
            'agents': agents,
        }
