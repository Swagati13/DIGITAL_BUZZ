from django.core.management.base import BaseCommand
import pandas as pd
from enquiries.models import Enquiry

class Command(BaseCommand):
    help = "Load enquiry CSV data"

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **kwargs):
        df = pd.read_csv(kwargs['csv_file'])
        for _, row in df.iterrows():
            Enquiry.objects.create(
                name=row['name'],
                age=row['age'],
                income=row['income'],
                city=row['city'],
                property_type=row['property_type'],
                budget=row['budget'],
                followups=row['followups'],
                site_visited=row['site_visited'],
                booked=row['booked'],
            )
        self.stdout.write(self.style.SUCCESS("Data imported successfully"))
