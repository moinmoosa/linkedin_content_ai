# LinkedIn Content AI

An automated content generation platform for LinkedIn, focusing on Business and Product Strategy topics.

## Features

- Automatic daily LinkedIn post generation
- Content focused on Business and Product Strategy
- OpenAI-powered content creation
- Scheduled posting at optimal times
- REST API endpoints for manual content generation
- Health check endpoint

## Setup

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables in `.env`:
```
OPENAI_API_KEY=your_openai_api_key_here
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
LINKEDIN_ACCESS_TOKEN=your_linkedin_access_token
```

4. Run the application:
```bash
python app.py
```

## API Endpoints

- `POST /generate`: Manually trigger content generation
- `GET /health`: Health check endpoint

## Content Generation

The platform generates content on various topics including:
- Business Strategy
- Product Strategy
- Market Analysis
- Innovation Management
- Strategic Planning
- Product Development
- Customer Experience
- Digital Transformation

Posts are automatically generated and scheduled for 9:00 AM daily.

## Next Steps

- Implement LinkedIn API integration
- Add content performance analytics
- Implement content customization options
- Add more topic categories
- Create a web interface for content management

## Note

Make sure to replace the placeholder API keys in the `.env` file with your actual credentials before running the application.
