AI-AVER-V4/
├── app/
│   ├── main.py             # FastAPI application
│   ├── templates/
│   │   └── index.html      # Your unified HTML frontend
│   └── static/             # For CSS, JS, images
├── src/
│   ├── metadata_analyzer.py # Your MetadataAnalyzer class
│   ├── prnu_processor.py    # New: For PRNU preprocessing (e.g., preprocess.py functions)
│   ├── prnu_model.py        # New: For PRNU model (e.g., generate_triplets.py, train.py functions)
│   ├── weather_validator.py # New: For historical weather validation
│   └── ai_integrations.py   # New: For AI calls (Gemini for narrative/KB enrichment)
├── database/
│   └── devices.json        # Your device knowledge base
├── data/
│   ├── raw/                # For uploaded training images (PRNU)
│   └── processed/          # For processed PRNU features, etc.
├── models/                 # For trained PRNU and other AI models
├── tests/                  # For unit tests
├── requirements.txt        # Python dependencies
├── README.md               # Project overview, setup, usage
└── .gitignore              # Files to ignore (e.g., .env, __pycache__, uploaded files)
