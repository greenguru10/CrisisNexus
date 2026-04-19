"""
Dummy Data Generator
====================
Generates fake NGO survey reports and volunteer records for testing.

Usage:
    python -m app.generate_dummy_data

Requires a running PostgreSQL database configured via .env.
"""

import random
import logging
from faker import Faker
from database import SessionLocal, init_db
from models.need import Need, UrgencyLevel, NeedStatus
from models.volunteer import Volunteer
from services.nlp_service import extract_from_text
from services.priority_service import compute_priority_score
from utils.location_utils import geocode_location

logging.basicConfig(level=logging.INFO, format="%(asctime)s │ %(message)s")
logger = logging.getLogger(__name__)
fake = Faker()

# ── Templates for realistic survey reports ───────────────────────

REPORT_TEMPLATES = [
    "Urgent: {count} families in {city} need clean drinking water. Wells have dried up and children are falling sick.",
    "Emergency medical assistance needed in {city}. {count} people injured after flooding. Hospitals overwhelmed.",
    "Critical food shortage in {city}. {count} villagers have not eaten in 3 days. Rice and grain supplies exhausted.",
    "{count} people displaced in {city} after the earthquake. They need shelter and warm blankets immediately.",
    "Sanitation crisis in {city}. {count} residents have no access to toilets. Risk of cholera outbreak.",
    "Need warm clothing for {count} children in {city}. Winter temperatures dropping below zero.",
    "Education disrupted in {city}. {count} children need school supplies and temporary classrooms after cyclone damage.",
    "{count} families in {city} urgently need food rations and medical supplies. Situation is dire.",
    "Water purification tablets needed for {count} people in {city}. Contaminated water causing diarrhea.",
    "Medical camp needed in {city}. {count} individuals suffering from fever and respiratory infections.",
    "{count} refugees in {city} require shelter, food, and basic hygiene kits. Conditions are worsening.",
    "Moderate need: {count} people in {city} require supplementary nutrition packs for malnourished children.",
    "{count} villagers in {city} need access to a mobile health clinic. Nearest hospital is 50 km away.",
    "Fire destroyed homes in {city}. {count} families are now homeless and need emergency shelter.",
    "Flood relief needed in {city}. {count} people stranded. Food and rescue boats required immediately.",
]

CITIES = [
    ("Mumbai", 19.076, 72.8777),
    ("Delhi", 28.7041, 77.1025),
    ("Bangalore", 12.9716, 77.5946),
    ("Chennai", 13.0827, 80.2707),
    ("Kolkata", 22.5726, 88.3639),
    ("Hyderabad", 17.385, 78.4867),
    ("Pune", 18.5204, 73.8567),
    ("Kathmandu", 27.7172, 85.324),
    ("Dhaka", 23.8103, 90.4125),
    ("Colombo", 6.9271, 79.8612),
    ("Nairobi", 1.2921, 36.8219),
    ("Lagos", 6.5244, 3.3792),
    ("Jakarta", -6.2088, 106.8456),
    ("Manila", 14.5995, 120.9842),
    ("Karachi", 24.8607, 67.0011),
]

SKILL_POOL = [
    "medical", "first_aid", "nursing", "cooking", "food", "nutrition",
    "logistics", "driving", "construction", "carpentry", "plumbing",
    "water", "purification", "engineering", "teaching", "education",
    "counseling", "shelter", "distribution", "coordination",
    "sanitation", "hygiene", "cleaning", "textiles", "clothing",
]


def generate_reports(count: int = 75) -> list[Need]:
    """Generate fake survey reports, run them through NLP + priority engine."""
    needs = []
    for i in range(count):
        city_name, city_lat, city_lon = random.choice(CITIES)
        people_count = random.choice([50, 100, 150, 200, 300, 500, 800, 1000, 1500])
        template = random.choice(REPORT_TEMPLATES)
        raw_text = template.format(count=people_count, city=city_name)

        # NLP extraction
        extracted = extract_from_text(raw_text)
        lat, lon = geocode_location(extracted.get("location"))

        # Use template coordinates as fallback
        lat = lat or city_lat + random.uniform(-0.05, 0.05)
        lon = lon or city_lon + random.uniform(-0.05, 0.05)

        # Priority score
        priority = compute_priority_score(
            urgency=extracted["urgency"],
            people_affected=extracted["people_affected"],
            category=extracted["category"],
        )

        # Some completed / assigned statuses for variety
        status = random.choices(
            [NeedStatus.PENDING, NeedStatus.ASSIGNED, NeedStatus.COMPLETED],
            weights=[0.55, 0.3, 0.15],
        )[0]

        need = Need(
            raw_text=raw_text,
            category=extracted["category"],
            urgency=UrgencyLevel(extracted["urgency"]),
            people_affected=extracted["people_affected"],
            location=extracted.get("location") or city_name,
            latitude=lat,
            longitude=lon,
            priority_score=priority,
            status=status,
        )
        needs.append(need)

    return needs


def generate_volunteers(count: int = 35) -> list[Volunteer]:
    """Generate fake volunteer records."""
    volunteers = []
    for i in range(count):
        city_name, city_lat, city_lon = random.choice(CITIES)
        num_skills = random.randint(2, 5)
        skills = random.sample(SKILL_POOL, num_skills)

        volunteer = Volunteer(
            name=fake.name(),
            skills=skills,
            location=city_name,
            latitude=city_lat + random.uniform(-0.1, 0.1),
            longitude=city_lon + random.uniform(-0.1, 0.1),
            availability=random.choices([True, False], weights=[0.75, 0.25])[0],
            rating=round(random.uniform(2.5, 5.0), 1),
        )
        volunteers.append(volunteer)

    return volunteers


def main():
    """Generate and insert dummy data into the database."""
    logger.info("Initialising database tables...")
    init_db()

    db = SessionLocal()
    try:
        # Clear existing data
        db.query(Need).delete()
        db.query(Volunteer).delete()
        db.commit()
        logger.info("Cleared existing data.")

        # Generate needs
        needs = generate_reports(75)
        db.add_all(needs)
        db.commit()
        logger.info("✅ Inserted %d needs.", len(needs))

        # Generate volunteers
        volunteers = generate_volunteers(35)
        db.add_all(volunteers)
        db.commit()
        logger.info("✅ Inserted %d volunteers.", len(volunteers))

        # Summary
        logger.info("═" * 50)
        logger.info("DUMMY DATA GENERATION COMPLETE")
        logger.info("  Needs:      %d", len(needs))
        logger.info("  Volunteers: %d", len(volunteers))
        logger.info("═" * 50)

    except Exception as e:
        db.rollback()
        logger.error("Error generating dummy data: %s", e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
