# -*- coding: utf-8 -*-
"""Seed list of 60 Hindi/Hinglish Indian YouTube creators for Iteration 2.

These were the original creators removed from the English iteration because
their primary content language is Hindi or Hinglish. Organized for the
Hindi evaluation dataset.

language:
  - "Hindi"    = primarily Hindi
  - "Hinglish" = Hindi-English mix (common in Indian YouTube)

359 transcripts from these creators are preserved in transcripts_hindi/
"""

HINDI_SEED_CREATORS: list[dict] = [
    # =============================================
    # FINANCE - Tier 1 (10 creators)
    # =============================================
    {"name": "Pranjal Kamra", "handle": "@PranjalKamra", "niche": "Finance", "tier": 1, "language": "Hinglish"},
    {"name": "CA Rachana Ranade", "handle": "@CARAchanaRanade", "niche": "Finance", "tier": 1, "language": "Hinglish"},
    {"name": "Ankur Warikoo", "handle": "@warikoo", "niche": "Finance", "tier": 1, "language": "Hinglish"},
    {"name": "Labour Law Advisor", "handle": "@LabourLawAdvisor", "niche": "Finance", "tier": 1, "language": "Hindi"},
    {"name": "Pushkar Raj Thakur", "handle": "@PushkarRajThakur", "niche": "Finance", "tier": 1, "language": "Hindi"},
    {"name": "Groww", "handle": "@Groww", "niche": "Finance", "tier": 1, "language": "Hinglish"},
    {"name": "Vivek Bindra", "handle": "@DrVivekBindra", "niche": "Finance", "tier": 1, "language": "Hindi"},
    {"name": "Sanjay Seth Finance", "handle": "@SanjaySethFinance", "niche": "Finance", "tier": 1, "language": "Hindi"},
    {"name": "Trading Chanakya", "handle": "@TradingChanakya", "niche": "Finance", "tier": 1, "language": "Hindi"},
    {"name": "Fin Baba", "handle": "@FinBaba", "niche": "Finance", "tier": 1, "language": "Hindi"},

    # =============================================
    # TECH / AI - Tier 1 (10 creators)
    # =============================================
    {"name": "Technical Guruji", "handle": "@TechnicalGuruji", "niche": "Tech / AI", "tier": 1, "language": "Hindi"},
    {"name": "CodeWithHarry", "handle": "@CodeWithHarry", "niche": "Tech / AI", "tier": 1, "language": "Hinglish"},
    {"name": "Tanmay Bhat", "handle": "@TanmayBhatYT", "niche": "Tech / AI", "tier": 1, "language": "Hinglish"},
    {"name": "Technical Sagar", "handle": "@TechnicalSagar", "niche": "Tech / AI", "tier": 1, "language": "Hindi"},
    {"name": "Geeky Ranjit", "handle": "@GeekyRanjit", "niche": "Tech / AI", "tier": 1, "language": "Hinglish"},
    {"name": "Tech Burner", "handle": "@TechBurner", "niche": "Tech / AI", "tier": 1, "language": "Hindi"},
    {"name": "Trakin Tech", "handle": "@TrakinTech", "niche": "Tech / AI", "tier": 1, "language": "Hindi"},
    {"name": "Manoj Dey", "handle": "@ManojDey", "niche": "Tech / AI", "tier": 1, "language": "Hindi"},
    {"name": "Crazy XYZ", "handle": "@CrazyXYZ", "niche": "Tech / AI", "tier": 1, "language": "Hindi"},
    {"name": "Tech With Atul", "handle": "@TechWithAtul", "niche": "Tech / AI", "tier": 1, "language": "Hindi"},

    # =============================================
    # ENTREPRENEURSHIP - Tier 1 (10 creators)
    # =============================================
    {"name": "Sandeep Maheshwari", "handle": "@SandeepMaheshwari", "niche": "Entrepreneurship", "tier": 1, "language": "Hindi"},
    {"name": "Raj Shamani", "handle": "@RajShamani", "niche": "Entrepreneurship", "tier": 1, "language": "Hinglish"},
    {"name": "Prafull Billore", "handle": "@PrafullBillore", "niche": "Entrepreneurship", "tier": 1, "language": "Hindi"},
    {"name": "Deepak Roy", "handle": "@DeepakRoyBRB", "niche": "Entrepreneurship", "tier": 1, "language": "Hinglish"},
    {"name": "Him eesh Madaan", "handle": "@HimEeshMadaan", "niche": "Entrepreneurship", "tier": 1, "language": "Hindi"},
    {"name": "Sonu Sharma", "handle": "@SonuSharma", "niche": "Entrepreneurship", "tier": 1, "language": "Hindi"},
    {"name": "Snax Gaming", "handle": "@SnaxGaming", "niche": "Entrepreneurship", "tier": 1, "language": "Hindi"},
    {"name": "Satish K Videos", "handle": "@SatishKVideos", "niche": "Entrepreneurship", "tier": 1, "language": "Hindi"},
    {"name": "Lakshay Chaudhary", "handle": "@LakshayChaudhary", "niche": "Entrepreneurship", "tier": 1, "language": "Hindi"},
    {"name": "Amit Bhadana", "handle": "@AmitBhadana", "niche": "Entrepreneurship", "tier": 1, "language": "Hindi"},

    # =============================================
    # EDUCATION - Tier 1 (10 creators)
    # =============================================
    {"name": "Physics Wallah", "handle": "@PhysicsWallah", "niche": "Education", "tier": 1, "language": "Hinglish"},
    {"name": "Khan Sir", "handle": "@KhanSirPatna", "niche": "Education", "tier": 1, "language": "Hindi"},
    {"name": "Aman Dhattarwal", "handle": "@AmanDhattarwal", "niche": "Education", "tier": 1, "language": "Hinglish"},
    {"name": "Shobhit Nirwan", "handle": "@ShobhitNirwan", "niche": "Education", "tier": 1, "language": "Hinglish"},
    {"name": "Study IQ", "handle": "@StudyIQEducation", "niche": "Education", "tier": 1, "language": "Hindi"},
    {"name": "Vedantu", "handle": "@VedantuMath", "niche": "Education", "tier": 1, "language": "Hinglish"},
    {"name": "Dear Sir", "handle": "@DearSir", "niche": "Education", "tier": 1, "language": "Hindi"},
    {"name": "Manoj Sir (Vedantu)", "handle": "@ManojSirVedantu", "niche": "Education", "tier": 1, "language": "Hindi"},
    {"name": "PW Mohit Tyagi", "handle": "@PWMohitTyagi", "niche": "Education", "tier": 1, "language": "Hindi"},
    {"name": "Unacademy", "handle": "@Unacademy", "niche": "Education", "tier": 1, "language": "Hinglish"},

    # =============================================
    # PODCAST - Tier 1 (10 creators)
    # =============================================
    {"name": "Ranveer Allahbadia", "handle": "@BeerBicepsGuy", "niche": "Podcast", "tier": 1, "language": "Hinglish"},
    {"name": "ANI Podcast", "handle": "@ANIPodcast", "niche": "Podcast", "tier": 1, "language": "Hinglish"},
    {"name": "Prakhar ke Pravachan", "handle": "@PrakharKePravachan", "niche": "Podcast", "tier": 1, "language": "Hindi"},
    {"name": "The Lallantop", "handle": "@thelallantop", "niche": "Podcast", "tier": 1, "language": "Hindi"},
    {"name": "Figuring Out", "handle": "@FiguringOut", "niche": "Podcast", "tier": 1, "language": "Hinglish"},
    {"name": "Dostcast", "handle": "@Dostcast", "niche": "Podcast", "tier": 1, "language": "Hinglish"},
    {"name": "Shwetabh Gangwar", "handle": "@ShwetabhGangwar", "niche": "Podcast", "tier": 1, "language": "Hinglish"},
    {"name": "TRS Clips", "handle": "@TRSClips", "niche": "Podcast", "tier": 1, "language": "Hinglish"},
    {"name": "Aaj Tak", "handle": "@aaborjillatak", "niche": "Podcast", "tier": 1, "language": "Hindi"},
    {"name": "NDTV India", "handle": "@NDTVIndia", "niche": "Podcast", "tier": 1, "language": "Hindi"},

    # =============================================
    # FITNESS - Tier 2 (5 creators)
    # =============================================
    {"name": "Fit Tuber", "handle": "@FitTuber", "niche": "Fitness", "tier": 2, "language": "Hinglish"},
    {"name": "Rohit Khatri", "handle": "@RohitKhatriaborjilla", "niche": "Fitness", "tier": 2, "language": "Hindi"},
    {"name": "Abhinav Mahajan", "handle": "@AbhinavMahajan", "niche": "Fitness", "tier": 2, "language": "Hinglish"},
    {"name": "Yatinder Singh", "handle": "@YatinderSingh", "niche": "Fitness", "tier": 2, "language": "Hindi"},
    {"name": "Jeet Selal", "handle": "@JeetSelal", "niche": "Fitness", "tier": 2, "language": "Hindi"},

    # =============================================
    # DRAMA / COMMENTARY - Tier 2 (5 creators)
    # =============================================
    {"name": "Triggered Insaan", "handle": "@TriggeredInsaan", "niche": "Drama / Commentary", "tier": 2, "language": "Hindi"},
    {"name": "Elvish Yadav", "handle": "@ElvishYadavVlogs", "niche": "Drama / Commentary", "tier": 2, "language": "Hindi"},
    {"name": "The Skin Doctor", "handle": "@TheSkinDoctor", "niche": "Drama / Commentary", "tier": 2, "language": "Hindi"},
    {"name": "Slayy Point", "handle": "@SlayyPoint", "niche": "Drama / Commentary", "tier": 2, "language": "Hinglish"},
    {"name": "Ashish Chanchlani", "handle": "@AshishChanchlaniVines", "niche": "Drama / Commentary", "tier": 2, "language": "Hindi"},
]
