"""Generate sample data for app_portfolio table."""
import csv
import random
from datetime import datetime, timedelta

# App name templates
APP_NAMES = [
    "Paint", "Countdown", "Calculator", "Notes", "Weather", "Music", "Video",
    "Photo", "Calendar", "Mail", "Chat", "Map", "News", "Shop", "Game",
    "Fitness", "Health", "Finance", "Travel", "Food", "Social", "Education",
    "Productivity", "Entertainment", "Utility"
]

PLATFORMS = ['iOS', 'Android']

COUNTRIES = [
    'United States', 'United Kingdom', 'Germany', 'France', 'Italy', 'Spain',
    'Canada', 'Australia', 'Japan', 'South Korea', 'Brazil', 'India',
    'Mexico', 'Netherlands', 'Sweden'
]


def generate_app_name(platform: str) -> str:
    """Generate realistic app name."""
    base_name = random.choice(APP_NAMES)
    return f"{base_name} for {platform}"


def generate_date() -> str:
    """Generate random date within last 12 months."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    random_date = start_date + timedelta(days=random.randint(0, 365))
    return random_date.strftime('%Y-%m-%d')


def generate_revenue() -> float:
    """Generate realistic revenue (0-10000)."""
    return round(random.uniform(0, 10000), 2)


def generate_installs() -> int:
    """Generate realistic install count (0-100000)."""
    return random.randint(0, 100000)


def generate_ua_cost() -> float:
    """Generate realistic UA cost (0-5000)."""
    return round(random.uniform(0, 5000), 2)


def generate_sample_data(num_records: int = 50) -> list:
    """Generate sample data records."""
    records = []
    for i in range(num_records):
        platform = random.choice(PLATFORMS)
        record = {
            'app_name': generate_app_name(platform),
            'platform': platform,
            'date': generate_date(),
            'country': random.choice(COUNTRIES),
            'installs': generate_installs(),
            'in_app_revenue': generate_revenue(),
            'ads_revenue': generate_revenue(),
            'ua_cost': generate_ua_cost()
        }
        records.append(record)
    return records


def write_csv(filename: str, records: list):
    """Write records to CSV file."""
    if not records:
        return
    
    fieldnames = [
        'app_name', 'platform', 'date', 'country', 'installs',
        'in_app_revenue', 'ads_revenue', 'ua_cost'
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    print(f"Generated {len(records)} records in {filename}")


if __name__ == '__main__':
    records = generate_sample_data(50)
    write_csv('sample_data.csv', records)

