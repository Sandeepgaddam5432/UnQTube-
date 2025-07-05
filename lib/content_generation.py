"""
Content Generation Module for UnQTube

This module provides advanced content generation capabilities using
multi-step prompt chains and sophisticated AI interactions.
"""

import os
import json
import asyncio
import time
from lib.gemini_api import generate_script_with_gemini
from lib.media_api import translateto
from lib.language import get_language_code
from lib.config_utils import read_config_file

# Import Claude API if available
try:
    from lib.claude_api import generate_script_with_claude, is_claude_available
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

class PromptChain:
    """Advanced prompt chain for sophisticated content generation
    
    This class implements a multi-step prompt chain that builds increasingly
    complex and refined content through a series of specialized AI interactions.
    """
    
    def __init__(self, title, genre="", language="english"):
        """Initialize the prompt chain
        
        Args:
            title (str): The main topic title
            genre (str): The general genre/category
            language (str): The target language for content
        """
        self.title = title
        self.genre = genre or self._infer_genre(title)
        self.language = language
        self.language_code = get_language_code(language)
        self.results = {}
        self.max_retries = 2
        
        # Determine which AI model to use
        config = read_config_file()
        self.use_claude = config.get('use_claude', 'no').lower() in ['yes', 'true', '1'] and CLAUDE_AVAILABLE
        if self.use_claude:
            print("Using Claude AI for content generation")
        else:
            print("Using Gemini AI for content generation")
        
    def _infer_genre(self, title):
        """Infer a general genre if none is provided"""
        # Common categories that might be inferred from title words
        genres = {
            "game": "video games",
            "food": "cooking",
            "recipe": "cooking",
            "film": "movies",
            "movie": "movies",
            "travel": "travel",
            "place": "travel",
            "technology": "tech",
            "tech": "tech",
            "history": "history",
            "science": "science",
            "book": "literature",
            "music": "music",
            "song": "music"
        }
        
        # Check for genre keywords in the title
        words = title.lower().split()
        for word in words:
            if word in genres:
                return genres[word]
                
        return "general"
        
    async def execute_chain(self):
        """Execute the complete prompt chain
        
        This is the main entry point that runs all steps in sequence.
        
        Returns:
            dict: The complete content generation results
        """
        try:
            print("\n==== Starting advanced content generation prompt chain ====")
            start_time = time.time()
            
            # Execute steps in sequence
            print("Step 1/5: Researching topic...")
            self.results["research"] = await self._execute_research()
            
            print("Step 2/5: Creating content outline...")
            self.results["outline"] = await self._create_outline()
            
            print("Step 3/5: Developing full script...")
            self.results["detailed_script"] = await self._develop_full_script()
            
            print("Step 4/5: Creating engagement hooks...")
            self.results["hooks"] = await self._create_hooks()
            
            print("Step 5/5: Generating optimal search terms...")
            self.results["search_terms"] = await self._generate_search_terms()
            
            elapsed = time.time() - start_time
            print(f"==== Completed content generation in {elapsed:.2f} seconds ====\n")
            
            # Compile and return final output
            return self._compile_final_output()
            
        except Exception as e:
            print(f"Error during prompt chain execution: {e}")
            # If we have partial results, try to salvage what we can
            if self.results and "outline" in self.results:
                print("Attempting to compile partial results...")
                return self._compile_final_output()
            else:
                # If we don't have enough to work with, raise the error
                raise
    
    async def execute_short_chain(self):
        """Execute a shorter prompt chain optimized for short-form videos
        
        Returns:
            dict: Content generation results for short videos
        """
        try:
            print("\n==== Starting short video content generation ====")
            start_time = time.time()
            
            # Execute short video steps
            print("Step 1/3: Creating short video outline...")
            self.results["outline"] = await self._create_short_outline()
            
            print("Step 2/3: Developing short script...")
            self.results["detailed_script"] = await self._develop_short_script()
            
            print("Step 3/3: Generating visual search terms...")
            self.results["search_terms"] = await self._generate_search_terms(is_short=True)
            
            elapsed = time.time() - start_time
            print(f"==== Completed short video content in {elapsed:.2f} seconds ====\n")
            
            # Compile and return final output
            return self._compile_short_output()
            
        except Exception as e:
            print(f"Error during short prompt chain execution: {e}")
            raise
    
    async def _execute_research(self):
        """Research the topic to gather key information
        
        Returns:
            str: Research results about the topic
        """
        prompt = f"""
        You're a professional researcher gathering key information about {self.title}.
        
        Provide comprehensive background information including:
        1. What exactly is {self.title}? Provide a clear definition.
        2. Historical context and development
        3. Key facts, statistics, or notable features
        4. Why this topic is interesting or important
        5. Current trends or developments related to {self.title}
        
        For a top 10 video about {self.title}, what are the most important pieces of information
        that would make the content factually accurate and interesting to viewers?
        
        Focus on providing factual, detailed information rather than just opinions.
        
        Format your response as paragraphs of factual information, not as a script.
        """
        
        for attempt in range(self.max_retries):
            try:
                research = await self._generate_content(prompt)
                # Basic validation - check length and if it contains actual content
                if len(research) > 300 and ":" in research:
                    return research
            except Exception as e:
                print(f"Research generation attempt {attempt+1} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise
        
        # Fallback minimal research
        return f"The topic {self.title} is part of the {self.genre} category. This will be a top 10 video about the best examples of {self.title}."
        
    async def _create_outline(self):
        """Create a compelling video outline
        
        Returns:
            str: Structured outline for the video content
        """
        # Include research results if available
        research_context = ""
        if "research" in self.results:
            research_context = f"""
            Based on this research information:
            {self.results["research"]}
            """
            
        prompt = f"""
        You're a top-tier YouTube content strategist creating an engaging outline for a video about {self.title}.
        {research_context}
        
        Create a compelling video outline with:
        1. An attention-grabbing hook for the first 15 seconds
        2. A clear thesis statement explaining what viewers will learn
        3. 10 main points/items about {self.title}, organized in logical progression
        4. For each of the 10 points, include:
           - A concise headline
           - Key supporting details/facts
           - Potential visual elements that would enhance this section
        5. A conclusion with a thought-provoking question and clear call-to-action
        
        Format as structured JSON with the following format:
        {{
          "hook": "Opening hook text here",
          "thesis": "Main thesis statement",
          "items": [
            {{
              "rank": 10,
              "title": "Item title",
              "description": "Description with key points",
              "visuals": ["visual element 1", "visual element 2"]
            }},
            // ... 9 more items in descending order (10, 9, 8...)
          ],
          "conclusion": "Conclusion text with call to action"
        }}
        
        The 10 items should be in descending order, starting with #10 and ending with #1 (the best).
        """
        
        for attempt in range(self.max_retries):
            try:
                outline_result = await self._generate_content(prompt)
                # Try to parse as JSON to validate
                try:
                    # Try to find and extract valid JSON if it's embedded in other text
                    import re
                    json_match = re.search(r'(\{[\s\S]*\})', outline_result)
                    if json_match:
                        json_str = json_match.group(1)
                        try:
                            outline_json = json.loads(json_str)
                            if self._validate_outline(outline_json):
                                return json.dumps(outline_json)
                        except:
                            pass
                    
                    # If that didn't work, try the original string
                    outline_json = json.loads(outline_result)
                    if self._validate_outline(outline_json):
                        return outline_result
                except json.JSONDecodeError:
                    print(f"Could not parse outline as JSON, attempt {attempt+1}")
                    # Try to fix common JSON formatting issues
                    try:
                        # Replace single quotes with double quotes
                        fixed_json = outline_result.replace("'", '"')
                        # Fix unquoted keys
                        fixed_json = re.sub(r'(\s*?)(\w+)(\s*?):', r'\1"\2"\3:', fixed_json)
                        # Try to parse the fixed JSON
                        outline_json = json.loads(fixed_json)
                        if self._validate_outline(outline_json):
                            return json.dumps(outline_json)
                    except:
                        if attempt == self.max_retries - 1:
                            # Last attempt, try to extract usable content
                            return self._extract_outline_fallback(outline_result)
            except Exception as e:
                print(f"Outline generation attempt {attempt+1} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise
        
        # Create minimal fallback outline
        return self._create_fallback_outline()
    
    def _validate_outline(self, outline_json):
        """Validate that the outline JSON has the expected structure
        
        Args:
            outline_json (dict): The parsed JSON outline
            
        Returns:
            bool: True if the outline has valid structure, False otherwise
        """
        # Check for required keys
        if not all(key in outline_json for key in ["hook", "thesis", "items", "conclusion"]):
            return False
            
        # Check items list
        if not isinstance(outline_json["items"], list) or len(outline_json["items"]) < 5:
            return False
            
        # Check item structure
        for item in outline_json["items"]:
            if not all(key in item for key in ["rank", "title", "description"]):
                return False
                
        return True
        
    def _extract_outline_fallback(self, outline_text):
        """Extract outline components from text if JSON parsing fails
        
        Args:
            outline_text (str): The raw outline text
            
        Returns:
            str: A simplified JSON outline
        """
        # Basic extraction of components
        lines = outline_text.split('\n')
        hook = "Welcome to our video about " + self.title
        thesis = f"Today we're exploring the top 10 {self.title}"
        items = []
        conclusion = f"Thanks for watching our video about {self.title}. If you enjoyed this content, please like and subscribe!"
        
        # Try to extract numbered items
        current_item = None
        for line in lines:
            line = line.strip()
            
            # Look for hooks
            if "hook" in line.lower() and ":" in line:
                hook = line.split(":", 1)[1].strip()
                
            # Look for thesis
            elif "thesis" in line.lower() and ":" in line:
                thesis = line.split(":", 1)[1].strip()
                
            # Look for conclusion
            elif "conclusion" in line.lower() and ":" in line:
                conclusion = line.split(":", 1)[1].strip()
                
            # Look for numbered items (10. Item title, #9 - Item title, etc.)
            elif any(f"{i}" in line[:5] for i in range(1, 11)):
                for i in range(1, 11):
                    if f"{i}." in line[:5] or f"#{i}" in line[:5] or f"{i}:" in line[:5]:
                        if current_item:
                            items.append(current_item)
                        title = line.split(".", 1)[1].strip() if "." in line else line
                        current_item = {
                            "rank": i,
                            "title": title,
                            "description": f"This is item #{i} about {self.title}",
                            "visuals": [f"{self.title} {i}", f"{title} visualization"]
                        }
                        break
            
            # Add text to current item description
            elif current_item and line and not line.startswith("#") and not line.startswith("{") and not line.startswith("}"):
                current_item["description"] = current_item.get("description", "") + " " + line
        
        # Add the last item if it exists
        if current_item:
            items.append(current_item)
            
        # If we couldn't extract enough items, create some
        while len(items) < 10:
            items.append({
                "rank": len(items) + 1,
                "title": f"Example of {self.title} #{len(items) + 1}",
                "description": f"This is an interesting example of {self.title}.",
                "visuals": [f"{self.title} example", f"{self.title} visual"]
            })
        
        # Create JSON structure
        outline = {
            "hook": hook,
            "thesis": thesis,
            "items": items,
            "conclusion": conclusion
        }
        
        return json.dumps(outline, indent=2)
    
    def _create_fallback_outline(self):
        """Create a minimal fallback outline when all else fails
        
        Returns:
            str: JSON string with basic outline structure
        """
        items = []
        for i in range(10, 0, -1):
            items.append({
                "rank": i,
                "title": f"#{i}: Example of {self.title}",
                "description": f"This is the #{i} best example of {self.title}.",
                "visuals": [f"{self.title} {i}", f"{self.title} example {i}"]
            })
            
        outline = {
            "hook": f"Welcome to our top 10 video about {self.title}!",
            "thesis": f"Today we're counting down the 10 best examples of {self.title} in the {self.genre} category.",
            "items": items,
            "conclusion": f"Thanks for watching our video about {self.title}. If you enjoyed this content, please like and subscribe!"
        }
        
        return json.dumps(outline, indent=2)
        
    async def _develop_full_script(self):
        """Develop the full detailed script based on the outline
        
        Returns:
            str: Complete script with all sections
        """
        try:
            # Parse the outline
            if not self.results.get("outline"):
                raise ValueError("Outline not available")
                
            outline_json = json.loads(self.results["outline"])
            
            # Build the prompt with the outline structure
            prompt = f"""
            You are an expert YouTube scriptwriter creating a professional script for a top 10 video about {self.title}.
            
            Use this outline to create a complete, detailed script:
            
            HOOK: {outline_json.get("hook", f"Welcome to our video about {self.title}")}
            
            THESIS: {outline_json.get("thesis", f"Today we'll explore the top 10 examples of {self.title}")}
            
            ITEMS:
            """
            
            # Add each item from the outline
            items = outline_json.get("items", [])
            for item in items:
                prompt += f"""
                #{item.get("rank", "")}: {item.get("title", "")}
                Details: {item.get("description", "")}
                
                """
                
            prompt += f"""
            CONCLUSION: {outline_json.get("conclusion", "Thanks for watching!")}
            
            For each section, write natural, engaging content that:
            1. Uses conversational language and a friendly tone
            2. Includes interesting facts and details to educate viewers
            3. Uses transitions between sections
            4. Includes occasional questions or statements that directly engage the audience
            5. For the top items (#3, #2, #1), builds excitement and anticipation
            
            Format the script with clear section headers (INTRO, #10, #9... etc., CONCLUSION) 
            and make the content flow naturally between sections.
            
            The entire script should be comprehensive, with at least 150-200 words for each of the top 10 items.
            """
            
            script = await self._generate_content(prompt)
            
            # Verify we got substantial content
            if len(script) < 500:
                print("Warning: Generated script is too short, attempting to expand...")
                return await self._expand_script(script)
                
            return script
            
        except Exception as e:
            print(f"Error developing full script: {e}")
            # Create a minimal script as fallback
            return self._create_fallback_script()
    
    async def _expand_script(self, initial_script):
        """Expand a script that's too short or lacks detail
        
        Args:
            initial_script (str): The initial script to expand
            
        Returns:
            str: The expanded script
        """
        prompt = f"""
        The following script for a video about {self.title} needs to be expanded with more detail,
        examples, and engaging content:
        
        {initial_script}
        
        Please expand this script to make it more comprehensive and engaging:
        1. Add more specific details, examples, and facts for each section
        2. Include more descriptive language and vivid imagery
        3. Add rhetorical questions and calls for audience engagement
        4. Make sure each of the top 10 items has at least 150-200 words of content
        5. Ensure smooth transitions between sections
        
        Provide the complete expanded script while maintaining the original structure and key points.
        """
        
        expanded_script = await self._generate_content(prompt)
        return expanded_script
    
    def _create_fallback_script(self):
        """Create a minimal fallback script when all else fails
        
        Returns:
            str: Basic script structure
        """
        script = f"""
        INTRO:
        Welcome to our video about {self.title}! Today we'll be counting down the top 10 examples
        in the {self.genre} category. Whether you're a fan or just curious, we've got some amazing
        selections for you. Let's get started!
        
        """
        
        # Generate 10 sections
        for i in range(10, 0, -1):
            script += f"""
            #{i}:
            Coming in at number {i}, we have an amazing example of {self.title}. 
            This one stands out because of its unique features and impressive qualities.
            It's definitely earned its place on our list because of its outstanding 
            characteristics and popularity among fans.
            
            """
        
        script += f"""
        CONCLUSION:
        Thanks for watching our countdown of the top 10 {self.title}! If you enjoyed this video,
        please like, comment, and subscribe for more content like this. Let us know in the comments
        if you agree with our list or if we missed any of your favorites!
        """
        
        return script
    
    async def _create_hooks(self):
        """Create compelling hooks for different parts of the video
        
        Returns:
            dict: Different hooks for various parts of the video
        """
        prompt = f"""
        Create compelling, attention-grabbing hooks for a YouTube video about {self.title}.
        
        For each hook type, create a script segment that will immediately capture viewer attention:
        
        1. OPENING HOOK (first 5 seconds): A powerful statement or question that stops scrolling viewers
        2. INTRO HOOK (15-20 seconds in): An intriguing fact or statement that makes viewers want to see the full countdown
        3. MIDPOINT HOOK (for item #5): A statement that builds anticipation for the top items
        4. FINALE HOOK (before item #1): A statement that creates maximum anticipation for the #1 spot
        5. SUBSCRIPTION HOOK (outro): A compelling reason for viewers to subscribe
        
        For each hook, use psychological techniques like curiosity gaps, powerful statistics,
        provocative questions, or bold claims that create emotional engagement.
        
        Format your response as JSON with the following structure:
        {{
          "opening_hook": "Hook text here",
          "intro_hook": "Hook text here",
          "midpoint_hook": "Hook text here",
          "finale_hook": "Hook text here",
          "subscription_hook": "Hook text here"
        }}
        """
        
        try:
            hooks_result = await self._generate_content(prompt)
            # Try to parse as JSON to validate
            try:
                # Try to find and extract valid JSON if it's embedded in other text
                import re
                json_match = re.search(r'(\{[\s\S]*\})', hooks_result)
                if json_match:
                    json_str = json_match.group(1)
                    try:
                        hooks_json = json.loads(json_str)
                        if all(key in hooks_json for key in ["opening_hook", "finale_hook", "subscription_hook"]):
                            return json.dumps(hooks_json)
                    except:
                        pass
                
                # If that didn't work, try the original string
                hooks_json = json.loads(hooks_result)
                # Basic validation
                if all(key in hooks_json for key in ["opening_hook", "finale_hook", "subscription_hook"]):
                    return hooks_result
            except json.JSONDecodeError:
                print("Could not parse hooks as JSON, attempting to fix...")
                try:
                    # Replace single quotes with double quotes
                    fixed_json = hooks_result.replace("'", '"')
                    # Fix unquoted keys
                    fixed_json = re.sub(r'(\s*?)(\w+)(\s*?):', r'\1"\2"\3:', fixed_json)
                    # Try to parse the fixed JSON
                    hooks_json = json.loads(fixed_json)
                    if all(key in hooks_json for key in ["opening_hook", "finale_hook", "subscription_hook"]):
                        return json.dumps(hooks_json)
                except:
                    print("Could not parse hooks as JSON, creating fallback")
        except Exception as e:
            print(f"Error creating hooks: {e}")
            
        # Create fallback hooks
        hooks = {
            "opening_hook": f"These are the 10 most amazing examples of {self.title} you need to see!",
            "intro_hook": f"The #1 item on this list shocked even the experts in {self.genre}!",
            "midpoint_hook": f"You won't believe what's coming in the top 5 {self.title} examples!",
            "finale_hook": f"The next example is considered by many to be the absolute best {self.title} of all time!",
            "subscription_hook": f"Subscribe now for more amazing content about {self.genre} and {self.title}!"
        }
        
        return json.dumps(hooks, indent=2)
    
    async def _generate_search_terms(self, is_short=False):
        """Generate optimal search terms for media based on the content
        
        Args:
            is_short (bool): Whether this is for a short video
            
        Returns:
            list: List of search terms for visuals
        """
        # Construct content from available results
        content = f"Topic: {self.title}\nGenre: {self.genre}\n\n"
        
        if "outline" in self.results:
            try:
                outline = json.loads(self.results["outline"])
                content += f"Outline: {json.dumps(outline, indent=2)}\n\n"
            except:
                content += f"Outline: {self.results['outline']}\n\n"
                
        if "detailed_script" in self.results and len(self.results["detailed_script"]) < 15000:
            content += f"Script: {self.results['detailed_script']}\n\n"
            
        prompt = f"""
        Based on this video content about {self.title}:
        
        {content}
        
        Generate {"10" if is_short else "20"} highly specific, visually descriptive search terms for finding
        stock footage or images that would perfectly accompany this content.
        
        For each search term:
        1. Be extremely specific and visually detailed
        2. Include suggestions for camera angles, lighting, or composition
        3. Focus on dynamic, high-quality visuals that would engage viewers
        4. Avoid generic terms - be precise about what should be shown
        
        Format your response ONLY as a JSON array of strings with the search terms.
        Example: ["aerial view of modern Tokyo skyline at sunset", "close-up of gaming controller with neon lighting"]
        """
        
        try:
            search_terms_result = await self._generate_content(prompt)
            
            # Try to extract JSON array
            try:
                # First look for anything that seems like a JSON array
                import re
                array_match = re.search(r'\[\s*".*"\s*\]', search_terms_result, re.DOTALL)
                if array_match:
                    search_terms_json = json.loads(array_match.group(0))
                else:
                    # Try to extract array from text that might contain explanations
                    array_match = re.search(r'(\[[\s\S]*?\])', search_terms_result)
                    if array_match:
                        try:
                            search_terms_json = json.loads(array_match.group(1))
                        except:
                            # Try the full string
                            search_terms_json = json.loads(search_terms_result)
                    else:
                        search_terms_json = json.loads(search_terms_result)
                
                if isinstance(search_terms_json, list) and len(search_terms_json) > 0:
                    return json.dumps(search_terms_json)
            except json.JSONDecodeError:
                print("Could not parse search terms as JSON, attempting to fix...")
                try:
                    # Try to extract terms manually
                    terms = []
                    # Look for quoted strings
                    quoted_strings = re.findall(r'"([^"]*)"', search_terms_result)
                    if quoted_strings:
                        terms = quoted_strings
                    else:
                        # Try to extract lines that might be search terms
                        lines = search_terms_result.split('\n')
                        for line in lines:
                            # Look for lines that start with numbers, bullets, etc.
                            if re.match(r'^[\d\.\-\*]\s+(.+)$', line.strip()):
                                term = re.sub(r'^[\d\.\-\*]\s+', '', line.strip())
                                if term and len(term) > 5:  # Avoid very short terms
                                    terms.append(term)
                    
                    if terms:
                        return json.dumps(terms)
                    print("Could not parse search terms as JSON, creating fallback")
                except:
                    print("Could not parse search terms as JSON, creating fallback")
        except Exception as e:
            print(f"Error generating search terms: {e}")
            
        # Create fallback search terms
        count = 10 if is_short else 20
        search_terms = [f"{self.title} {i}" for i in range(1, count + 1)]
        return json.dumps(search_terms)
    
    async def _create_short_outline(self):
        """Create an outline specifically for short-form videos
        
        Returns:
            str: JSON outline for short videos
        """
        prompt = f"""
        Create an engaging outline for a 30-60 second short vertical video about {self.title}.
        
        The outline should include:
        1. An attention-grabbing hook (first 3 seconds)
        2. 3-5 key points that can be covered in a very brief format
        3. A strong call-to-action
        
        Format as structured JSON with the following format:
        {{
          "hook": "Opening hook text here",
          "points": [
            {{
              "title": "Point title",
              "content": "Brief point content"
            }},
            // ... more points
          ],
          "call_to_action": "CTA text here"
        }}
        
        Remember this is for a SHORT video (30-60 seconds), so content must be concise and impactful.
        """
        
        for attempt in range(self.max_retries):
            try:
                outline_result = await self._generate_content(prompt)
                # Try to parse as JSON to validate
                try:
                    # Try to find and extract valid JSON if it's embedded in other text
                    import re
                    json_match = re.search(r'(\{[\s\S]*\})', outline_result)
                    if json_match:
                        json_str = json_match.group(1)
                        try:
                            outline_json = json.loads(json_str)
                            if "hook" in outline_json and "points" in outline_json:
                                return json.dumps(outline_json)
                        except:
                            pass
                    
                    # If that didn't work, try the original string
                    outline_json = json.loads(outline_result)
                    # Basic validation
                    if "hook" in outline_json and "points" in outline_json:
                        return outline_result
                except json.JSONDecodeError:
                    print(f"Could not parse short outline as JSON, attempt {attempt+1}")
                    # Try to fix common JSON formatting issues
                    try:
                        # Replace single quotes with double quotes
                        fixed_json = outline_result.replace("'", '"')
                        # Fix unquoted keys
                        fixed_json = re.sub(r'(\s*?)(\w+)(\s*?):', r'\1"\2"\3:', fixed_json)
                        # Try to parse the fixed JSON
                        outline_json = json.loads(fixed_json)
                        if "hook" in outline_json and "points" in outline_json:
                            return json.dumps(outline_json)
                    except:
                        pass
            except Exception as e:
                print(f"Short outline generation attempt {attempt+1} failed: {e}")
                
        # Create fallback short outline
        outline = {
            "hook": f"Did you know these facts about {self.title}?",
            "points": [
                {
                    "title": f"Amazing fact about {self.title}",
                    "content": f"Here's something incredible about {self.title} that most people don't know."
                },
                {
                    "title": "Surprising detail",
                    "content": f"This detail about {self.title} will surprise you!"
                },
                {
                    "title": "Final revelation",
                    "content": "The most important thing to remember is this key point."
                }
            ],
            "call_to_action": "Follow for more interesting facts!"
        }
        
        return json.dumps(outline, indent=2)
        
    async def _develop_short_script(self):
        """Develop a script for short-form videos
        
        Returns:
            str: Complete short video script
        """
        try:
            # Parse the short outline
            if not self.results.get("outline"):
                raise ValueError("Short outline not available")
                
            outline_json = json.loads(self.results["outline"])
            
            # Build the prompt with the outline structure
            prompt = f"""
            You are an expert creating viral short-form video scripts (30-60 seconds) about {self.title}.
            
            Use this outline to create a complete, engaging script for a vertical video:
            
            HOOK: {outline_json.get("hook", f"Did you know these facts about {self.title}?")}
            
            POINTS:
            """
            
            # Add each point from the outline
            points = outline_json.get("points", [])
            for point in points:
                prompt += f"""
                - {point.get("title", "")}: {point.get("content", "")}
                """
                
            prompt += f"""
            CALL TO ACTION: {outline_json.get("call_to_action", "Follow for more content like this!")}
            
            Write a natural, engaging script that:
            1. Uses short, punchy sentences ideal for short-form video
            2. Includes visual direction notes for each section [in brackets]
            3. Times out to approximately 30-60 seconds when read at normal pace
            4. Uses hooks, patterns interrupts, and questions to maintain viewer attention
            5. Has a clear structure: Hook → Points → Call to action
            
            Format the final script with clear section breaks and include approximate timing for each section.
            """
            
            short_script = await self._generate_content(prompt)
            
            # Verify we got substantial content
            if len(short_script) < 200:
                print("Warning: Generated short script is too short, using fallback...")
                return self._create_fallback_short_script()
                
            return short_script
            
        except Exception as e:
            print(f"Error developing short script: {e}")
            return self._create_fallback_short_script()
            
    def _create_fallback_short_script(self):
        """Create a fallback script for short videos
        
        Returns:
            str: Basic short video script
        """
        script = f"""
        [0:00-0:05] HOOK:
        Did you know these amazing facts about {self.title}? You won't believe #3!
        
        [0:05-0:15] POINT 1:
        First, {self.title} is known for its incredible features that most people overlook.
        [Close-up shot with surprised expression]
        
        [0:15-0:25] POINT 2:
        The most surprising thing? Experts say that {self.title} is one of the most 
        misunderstood topics in {self.genre}!
        [Transition to fact display with text overlay]
        
        [0:25-0:35] POINT 3:
        And finally, here's the secret that nobody talks about...
        [Dramatic pause with zoom effect]
        
        [0:35-0:45] CALL TO ACTION:
        Follow for more mind-blowing facts about {self.genre} and {self.title}!
        [End with channel name/handle and follow button animation]
        """
        
        return script
        
    def _compile_final_output(self):
        """Compile all results into a structured final output
        
        Returns:
            dict: Complete content package with all components
        """
        # Start with the basic structure
        output = {
            "title": self.title,
            "genre": self.genre,
            "language": self.language,
            "top10": []
        }
        
        # Parse outline if available
        try:
            if "outline" in self.results:
                outline = json.loads(self.results["outline"])
                
                # Extract hook, thesis and conclusion
                output["intro_text"] = outline.get("hook", "") + " " + outline.get("thesis", "")
                output["conclusion"] = outline.get("conclusion", "")
                
                # Extract items
                if "items" in outline and isinstance(outline["items"], list):
                    for item in outline["items"]:
                        output["top10"].append({
                            "name": item.get("title", f"Example of {self.title}"),
                            "rank": item.get("rank", 0),
                            "script": item.get("description", ""),
                            "search_terms": item.get("visuals", [f"{self.title} visual"])
                        })
                        
            # Sort by rank if available
            if output["top10"]:
                output["top10"] = sorted(output["top10"], key=lambda x: x.get("rank", 0), reverse=True)
        except Exception as e:
            print(f"Error parsing outline: {e}")
            # Create fallback items if needed
            if not output.get("top10"):
                output["top10"] = [
                    {"name": f"Example {i} of {self.title}", "rank": i, 
                     "script": f"This is example {i} of {self.title}.", 
                     "search_terms": [f"{self.title} {i}"]} 
                    for i in range(10, 0, -1)
                ]
        
        # Add hooks if available
        try:
            if "hooks" in self.results:
                hooks = json.loads(self.results["hooks"])
                output["hooks"] = hooks
        except Exception as e:
            print(f"Error parsing hooks: {e}")
            
        # Add search terms if available
        try:
            if "search_terms" in self.results:
                search_terms = json.loads(self.results["search_terms"])
                output["search_terms"] = search_terms
                
                # Distribute search terms to items without them
                if isinstance(search_terms, list) and output.get("top10"):
                    terms_per_item = max(1, len(search_terms) // len(output["top10"]))
                    term_index = 0
                    
                    for item in output["top10"]:
                        if not item.get("search_terms"):
                            item_terms = []
                            for _ in range(terms_per_item):
                                if term_index < len(search_terms):
                                    item_terms.append(search_terms[term_index])
                                    term_index += 1
                            item["search_terms"] = item_terms
        except Exception as e:
            print(f"Error parsing search terms: {e}")
            
        # Add detailed script if available
        if "detailed_script" in self.results:
            output["full_script"] = self.results["detailed_script"]
            
        # Add research if available
        if "research" in self.results:
            output["research"] = self.results["research"]
            
        return output
        
    def _compile_short_output(self):
        """Compile results for short video format
        
        Returns:
            dict: Content package for short videos
        """
        # Start with the basic structure
        output = {
            "title": self.title,
            "scenes": []
        }
        
        # Parse outline if available
        try:
            if "outline" in self.results:
                outline = json.loads(self.results["outline"])
                
                # Add hook as first scene
                if "hook" in outline:
                    output["scenes"].append({
                        "visual_description": "Opening hook",
                        "text": outline["hook"],
                        "search_terms": ["attention grabbing opener", f"{self.title} introduction"]
                    })
                    
                # Add points as scenes
                if "points" in outline and isinstance(outline["points"], list):
                    for i, point in enumerate(outline["points"]):
                        scene = {
                            "visual_description": point.get("title", f"Point {i+1}"),
                            "text": point.get("content", f"Point about {self.title}"),
                            "search_terms": [f"{self.title} visual {i+1}", f"{point.get('title', '')} visualization"]
                        }
                        output["scenes"].append(scene)
                        
                # Add call to action as final scene
                if "call_to_action" in outline:
                    output["scenes"].append({
                        "visual_description": "Call to action",
                        "text": outline["call_to_action"],
                        "search_terms": ["subscribe reminder", "follow call to action"]
                    })
        except Exception as e:
            print(f"Error compiling short output: {e}")
            
            # Create fallback scenes
            output["scenes"] = [
                {
                    "visual_description": "Opening hook",
                    "text": f"Did you know these facts about {self.title}?",
                    "search_terms": [f"{self.title} introduction", "attention grabbing visual"]
                },
                {
                    "visual_description": "Main content",
                    "text": f"Here's what you need to know about {self.title}.",
                    "search_terms": [f"{self.title} closeup", "detailed view"]
                },
                {
                    "visual_description": "Conclusion",
                    "text": "Follow for more amazing content!",
                    "search_terms": ["follow reminder", "conclusion shot"]
                }
            ]
        
        # Add search terms if available
        try:
            if "search_terms" in self.results:
                search_terms = json.loads(self.results["search_terms"])
                
                # Distribute search terms to scenes
                if isinstance(search_terms, list) and output["scenes"]:
                    terms_per_scene = max(1, len(search_terms) // len(output["scenes"]))
                    term_index = 0
                    
                    for scene in output["scenes"]:
                        scene_terms = []
                        for _ in range(terms_per_scene):
                            if term_index < len(search_terms):
                                scene_terms.append(search_terms[term_index])
                                term_index += 1
                        if scene_terms:
                            scene["search_terms"] = scene_terms
        except Exception as e:
            print(f"Error distributing search terms: {e}")
            
        # Add full script if available
        if "detailed_script" in self.results:
            output["full_script"] = self.results["detailed_script"]
            
        return output
    
    async def _generate_content(self, prompt):
        """Generate content using the selected AI model
        
        This function uses either Gemini or Claude based on configuration.
        
        Args:
            prompt (str): The prompt to send to the AI
            
        Returns:
            str: Generated content from the AI
        """
        try:
            # Use Claude if configured and available
            if self.use_claude:
                # Get Claude model from config or use default
                config = read_config_file()
                claude_model = config.get('claude_model', 'claude-3-haiku-20240307')
                
                # Generate content with Claude
                return await generate_script_with_claude(prompt, model=claude_model)
            else:
                # Use Gemini (default)
                return await generate_script_with_gemini(prompt)
        except Exception as e:
            print(f"Error generating content: {e}")
            
            # If one AI fails, try the other as fallback
            try:
                if self.use_claude:
                    print("Claude API failed. Falling back to Gemini...")
                    return await generate_script_with_gemini(prompt)
                elif CLAUDE_AVAILABLE:
                    print("Gemini API failed. Trying Claude as fallback...")
                    return await generate_script_with_claude(prompt)
            except Exception as fallback_error:
                print(f"Fallback also failed: {fallback_error}")
                
            # If all attempts fail, raise the original error
            raise e


async def generate_top10_content(title, genre="", language="english"):
    """Generate complete content for a top 10 video
    
    This is the main entry point for generating top 10 video content.
    
    Args:
        title (str): The main topic title
        genre (str): The general genre/category
        language (str): The target language for content
        
    Returns:
        dict: Complete content package with all components
    """
    chain = PromptChain(title, genre, language)
    return await chain.execute_chain()
    
async def generate_short_content(topic, language="english"):
    """Generate content for a short video
    
    This is the main entry point for generating short video content.
    
    Args:
        topic (str): The topic for the short video
        language (str): The target language for content
        
    Returns:
        dict: Content package for short videos
    """
    chain = PromptChain(topic, "", language)
    return await chain.execute_short_chain() 