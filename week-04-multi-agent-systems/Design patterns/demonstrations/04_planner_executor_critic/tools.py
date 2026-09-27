"""Mock travel research tools for Flight, Hotel, and Activity specialists."""

import json
from typing import Dict, Any

FLIGHT_CATALOG = {
    "tokyo": {
        "premium": {"carrier": "ANA", "price_usd": 1850.0, "route": "Non-stop SFO->HND", "details": "Lie-flat Premium Economy"},
        "standard": {"carrier": "United Airlines", "price_usd": 1200.0, "route": "1 stop SFO->NRT", "details": "Standard Economy with checked bags"},
        "budget": {"carrier": "Zipair", "price_usd": 750.0, "route": "Non-stop SJC->NRT", "details": "Low-cost carrier, carry-on only"}
    },
    "paris": {
        "premium": {"carrier": "Air France", "price_usd": 1600.0, "route": "Non-stop JFK->CDG", "details": "Premium Economy"},
        "standard": {"carrier": "Delta", "price_usd": 950.0, "route": "1 stop BOS->CDG", "details": "Standard Economy"},
        "budget": {"carrier": "French Bee", "price_usd": 620.0, "route": "Non-stop EWR->ORY", "details": "Basic Economy"}
    }
}

HOTEL_CATALOG = {
    "tokyo": {
        "luxury": {"name": "Park Hyatt Tokyo (Shinjuku)", "price_per_night_usd": 480.0, "rating": "5-Star"},
        "boutique": {"name": "Hotel Gracery Shinjuku", "price_per_night_usd": 210.0, "rating": "4-Star Modern"},
        "budget": {"name": "Sotetsu Fresa Inn (Ginza)", "price_per_night_usd": 120.0, "rating": "3-Star Business Hotel"}
    },
    "paris": {
        "luxury": {"name": "Le Meurice", "price_per_night_usd": 650.0, "rating": "5-Star Palace"},
        "boutique": {"name": "Hôtel Fabric (Oberkampf)", "price_per_night_usd": 230.0, "rating": "4-Star Boutique"},
        "budget": {"name": "Ibis Styles Paris Gare de Lyon", "price_per_night_usd": 130.0, "rating": "3-Star Clean"}
    }
}

ACTIVITY_CATALOG = {
    "tokyo": {
        "deluxe": {"package": "Private Guided Mt. Fuji Tour + Sumo Tournament Ringside + TeamLab Planets", "total_cost_usd": 650.0},
        "standard": {"package": "TeamLab Planets + Tsukiji Market Tour + Shibuya Sky + 7-Day Tokyo Metro Pass", "total_cost_usd": 280.0},
        "budget": {"package": "Free Meiji Shrine + Shibuya Crossing + Senso-ji Temple + 72hr Metro Subway Pass", "total_cost_usd": 95.0}
    },
    "paris": {
        "deluxe": {"package": "Louvre Private Guided Tour + Seine Dinner Cruise + Versailles VIP Access", "total_cost_usd": 550.0},
        "standard": {"package": "Louvre Timed Entry + Eiffel Tower Summit + 5-Day Navigo Metro Pass", "total_cost_usd": 240.0},
        "budget": {"package": "Montmartre Walking Tour + Latin Quarter + Notre-Dame exterior + Metro T+ tickets", "total_cost_usd": 85.0}
    }
}


def search_flight_options(destination: str, tier: str = "standard") -> Dict[str, Any]:
    dest_key = destination.strip().lower()
    city_data = FLIGHT_CATALOG.get(dest_key, FLIGHT_CATALOG["tokyo"])
    return city_data.get(tier, city_data["standard"])


def search_hotel_options(destination: str, nights: int = 6, tier: str = "boutique") -> Dict[str, Any]:
    dest_key = destination.strip().lower()
    city_data = HOTEL_CATALOG.get(dest_key, HOTEL_CATALOG["tokyo"])
    option = city_data.get(tier, city_data["boutique"])
    total = round(option["price_per_night_usd"] * nights, 2)
    return {
        **option,
        "nights": nights,
        "total_cost_usd": total
    }


def search_activity_options(destination: str, tier: str = "standard") -> Dict[str, Any]:
    dest_key = destination.strip().lower()
    city_data = ACTIVITY_CATALOG.get(dest_key, ACTIVITY_CATALOG["tokyo"])
    return city_data.get(tier, city_data["standard"])
