from typing import Dict, List
import random

class ContentTemplates:
    def __init__(self):
        self.pivot_templates = [
            {
                "title": "Strategic Pivot Success: {company_name}",
                "structure": [
                    "🔄 The Pivot Point: {pivot_description}",
                    "🎯 Original Business: {original_business}",
                    "💡 The Realization: {realization}",
                    "🚀 The Transformation: {transformation}",
                    "📈 The Results: {results}",
                    "🔑 Key Lessons:\n{lessons}",
                    "\n#BusinessPivot #StrategicThinking #BusinessTransformation"
                ]
            },
            {
                "title": "From {original_industry} to {new_industry}: {company_name}'s Bold Pivot",
                "structure": [
                    "Before: {original_state}",
                    "Catalyst: {pivot_trigger}",
                    "The Pivot Strategy: {strategy}",
                    "Challenges Overcome: {challenges}",
                    "Current Success: {current_state}",
                    "Leadership Insights: {leadership_lessons}",
                    "\n#BusinessStrategy #Innovation #Leadership"
                ]
            }
        ]
        
        self.success_templates = [
            {
                "title": "{company_name}'s Path to Success",
                "structure": [
                    "💫 The Vision: {vision}",
                    "🎯 The Strategy: {strategy}",
                    "💪 The Execution: {execution}",
                    "📈 The Results: {results}",
                    "🔑 Success Factors: {success_factors}",
                    "\n#BusinessSuccess #Entrepreneurship #Growth"
                ]
            }
        ]
        
        self.innovation_templates = [
            {
                "title": "Innovation Spotlight: {company_name}",
                "structure": [
                    "🔍 The Problem: {problem}",
                    "💡 The Innovation: {innovation}",
                    "🚀 Implementation: {implementation}",
                    "🌟 Market Impact: {impact}",
                    "🔮 Future Implications: {future}",
                    "\n#Innovation #Technology #Future"
                ]
            }
        ]
        
        self.aerospace_templates = [
            {
                "title": "Aerospace Innovation: {company_name}",
                "structure": [
                    "🚀 Groundbreaking Achievement: {achievement}",
                    "🔬 Technical Context: {technical_context}",
                    "💡 Innovation Process: {innovation_process}",
                    "📈 Industry Impact: {industry_impact}",
                    "🔮 Future Implications: {future_implications}",
                    "📊 Validation: {validation}",
                    "🔑 Takeaway: {takeaway}",
                    "\n#Aerospace #Innovation #Technology"
                ]
            }
        ]
        
        self.templates = {
            'success': {
                'structure': {
                    'hook': 'Start with an attention-grabbing fact or question',
                    'context': 'Provide background and setup',
                    'insight': 'Share unique perspective or learning',
                    'evidence': 'Support with data or examples',
                    'takeaway': 'End with actionable insight or question'
                }
            },
            'pivot': {
                'structure': {
                    'hook': 'Start with the challenge or problem',
                    'context': 'Explain the market situation',
                    'insight': 'Share the pivot decision and rationale',
                    'evidence': 'Show the results and impact',
                    'takeaway': 'End with lessons learned'
                }
            },
            'innovation': {
                'structure': {
                    'hook': 'Start with a breakthrough moment or achievement',
                    'context': 'Explain the technical challenge',
                    'insight': 'Share the innovative solution',
                    'evidence': 'Show the impact and results',
                    'takeaway': 'End with future implications'
                }
            },
            'aerospace': {
                'structure': {
                    'hook': 'Start with a groundbreaking aerospace achievement',
                    'technical_context': 'Explain the engineering challenges and physics involved',
                    'innovation_process': 'Detail the R&D journey and breakthroughs',
                    'industry_impact': 'Show how it changed aerospace/defense dynamics',
                    'future_implications': 'Discuss implications for future technology',
                    'validation': 'Share test results and performance metrics',
                    'takeaway': 'End with industry-wide implications'
                },
                'technical_elements': {
                    'physics': ['aerodynamics', 'propulsion', 'materials science'],
                    'engineering': ['systems integration', 'avionics', 'structural design'],
                    'testing': ['wind tunnel', 'flight testing', 'simulation'],
                    'metrics': ['thrust-to-weight ratio', 'range', 'payload capacity']
                },
                'industry_aspects': {
                    'market': ['defense contracts', 'commercial aviation', 'space exploration'],
                    'competition': ['market share', 'technological edge', 'innovation rate'],
                    'regulations': ['safety standards', 'export controls', 'certification'],
                    'partnerships': ['suppliers', 'research institutions', 'government agencies']
                }
            }
        }
    
    def get_pivot_template(self) -> Dict:
        """Get a random pivot story template"""
        return random.choice(self.pivot_templates)

    def get_success_template(self) -> Dict:
        """Get a random success story template"""
        return random.choice(self.success_templates)

    def get_innovation_template(self) -> Dict:
        """Get template for innovation stories"""
        return {
            'structure': {
                'hook': 'Start with a surprising innovation milestone',
                'context': 'Explain the industry challenge being solved',
                'innovation': 'Detail the innovative solution and technology',
                'behind_scenes': 'Share internal development challenges',
                'impact': 'Show market and industry impact',
                'validation': 'Share metrics and external validation',
                'future': 'Discuss future implications',
                'engagement': 'End with thought-provoking questions'
            },
            'requirements': {
                'authenticity': {
                    'specific_dates': True,
                    'real_numbers': True,
                    'named_sources': True,
                    'direct_quotes': True,
                    'verifiable_facts': True
                },
                'insights': {
                    'behind_scenes': True,
                    'counter_intuitive': True,
                    'industry_specific': True,
                    'decision_rationale': True,
                    'failure_lessons': True
                }
            }
        }

    def get_aerospace_template(self) -> str:
        """Get a template for an aerospace story"""
        return """
Generate an engaging LinkedIn post about {company_name} that focuses on aerospace innovation and technological breakthroughs. 
The post should follow this structure:

1. Opening Hook (1-2 sentences)
- Start with a compelling fact about the company's aerospace journey
- Include specific dates and numerical data

2. Technical Deep-Dive (2-3 sentences)
- Focus on a specific aerospace program or technology
- REQUIRED: Include detailed behind-the-scenes engineering challenges
- REQUIRED: Explain specific technical decisions made during development

3. Innovation Process (2-3 sentences)
- REQUIRED: Name specific engineers or leaders involved
- REQUIRED: Include direct quotes about decision-making processes
- REQUIRED: Discuss alternative approaches that were considered and why they were rejected

4. Industry Impact (2-3 sentences)
- Discuss how this innovation changed industry standards
- Include specific market data or performance metrics
- Reference independent validation sources (analysts, industry reports)

5. Future Implications (1-2 sentences)
- Pose thought-provoking questions about future developments
- Reference ongoing research or development programs

6. Validation (1 sentence)
- Include a specific, verifiable fact from a reputable source

7. Key Takeaway (1-2 sentences)
- Synthesize the main lessons learned
- Focus on unexpected insights or counter-intuitive findings

8. Engagement Hook
- Ask 2-3 thought-provoking questions to encourage discussion
- Make questions relevant to both aerospace and general business audience

9. Hashtags (4-5 relevant tags)

REQUIRED ELEMENTS:
- At least 2 specific dates
- At least 2 numerical facts
- At least 2 named sources (engineers, executives, or experts)
- At least 2 direct quotes about decision-making
- At least 2 specific technical details
- At least 2 behind-the-scenes challenges
- At least 2 alternative approaches that were considered
- At least 1 independent validation source

Format with appropriate emojis and spacing for LinkedIn.
"""

    def format_template(self, template: Dict, data: Dict) -> str:
        """Format a template with actual data"""
        try:
            # Format title
            formatted_title = template["title"].format(**data)
            
            # Format each section of the structure
            formatted_sections = []
            for section in template["structure"]:
                try:
                    formatted_sections.append(section.format(**data))
                except KeyError as e:
                    # If a key is missing, use a placeholder
                    missing_key = str(e).strip("'")
                    formatted_sections.append(section.format(**{
                        **data,
                        missing_key: f"[{missing_key}]"
                    }))
            
            # Combine all sections
            return f"{formatted_title}\n\n" + "\n".join(formatted_sections)
        except Exception as e:
            return f"Error formatting template: {str(e)}"

    def generate_multiple_variations(self, template: Dict, data: Dict, num_variations: int = 3) -> List[str]:
        """Generate multiple variations of the same story"""
        variations = []
        base_content = self.format_template(template, data)
        
        # Generate variations by adding different perspectives or focuses
        perspectives = [
            "leadership perspective",
            "market impact focus",
            "innovation angle",
            "cultural transformation aspect",
            "customer-centric view"
        ]
        
        variations.append(base_content)  # Add the base version
        
        for i in range(num_variations - 1):
            perspective = perspectives[i % len(perspectives)]
            variation_data = {
                **data,
                "perspective": perspective,
                # Add some variety to the key sections
                "lessons": data.get("lessons", "") + f"\n(From a {perspective})",
                "impact": data.get("impact", "") + f"\n(Considering {perspective})"
            }
            variations.append(self.format_template(template, variation_data))
        
        return variations
