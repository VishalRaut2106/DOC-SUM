import os
import logging
import google.generativeai as genai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def configure_gemini(api_key, model_name="gemini-pro"):
    """
    Configure the Gemini API with the provided API key.
    
    Args:
        api_key (str): The Gemini API key.
        model_name (str): The model name to use (default: gemini-pro).
        
    Returns:
        tuple: (status, model or error_message)
    """
    if not api_key:
        logger.error("Gemini API key is not provided.")
        return False, "API key is required"
    
    try:
        # Configure the Gemini API
        genai.configure(api_key=api_key)
        
        # Get the specified model
        model = genai.GenerativeModel(model_name)
        
        return True, model
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error configuring Gemini: {error_message}")
        return False, error_message

def extract_summary(text, model):
    """
    Extract a summary from the given text using the Gemini API.
    
    Args:
        text (str): The text to summarize.
        model: The configured Gemini model.
        
    Returns:
        str: The generated summary.
    """
    if not text.strip():
        logger.warning("Empty text provided for summarization.")
        return "No content to summarize."
    
    try:
        # Prepare the prompt
        prompt = f"""Please provide a comprehensive summary of the following text, capturing all key points:

        Text to summarize:
        ---
        {text}
        ---

Your summary should:
1. Be well-structured and easy to understand
2. Maintain the original meaning and important details
3. Be between 10-20% of the original length
4. Use bullet points for main concepts where appropriate
"""
        
        # Generate the summary
        response = model.generate_content(prompt)
        summary = response.text
        
        if not summary:
            logger.warning("Empty summary generated.")
            return "Failed to generate summary. Please try again."
        
        return summary
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error extracting summary: {error_message}")
        raise Exception(f"Summary generation failed: {error_message}")

def split_into_paragraphs(text, model, max_paragraphs=10):
    """
    Split the text into meaningful paragraphs using the Gemini API.
    
    Args:
        text (str): The text to split into paragraphs.
        model: The configured Gemini model.
        max_paragraphs (int): Maximum number of paragraphs to return.
        
    Returns:
        list: List of paragraphs.
    """
    if not text.strip():
        logger.warning("Empty text provided for paragraph splitting.")
        return []
    
    try:
        # Check if text already has paragraphs
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        
        # If we already have reasonable paragraphs, return them
        if len(paragraphs) >= 3 and len(paragraphs) <= max_paragraphs:
            return paragraphs[:max_paragraphs]
        
        # If we have too many short paragraphs, ask Gemini to reorganize
        if len(paragraphs) > max_paragraphs:
            prompt = f"""Please reorganize the following text into {max_paragraphs} meaningful, well-structured paragraphs:

            Text to reorganize:
            ---
            {text}
            ---

Each paragraph should:
1. Cover a specific topic or idea
2. Be logically connected to the previous and next paragraphs
3. Be a reasonable length (not too short, not too long)
"""
            
            response = model.generate_content(prompt)
            content = response.text
            
            # Extract the paragraphs from the response
            new_paragraphs = [p for p in content.split('\n\n') if p.strip()]
            if new_paragraphs:
                return new_paragraphs[:max_paragraphs]
        
        # If we have too few paragraphs, ask Gemini to split it more
        if len(paragraphs) < 3:
            prompt = f"""Please split the following text into 5-10 meaningful, well-structured paragraphs:

{text}

Each paragraph should:
1. Cover a specific topic or idea
2. Be logically connected to the previous and next paragraphs
3. Be a reasonable length (not too short, not too long)
"""
            
            response = model.generate_content(prompt)
            content = response.text
            
            # Extract the paragraphs from the response
            new_paragraphs = [p for p in content.split('\n\n') if p.strip()]
            if new_paragraphs:
                return new_paragraphs[:max_paragraphs]
        
        # If all else fails, return the original paragraphs or split by sentences
        if not paragraphs:
            # Split by sentences if no paragraphs
            sentences = [s.strip() + '.' for s in text.replace('\n', ' ').split('.') if s.strip()]
            paragraphs = []
            current = ""
            
            for sentence in sentences:
                if len(current) + len(sentence) > 500:  # Arbitrary length for paragraph
                    paragraphs.append(current)
                    current = sentence
                else:
                    current += " " + sentence
            
            if current:
                paragraphs.append(current)
        
        return paragraphs[:max_paragraphs]
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error splitting text into paragraphs: {error_message}")
        raise Exception(f"Paragraph splitting failed: {error_message}")

def generate_questions(paragraph, model, num_questions=3):
    """
    Generate questions and answers based on the paragraph using the Gemini API.
    
    Args:
        paragraph (str): The paragraph to generate questions from.
        model: The configured Gemini model.
        num_questions (int): The number of questions to generate.
        
    Returns:
        list: List of dictionaries containing questions and answers.
    """
    if not paragraph.strip():
        logger.warning("Empty paragraph provided for question generation.")
        return []
    
    try:
        # Prepare the prompt
        prompt = f"""Based on the following paragraph, generate {num_questions} quiz questions that would test understanding of the key concepts. For each question, provide a detailed answer.

        Paragraph to use for questions:
        ---
        {paragraph}
        ---

Format your response as follows:
Q1: [Question 1]
A1: [Answer 1]

Q2: [Question 2]
A2: [Answer 2]

Q3: [Question 3]
A3: [Answer 3]

Make sure the questions:
1. Test different aspects of the content
2. Vary in difficulty
3. Include some that require critical thinking
4. Are clear and unambiguous
"""
        
        # Generate the questions and answers
        response = model.generate_content(prompt)
        content = response.text
        
        # Parse the response into question-answer pairs
        qa_pairs = []
        lines = content.strip().split('\n')
        
        current_question = ""
        current_answer = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('Q') and ':' in line:
                # If we already have a question and answer, add them to our pairs
                if current_question and current_answer:
                    qa_pairs.append({
                        'question': current_question,
                        'answer': current_answer
                    })
                
                # Start a new question
                current_question = line.split(':', 1)[1].strip()
                current_answer = ""
            elif line.startswith('A') and ':' in line:
                # Add the answer
                current_answer = line.split(':', 1)[1].strip()
        
        # Add the last question-answer pair if we have one
        if current_question and current_answer:
            qa_pairs.append({
                'question': current_question,
                'answer': current_answer
            })
        
        return qa_pairs
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error generating questions: {error_message}")
        raise Exception(f"Question generation failed: {error_message}") 