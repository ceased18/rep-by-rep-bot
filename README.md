# Rep by Rep - Ramadan Bot

A Discord bot designed to support bodybuilders and fitness enthusiasts during Ramadan, providing personalized nutrition and workout guidance.

## Features

### 1. Personalized Meal Plans (`/mealplan`)
- Generates customized meal plans based on user metrics and goals
- Includes detailed macro and micronutrient information
- Provides timing recommendations for Suhoor, Iftar, and Post-Taraweeh meals
- Exports professional PDF reports with nutritional analysis

### 2. RIFT & TAPS Methodology (`/rift_taps`)
- Explains the RIFT & TAPS training methodology for Ramadan
- Provides structured guidance for training during fasting
- Offers personalized advice through interactive chat

### 3. Ask Questions (`/ask`)
- Interactive Q&A about bodybuilding during Ramadan
- Access to comprehensive fitness and nutrition knowledge
- Real-time responses to training and diet questions

### 4. Daily Check-ins
- Automated daily progress tracking
- Monitors hydration, meal timing, and workout completion
- Community support through reactions and responses

## Technical Features
- Integration with USDA FoodData Central API for accurate macro information
- Open Food Facts API integration for detailed micronutrient data
- OpenAI Assistant API for intelligent interactions
- Professional PDF generation for meal plans

## Setup
1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Set up environment variables:
```
DISCORD_TOKEN=your_discord_bot_token
OPENAI_API_KEY=your_openai_api_key
USDA_API_KEY=your_usda_api_key
ASSISTANT_ID=your_openai_assistant_id
GUIDED_MEMBERS_ROLE_ID=your_discord_role_id
CHECK_IN_CHANNEL_ID=your_discord_channel_id
APPLICATION_ID=your_discord_application_id
```

## Bot Commands
- `/help` - Show available commands and usage information
- `/rift_taps` - Learn about the RIFT & TAPS methodology
- `/mealplan` - Get a personalized Ramadan meal plan
- `/ask <question>` - Ask questions about bodybuilding during Ramadan

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments
- USDA FoodData Central for nutritional data
- Open Food Facts for micronutrient information
- OpenAI for intelligent assistance
- Discord.py for bot framework
