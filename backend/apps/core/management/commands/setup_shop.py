"""
Management command to set up initial shop and owner account
"""
from django.core.management.base import BaseCommand
from apps.core.models import Shop, User
import secrets


class Command(BaseCommand):
    help = 'Set up initial shop configuration and owner account'
    
    def add_arguments(self, parser):
        parser.add_argument('--shop-name', type=str, default='Demo Electronics Shop')
        parser.add_argument('--owner-name', type=str, default='Shop Owner')
        parser.add_argument('--phone', type=str, default='+250788123456')
        parser.add_argument('--username', type=str, default='owner')
        parser.add_argument('--password', type=str, default='owner123')
    
    def handle(self, *args, **options):
        # Check if shop already exists
        if Shop.objects.exists():
            self.stdout.write(self.style.WARNING('Shop already configured!'))
            shop = Shop.objects.first()
            self.stdout.write(f'Shop: {shop.name}')
            return
        
        # Create shop
        shop = Shop.objects.create(
            name=options['shop_name'],
            owner_name=options['owner_name'],
            phone_number=options['phone'],
            license_key=f'EROM-DEMO-{secrets.token_hex(4).upper()}',
            device_id=secrets.token_hex(16),
            currency='RWF',
            timezone='Africa/Kigali',
            is_active=True
        )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Shop created: {shop.name}'))
        self.stdout.write(f'  License Key: {shop.license_key}')
        
        # Create owner account
        owner = User.objects.create(
            username=options['username'],
            full_name=options['owner_name'],
            role=User.OWNER,
            is_active=True
        )
        owner.set_password(options['password'])
        owner.save()
        
        self.stdout.write(self.style.SUCCESS(f'✓ Owner account created'))
        self.stdout.write(f'  Username: {owner.username}')
        self.stdout.write(f'  Password: {options["password"]}')
        self.stdout.write(f'  Role: {owner.role}')
        
        self.stdout.write(self.style.SUCCESS('\n✓ Setup complete! You can now login.'))
