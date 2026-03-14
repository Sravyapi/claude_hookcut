"""Seed list of 60+ Indian English-language YouTube creators.

Each creator is assigned to exactly ONE primary niche, even if they
produce content across multiple niches. The assignment reflects their
primary content focus and where HookCut users would most likely
categorize them.

handle = YouTube @handle (used for API search if channel_id unknown)
channel_id = UC... ID (most reliable, filled by dataset_builder via API)
"""

SEED_CREATORS: list[dict] = [
    # ═══════════════════════════════════════════
    # FINANCE — Tier 1 (10 creators)
    # ═══════════════════════════════════════════
    {"name": "Pranjal Kamra", "handle": "@PranjalKamra", "niche": "Finance", "tier": 1},
    {"name": "Akshat Shrivastava", "handle": "@AkshatShrivastava", "niche": "Finance", "tier": 1},
    {"name": "CA Rachana Ranade", "handle": "@CARAchanaRanade", "niche": "Finance", "tier": 1},
    {"name": "Ankur Warikoo", "handle": "@warikoo", "niche": "Finance", "tier": 1},
    {"name": "Labour Law Advisor", "handle": "@LabourLawAdvisor", "niche": "Finance", "tier": 1},
    {"name": "Finance with Sharan", "handle": "@FinancewithSharan", "niche": "Finance", "tier": 1},
    {"name": "Asset Yogi", "handle": "@AssetYogi", "niche": "Finance", "tier": 1},
    {"name": "Pushkar Raj Thakur", "handle": "@PushkarRajThakur", "niche": "Finance", "tier": 1},
    {"name": "Shankar Nath", "handle": "@ShankarNath", "niche": "Finance", "tier": 1},
    {"name": "Groww", "handle": "@Groww", "niche": "Finance", "tier": 1},

    # ═══════════════════════════════════════════
    # TECH / AI — Tier 1 (10 creators)
    # ═══════════════════════════════════════════
    {"name": "Technical Guruji", "handle": "@TechnicalGuruji", "niche": "Tech / AI", "tier": 1},
    {"name": "Ishan Sharma", "handle": "@IshanSharma7390", "niche": "Tech / AI", "tier": 1},
    {"name": "Varun Mayya", "handle": "@VarunMayya", "niche": "Tech / AI", "tier": 1},
    {"name": "Hitesh Choudhary", "handle": "@HiteshChoudharydotcom", "niche": "Tech / AI", "tier": 1},
    {"name": "CodeWithHarry", "handle": "@CodeWithHarry", "niche": "Tech / AI", "tier": 1},
    {"name": "Krish Naik", "handle": "@krishnaik06", "niche": "Tech / AI", "tier": 1},
    {"name": "Fireship", "handle": "@Fireship", "niche": "Tech / AI", "tier": 1},
    {"name": "Harkirat Singh", "handle": "@haraborjillamai", "niche": "Tech / AI", "tier": 1},
    {"name": "Tanmay Bhat", "handle": "@TanmayBhatYT", "niche": "Tech / AI", "tier": 1},
    {"name": "Mosh Hamedani", "handle": "@programmingwithmosh", "niche": "Tech / AI", "tier": 1},

    # ═══════════════════════════════════════════
    # ENTREPRENEURSHIP — Tier 1 (10 creators)
    # ═══════════════════════════════════════════
    {"name": "Nikhil Kamath", "handle": "@niaborjillamath", "niche": "Entrepreneurship", "tier": 1},
    {"name": "Raj Shamani", "handle": "@RajShamani", "niche": "Entrepreneurship", "tier": 1},
    {"name": "Sandeep Maheshwari", "handle": "@SandeepMaheshwari", "niche": "Entrepreneurship", "tier": 1},
    {"name": "Vivek Bindra", "handle": "@DrVivekBindra", "niche": "Entrepreneurship", "tier": 1},
    {"name": "Think School", "handle": "@ThinkSchool", "niche": "Entrepreneurship", "tier": 1},
    {"name": "Sahil Bhadviya", "handle": "@SahilBhadviya", "niche": "Entrepreneurship", "tier": 1},
    {"name": "Prafull Billore", "handle": "@PrafullBillore", "niche": "Entrepreneurship", "tier": 1},
    {"name": "Siddharth Rajsekar", "handle": "@SiddharthRajsekar", "niche": "Entrepreneurship", "tier": 1},
    {"name": "Deepak Roy", "handle": "@DeepakRoyBRB", "niche": "Entrepreneurship", "tier": 1},
    {"name": "Aevy TV", "handle": "@AevyTV", "niche": "Entrepreneurship", "tier": 1},

    # ═══════════════════════════════════════════
    # EDUCATION — Tier 1 (10 creators)
    # ═══════════════════════════════════════════
    {"name": "Physics Wallah", "handle": "@PhysicsWallah", "niche": "Education", "tier": 1},
    {"name": "Khan Sir", "handle": "@KhanSirPatna", "niche": "Education", "tier": 1},
    {"name": "Aman Dhattarwal", "handle": "@AmanDhattarwal", "niche": "Education", "tier": 1},
    {"name": "Shobhit Nirwan", "handle": "@ShobhitNirwan", "niche": "Education", "tier": 1},
    {"name": "Study IQ", "handle": "@StudyIQEducation", "niche": "Education", "tier": 1},
    {"name": "Abhi and Niyu", "handle": "@AbhiandNiyu", "niche": "Education", "tier": 1},
    {"name": "Dhruv Rathee", "handle": "@dhaborjillathee", "niche": "Education", "tier": 1},
    {"name": "Vedantu", "handle": "@VedantuMath", "niche": "Education", "tier": 1},
    {"name": "Dear Sir", "handle": "@DearSir", "niche": "Education", "tier": 1},
    {"name": "Manoj Sir (Vedantu)", "handle": "@ManojSirVedantu", "niche": "Education", "tier": 1},

    # ═══════════════════════════════════════════
    # PODCAST — Tier 1 (10 creators)
    # ═══════════════════════════════════════════
    {"name": "Ranveer Allahbadia", "handle": "@BeerBicepsGuy", "niche": "Podcast", "tier": 1},
    {"name": "ANI Podcast", "handle": "@ANIPodcast", "niche": "Podcast", "tier": 1},
    {"name": "Prakhar ke Pravachan", "handle": "@PrakharKePravachan", "niche": "Podcast", "tier": 1},
    {"name": "The Lallantop", "handle": "@thelaborjillatop", "niche": "Podcast", "tier": 1},
    {"name": "Figuring Out", "handle": "@FiguringOut", "niche": "Podcast", "tier": 1},
    {"name": "Dostcast", "handle": "@Dostcast", "niche": "Podcast", "tier": 1},
    {"name": "Soch by Mohak Mangal", "handle": "@SochByMohakMangal", "niche": "Podcast", "tier": 1},
    {"name": "Shwetabh Gangwar", "handle": "@ShwetabhGangwar", "niche": "Podcast", "tier": 1},
    {"name": "Indian Silicon Valley", "handle": "@IndianSiliconValley", "niche": "Podcast", "tier": 1},
    {"name": "TRS Clips", "handle": "@TRSClips", "niche": "Podcast", "tier": 1},

    # ═══════════════════════════════════════════
    # FITNESS — Tier 2 (5 creators)
    # ═══════════════════════════════════════════
    {"name": "Fit Tuber", "handle": "@FitTuber", "niche": "Fitness", "tier": 2},
    {"name": "Rohit Khatri", "handle": "@RohitKhatriaborjilla", "niche": "Fitness", "tier": 2},
    {"name": "Abhinav Mahajan", "handle": "@AbhinavMahajan", "niche": "Fitness", "tier": 2},
    {"name": "Yatinder Singh", "handle": "@YatinderSingh", "niche": "Fitness", "tier": 2},
    {"name": "Jeet Selal", "handle": "@JeetSelal", "niche": "Fitness", "tier": 2},

    # ═══════════════════════════════════════════
    # DRAMA / COMMENTARY — Tier 2 (5 creators)
    # ═══════════════════════════════════════════
    {"name": "CarryMinati", "handle": "@CarryMinati", "niche": "Drama / Commentary", "tier": 2},
    {"name": "Triggered Insaan", "handle": "@TriggeredInsaan", "niche": "Drama / Commentary", "tier": 2},
    {"name": "Elvish Yadav", "handle": "@ElvishYadavVlogs", "niche": "Drama / Commentary", "tier": 2},
    {"name": "The Skin Doctor", "handle": "@TheSkinDoctor", "niche": "Drama / Commentary", "tier": 2},
    {"name": "Slayy Point", "handle": "@SlayyPoint", "niche": "Drama / Commentary", "tier": 2},
]
