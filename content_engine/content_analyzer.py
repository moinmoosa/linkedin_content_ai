import json
import re
from typing import Dict, List, Optional
from collections import defaultdict
import numpy as np
from pathlib import Path

class ContentAnalyzer:
    def __init__(self):
        self.examples = []
        self.patterns = defaultdict(list)
        self.templates = defaultdict(list)
        self.industry_keywords = defaultdict(set)
        self.story_structures = defaultdict(list)
        
        # Load example data if exists
        self._load_examples()
    
    def _load_examples(self):
        """Load examples from JSON file if it exists"""
        example_file = Path(__file__).parent / 'data' / 'examples.json'
        if example_file.exists():
            with open(example_file, 'r') as f:
                data = json.load(f)
                self.examples = data.get('examples', [])
                self._analyze_examples()

    def _analyze_examples(self):
        """Analyze all loaded examples and extract patterns"""
        for example in self.examples:
            self._update_patterns(example)

    def add_example(self, content: str, metadata: Dict):
        """Add a new example and analyze it"""
        example = {
            'content': content,
            'metadata': metadata,
            'analysis': self._analyze_single_content(content)
        }
        self.examples.append(example)
        self._update_patterns(example)
        self._save_examples()

    def _analyze_single_content(self, content: str) -> Dict:
        """Analyze a single piece of content"""
        paragraphs = content.split('\n\n')
        sentences = [s.strip() for s in content.split('.') if s.strip()]
        words = content.split()
        
        return {
            'structure': {
                'paragraphs': len(paragraphs),
                'sentences': len(sentences),
                'words': len(words),
                'avg_sentence_length': len(words) / len(sentences) if sentences else 0
            },
            'patterns': {
                'hooks': self._extract_hooks(sentences[0] if sentences else ""),
                'calls_to_action': self._extract_cta(sentences[-1] if sentences else ""),
                'key_phrases': self._extract_key_phrases(content)
            },
            'style_markers': self._analyze_style(content)
        }

    def _extract_hooks(self, opening: str) -> List[str]:
        """Extract opening hook patterns"""
        hooks = []
        if re.search(r'^(Did you know|Have you ever|What if|Imagine|Here\'s|Today)', opening):
            hooks.append('question_hook')
        if re.search(r'\d+', opening):
            hooks.append('statistic_hook')
        if '"' in opening or '"' in opening:
            hooks.append('quote_hook')
        return hooks

    def _extract_cta(self, closing: str) -> List[str]:
        """Extract call-to-action patterns"""
        ctas = []
        if re.search(r'(What do you think|Share your|Let me know|Comment below)', closing):
            ctas.append('engagement_question')
        if re.search(r'(Follow|Connect|DM)', closing):
            ctas.append('connection_request')
        return ctas

    def _extract_key_phrases(self, content: str) -> List[str]:
        """Extract key phrases and industry-specific terminology"""
        phrases = []
        # Add key phrase extraction logic here
        return phrases

    def _analyze_style(self, content: str) -> Dict:
        """Analyze writing style markers"""
        return {
            'personal_pronouns': len(re.findall(r'\b(I|we|our|my)\b', content, re.I)),
            'questions': len(re.findall(r'\?', content)),
            'bullet_points': len(re.findall(r'•|\*|-', content)),
            'emojis': len(re.findall(r'[\U0001F300-\U0001F9FF]', content)),
            'hashtags': len(re.findall(r'#\w+', content))
        }

    def _update_patterns(self, example: Dict):
        """Update various pattern collections based on an example"""
        content = example['content']
        metadata = example.get('metadata', {})

        # Extract industry keywords
        industry = metadata.get('industry', 'general')
        words = content.lower().split()
        self.industry_keywords[industry].update(words)

        # Analyze story structure
        paragraphs = content.split('\n\n')
        story_type = metadata.get('story_type', 'general')
        self.story_structures[story_type].append({
            'paragraph_count': len(paragraphs),
            'first_paragraph': paragraphs[0] if paragraphs else '',
            'last_paragraph': paragraphs[-1] if paragraphs else ''
        })

        # Analyze tone and writing style
        tone = metadata.get('tone', 'professional')
        self.patterns[tone].append({
            'sentence_patterns': self._extract_sentence_patterns(content),
            'hooks': self._extract_hooks(content)
        })

    def _extract_sentence_patterns(self, content: str) -> List[str]:
        """Extract common sentence structures"""
        sentences = re.split(r'[.!?]', content)
        patterns = []
        for sentence in sentences:
            # Extract basic sentence pattern
            pattern = re.sub(r'\w+', 'WORD', sentence.strip())
            patterns.append(pattern)
        return patterns

    def _extract_hooks(self, content: str) -> List[str]:
        """Extract potential hooks from the content"""
        sentences = re.split(r'[.!?]', content)
        hooks = []
        for sentence in sentences[:3]:  # Look at first few sentences
            if len(sentence.split()) <= 10:  # Short sentences are likely hooks
                hooks.append(sentence.strip())
        return hooks

    def _save_examples(self):
        """Save examples to a JSON file"""
        example_file = Path(__file__).parent / 'data' / 'examples.json'
        example_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(example_file, 'w') as f:
            json.dump({
                'examples': self.examples,
                'patterns': {k: str(v) for k, v in self.patterns.items()},
                'industry_keywords': {k: list(v) for k, v in self.industry_keywords.items()}
            }, f, indent=2)

    def generate_content_structure(self, params: Dict) -> Dict:
        """Generate content structure based on analyzed patterns"""
        story_type = params.get('story_type', 'general')
        industry = params.get('industry', 'general')
        
        # Get average structure for story type
        structures = self.story_structures.get(story_type, [])
        if not structures:
            structures = [s for structs in self.story_structures.values() for s in structs]
        
        avg_structure = {
            'paragraphs': int(np.mean([s['paragraph_count'] for s in structures])),
            'sentences': int(np.mean([len(re.split(r'[.!?]', s['first_paragraph'])) + len(re.split(r'[.!?]', s['last_paragraph'])) for s in structures])),
            'words': int(np.mean([len(s['first_paragraph'].split()) + len(s['last_paragraph'].split()) for s in structures]))
        }
        
        # Get relevant examples
        relevant_examples = [
            ex for ex in self.examples 
            if ex['metadata'].get('story_type') == story_type 
            or ex['metadata'].get('industry') == industry
        ]
        
        # Extract patterns
        hooks = []
        ctas = []
        for ex in relevant_examples:
            hooks.extend(ex['analysis']['patterns']['hooks'])
            ctas.extend(ex['analysis']['patterns']['calls_to_action'])
        
        return {
            'structure': avg_structure,
            'recommended_hooks': list(set(hooks)),
            'recommended_ctas': list(set(ctas)),
            'industry_keywords': list(self.industry_keywords[industry])
        }

    def get_similar_examples(self, params: Dict, limit: int = 3) -> List[Dict]:
        """Get similar examples based on parameters"""
        story_type = params.get('story_type')
        industry = params.get('industry')
        
        similar = []
        for example in self.examples:
            score = 0
            if example['metadata'].get('story_type') == story_type:
                score += 2
            if example['metadata'].get('industry') == industry:
                score += 2
            if score > 0:
                similar.append((score, example))
        
        similar.sort(key=lambda x: x[0], reverse=True)
        return [ex for _, ex in similar[:limit]]
