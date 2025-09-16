"""
Text processing utilities for document analysis
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from io import BytesIO
from datetime import datetime

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk

# PDF processing
try:
    import PyPDF2
    from pdfplumber import PDF
except ImportError:
    PyPDF2 = None
    PDF = None

# DOCX processing
try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

# Additional NLP libraries
try:
    import spacy
    from textstat import flesch_reading_ease, flesch_kincaid_grade
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    spacy = None
    flesch_reading_ease = None
    flesch_kincaid_grade = None
    TfidfVectorizer = None
    cosine_similarity = None

logger = logging.getLogger(__name__)


class TextProcessor:
    """Text processing and analysis utilities"""
    
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        
        # Load spaCy model if available
        self.nlp_model = None
        if spacy:
            try:
                self.nlp_model = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
    
    def extract_pdf_text(self, file_content: bytes) -> str:
        """
        Extract text from PDF file
        
        Args:
            file_content: PDF file content as bytes
            
        Returns:
            Extracted text
        """
        try:
            if PDF:
                # Use pdfplumber for better text extraction
                with PDF(BytesIO(file_content)) as pdf:
                    text_parts = []
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)
                    return '\n'.join(text_parts)
            
            elif PyPDF2:
                # Fallback to PyPDF2
                pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
                text_parts = []
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                return '\n'.join(text_parts)
            
            else:
                raise ValueError("No PDF processing library available")
        
        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}")
            raise ValueError(f"Failed to extract text from PDF: {e}")
    
    def extract_docx_text(self, file_content: bytes) -> str:
        """
        Extract text from DOCX file
        
        Args:
            file_content: DOCX file content as bytes
            
        Returns:
            Extracted text
        """
        try:
            if not DocxDocument:
                raise ValueError("python-docx library not available")
            
            doc = DocxDocument(BytesIO(file_content))
            text_parts = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)
            
            return '\n'.join(text_parts)
        
        except Exception as e:
            logger.error(f"DOCX text extraction failed: {e}")
            raise ValueError(f"Failed to extract text from DOCX: {e}")
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.,!?;:\'"()-]', '', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        
        return text
    
    def tokenize_text(self, text: str) -> List[str]:
        """
        Tokenize text into words
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of tokens
        """
        tokens = word_tokenize(text.lower())
        # Remove stopwords and non-alphabetic tokens
        filtered_tokens = [
            self.lemmatizer.lemmatize(token) 
            for token in tokens 
            if token.isalpha() and token not in self.stop_words
        ]
        return filtered_tokens
    
    def extract_sentences(self, text: str) -> List[str]:
        """
        Extract sentences from text
        
        Args:
            text: Text to process
            
        Returns:
            List of sentences
        """
        sentences = sent_tokenize(text)
        return [sentence.strip() for sentence in sentences if sentence.strip()]
    
    def calculate_readability(self, text: str) -> Dict[str, float]:
        """
        Calculate text readability metrics
        
        Args:
            text: Text to analyze
            
        Returns:
            Readability metrics
        """
        metrics = {}
        
        try:
            if flesch_reading_ease:
                metrics['flesch_reading_ease'] = flesch_reading_ease(text)
                metrics['flesch_kincaid_grade'] = flesch_kincaid_grade(text)
            
            # Basic metrics
            sentences = self.extract_sentences(text)
            words = word_tokenize(text)
            
            metrics.update({
                'sentence_count': len(sentences),
                'word_count': len(words),
                'avg_words_per_sentence': len(words) / len(sentences) if sentences else 0,
                'avg_sentence_length': sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
            })
        
        except Exception as e:
            logger.warning(f"Readability calculation failed: {e}")
        
        return metrics
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text
        
        Args:
            text: Text to analyze
            
        Returns:
            List of entities
        """
        entities = []
        
        try:
            if self.nlp_model:
                # Use spaCy for better entity recognition
                doc = self.nlp_model(text)
                for ent in doc.ents:
                    entities.append({
                        'text': ent.text,
                        'label': ent.label_,
                        'start': ent.start_char,
                        'end': ent.end_char,
                        'confidence': getattr(ent, 'score', 1.0)
                    })
            else:
                # Fallback to NLTK
                tokens = word_tokenize(text)
                pos_tags = pos_tag(tokens)
                chunks = ne_chunk(pos_tags)
                
                current_entity = []
                current_label = None
                
                for chunk in chunks:
                    if hasattr(chunk, 'label'):
                        if current_entity:
                            entities.append({
                                'text': ' '.join(current_entity),
                                'label': current_label,
                                'confidence': 0.8
                            })
                        current_entity = [token for token, pos in chunk]
                        current_label = chunk.label()
                    else:
                        if current_entity:
                            entities.append({
                                'text': ' '.join(current_entity),
                                'label': current_label,
                                'confidence': 0.8
                            })
                            current_entity = []
                            current_label = None
        
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
        
        return entities
    
    def extract_keywords(self, text: str, num_keywords: int = 10) -> List[Dict[str, Any]]:
        """
        Extract keywords using TF-IDF
        
        Args:
            text: Text to analyze
            num_keywords: Number of keywords to extract
            
        Returns:
            List of keywords with scores
        """
        try:
            if not TfidfVectorizer:
                # Simple fallback: word frequency
                tokens = self.tokenize_text(text)
                word_freq = {}
                for token in tokens:
                    word_freq[token] = word_freq.get(token, 0) + 1
                
                sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
                return [
                    {'keyword': word, 'score': freq, 'weight': freq / len(tokens)}
                    for word, freq in sorted_words[:num_keywords]
                ]
            
            # Use TF-IDF
            sentences = self.extract_sentences(text)
            if len(sentences) < 2:
                sentences = [text]  # Use full text if not enough sentences
            
            vectorizer = TfidfVectorizer(
                max_features=num_keywords * 2,
                stop_words='english',
                lowercase=True,
                token_pattern=r'\b[a-zA-Z]{3,}\b'
            )
            
            tfidf_matrix = vectorizer.fit_transform(sentences)
            feature_names = vectorizer.get_feature_names_out()
            
            # Get average TF-IDF scores across all sentences
            mean_scores = tfidf_matrix.mean(axis=0).A1
            
            # Sort by score
            keyword_scores = list(zip(feature_names, mean_scores))
            keyword_scores.sort(key=lambda x: x[1], reverse=True)
            
            return [
                {
                    'keyword': keyword,
                    'score': float(score),
                    'weight': float(score) / max(mean_scores) if max(mean_scores) > 0 else 0
                }
                for keyword, score in keyword_scores[:num_keywords]
                if score > 0
            ]
        
        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            return []
    
    def generate_summary(self, text: str, max_length: int = 500) -> str:
        """
        Generate extractive summary of text
        
        Args:
            text: Text to summarize
            max_length: Maximum summary length in characters
            
        Returns:
            Text summary
        """
        try:
            sentences = self.extract_sentences(text)
            if not sentences:
                return ""
            
            if len(' '.join(sentences)) <= max_length:
                return text
            
            # Simple extractive summarization using sentence ranking
            # Score sentences based on keyword frequency
            keywords = self.extract_keywords(text, num_keywords=20)
            keyword_set = {kw['keyword'] for kw in keywords}
            
            sentence_scores = []
            for sentence in sentences:
                score = 0
                sentence_words = set(self.tokenize_text(sentence))
                
                # Score based on keyword overlap
                overlap = sentence_words.intersection(keyword_set)
                score += len(overlap)
                
                # Prefer sentences of moderate length
                word_count = len(sentence.split())
                if 10 <= word_count <= 30:
                    score += 2
                elif word_count < 5:
                    score -= 1
                
                sentence_scores.append((sentence, score))
            
            # Sort by score and select top sentences
            sentence_scores.sort(key=lambda x: x[1], reverse=True)
            
            summary_sentences = []
            current_length = 0
            
            for sentence, score in sentence_scores:
                if current_length + len(sentence) <= max_length:
                    summary_sentences.append(sentence)
                    current_length += len(sentence)
                else:
                    break
            
            # Reorder sentences by their original position
            original_order = []
            for summary_sentence in summary_sentences:
                original_index = sentences.index(summary_sentence)
                original_order.append((original_index, summary_sentence))
            
            original_order.sort(key=lambda x: x[0])
            
            return ' '.join([sentence for _, sentence in original_order])
        
        except Exception as e:
            logger.error(f"Text summarization failed: {e}")
            return text[:max_length] + "..." if len(text) > max_length else text
    
    def classify_text(self, text: str, categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Classify text into categories
        
        Args:
            text: Text to classify
            categories: Optional list of allowed categories
            
        Returns:
            Classification results
        """
        # Simple rule-based classification for demonstration
        # In production, you'd use a trained model
        
        text_lower = text.lower()
        
        # Default categories if none provided
        if not categories:
            categories = [
                'business', 'technology', 'science', 'health', 'education',
                'entertainment', 'sports', 'politics', 'travel', 'food',
                'finance', 'legal', 'medical', 'academic', 'news'
            ]
        
        # Simple keyword-based classification
        category_keywords = {
            'business': ['business', 'company', 'market', 'profit', 'revenue', 'corporate'],
            'technology': ['technology', 'software', 'computer', 'digital', 'ai', 'machine learning'],
            'science': ['research', 'study', 'experiment', 'hypothesis', 'scientific'],
            'health': ['health', 'medical', 'doctor', 'patient', 'treatment', 'disease'],
            'education': ['education', 'student', 'teacher', 'school', 'university', 'learning'],
            'legal': ['law', 'legal', 'court', 'judge', 'attorney', 'contract'],
            'finance': ['finance', 'money', 'investment', 'bank', 'economic', 'financial'],
            'academic': ['paper', 'abstract', 'methodology', 'conclusion', 'references', 'journal']
        }
        
        scores = {}
        for category in categories:
            score = 0
            if category in category_keywords:
                for keyword in category_keywords[category]:
                    score += text_lower.count(keyword)
            scores[category] = score
        
        # Find primary category
        primary_category = max(scores, key=scores.get) if scores else 'general'
        confidence = scores[primary_category] / sum(scores.values()) if sum(scores.values()) > 0 else 0
        
        return {
            'primary_category': primary_category,
            'confidence': confidence,
            'all_scores': scores,
            'classification_type': 'keyword_based'
        }
    
    def process_text(self, text: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Comprehensive text processing
        
        Args:
            text: Text to process
            options: Processing options
            
        Returns:
            Processing results
        """
        if not options:
            options = {}
        
        results = {
            'processed_at': datetime.utcnow().isoformat(),
            'original_length': len(text)
        }
        
        try:
            # Clean text
            cleaned_text = self.clean_text(text)
            results['cleaned_text'] = cleaned_text
            results['cleaned_length'] = len(cleaned_text)
            
            # Basic metrics
            sentences = self.extract_sentences(cleaned_text)
            tokens = self.tokenize_text(cleaned_text)
            
            results.update({
                'sentence_count': len(sentences),
                'word_count': len(tokens),
                'unique_words': len(set(tokens)),
                'avg_sentence_length': len(tokens) / len(sentences) if sentences else 0
            })
            
            # Readability metrics
            if options.get('calculate_readability', True):
                results['readability'] = self.calculate_readability(cleaned_text)
            
            # Entity extraction
            if options.get('extract_entities', True):
                results['entities'] = self.extract_entities(cleaned_text)
            
            # Keyword extraction
            if options.get('extract_keywords', True):
                num_keywords = options.get('num_keywords', 10)
                results['keywords'] = self.extract_keywords(cleaned_text, num_keywords)
            
            # Text classification
            if options.get('classify_text', True):
                categories = options.get('categories')
                results['classification'] = self.classify_text(cleaned_text, categories)
            
            # Summary generation
            if options.get('generate_summary', True):
                max_length = options.get('summary_max_length', 500)
                results['summary'] = self.generate_summary(cleaned_text, max_length)
            
            results['success'] = True
            
        except Exception as e:
            logger.error(f"Text processing failed: {e}")
            results.update({
                'success': False,
                'error': str(e)
            })
        
        return results


# Global instance
text_processor = TextProcessor()