import os
import sys
import argparse
import tempfile
import subprocess
import glob
import markdown
import pdfkit
from pathlib import Path
import google.generativeai as genai
from typing import List, Dict, Any, Tuple
import logging
from dotenv import load_dotenv 
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GitHubRepoAnalyzer:
    def __init__(self, api_key: str):
        """
        Initialize the analyzer with a Google Gemini API key.
        
        Args:
            api_key: Google Gemini API key
        """
        self.api_key = api_key
        genai.configure(api_key=api_key)
        
        # Try using Gemini 2.0 Flash-Lite
        try:
            self.model = genai.GenerativeModel('gemini-2.0-flash-lite')
            logger.info("Successfully initialized gemini-2.0-flash-lite model")
        except Exception as e:
            logger.warning(f"Failed to initialize gemini-2.0-flash-lite: {e}")
            try:
                # Fall back to gemini-1.5-pro
                self.model = genai.GenerativeModel('gemini-1.5-pro')
                logger.info("Falling back to gemini-1.5-pro model")
            except Exception as e2:
                logger.warning(f"Failed to initialize gemini-1.5-pro: {e2}")
                try:
                    # Try another fallback
                    self.model = genai.GenerativeModel('gemini-pro')
                    logger.info("Falling back to gemini-pro model")
                except Exception as e3:
                    logger.warning(f"Failed to initialize gemini-pro: {e3}")
                    # As last resort, list available models and use the first generative one
                    models = genai.list_models()
                    generative_models = [m for m in models if "generateContent" in m.supported_generation_methods]
                    if generative_models:
                        logger.info(f"Using available model: {generative_models[0].name}")
                        self.model = genai.GenerativeModel(generative_models[0].name)
                    else:
                        raise ValueError("No suitable Gemini models found. Please check your API key and available models.")
            
        # Common binary/non-text file extensions to ignore
        self.ignored_extensions = {
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.ico', '.tif', '.tiff',
            '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx',
            '.zip', '.tar', '.gz', '.rar', '.7z',
            '.exe', '.dll', '.so', '.dylib', '.class', '.pyc',
            '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac',
            '.db', '.sqlite', '.sqlite3',
            '.ttf', '.otf', '.woff', '.woff2',
            '.bin', '.dat', '.pickle', '.pkl'
        }
        
        # Extensions typically used for documentation
        self.doc_extensions = {
            '.md', '.rst', '.txt', '.pdf', '.doc', '.docx', '.html'
        }
        
        # File names typically used for documentation
        self.doc_filenames = {
            'readme', 'license', 'contributing', 'changelog', 'documentation',
            'docs', 'manual', 'guide', 'tutorial', 'faq', 'help'
        }

    def clone_repository(self, repo_url: str, target_dir: str) -> bool:
        """
        Clone a GitHub repository to a target directory.
        
        Args:
            repo_url: URL of the GitHub repository
            target_dir: Local directory to clone into
            
        Returns:
            bool: True if cloning was successful, False otherwise
        """
        try:
            logger.info(f"Cloning repository: {repo_url}")
            subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, target_dir],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone repository: {e}")
            return False

    def is_documentation_file(self, filepath: str) -> bool:
        """
        Check if a file is likely documentation.
        
        Args:
            filepath: Path to the file
            
        Returns:
            bool: True if the file appears to be documentation
        """
        filename = os.path.basename(filepath).lower()
        extension = os.path.splitext(filename)[1].lower()
        basename_without_ext = os.path.splitext(filename)[0].lower()
        
        # Check if the file extension is typically used for documentation
        if extension in self.doc_extensions:
            # Check if the filename indicates it's documentation
            for doc_name in self.doc_filenames:
                if doc_name in basename_without_ext:
                    return True
        
        return False

    def collect_code_files(self, repo_dir: str) -> Dict[str, List[str]]:
        """
        Collect all code files from the repository, grouped by language.
        
        Args:
            repo_dir: Path to the repository directory
            
        Returns:
            Dict mapping language extensions to lists of file paths
        """
        code_files = {}
        
        # Walk through the repository directory
        for root, _, files in os.walk(repo_dir):
            # Skip .git directory
            if '.git' in root.split(os.path.sep):
                continue
            
            for file in files:
                filepath = os.path.join(root, file)
                
                # Skip binary and non-text files
                extension = os.path.splitext(file)[1].lower()
                if extension in self.ignored_extensions:
                    continue
                
                # Skip documentation files
                if self.is_documentation_file(filepath):
                    logger.info(f"Skipping documentation file: {filepath}")
                    continue
                
                # Group files by extension (language)
                if extension not in code_files:
                    code_files[extension] = []
                code_files[extension].append(filepath)
        
        return code_files

    def read_file_content(self, filepath: str, max_size: int = 1024 * 1024) -> str:
        """
        Read the content of a file safely, handling encoding issues.
        
        Args:
            filepath: Path to the file
            max_size: Maximum file size to read (in bytes)
            
        Returns:
            str: File content or empty string if there was an error
        """
        try:
            # Check file size first
            file_size = os.path.getsize(filepath)
            if file_size > max_size:
                logger.warning(f"File too large ({file_size/1024/1024:.2f} MB), skipping: {filepath}")
                return f"[File too large: {filepath}]"
            
            # Try to read with utf-8 encoding first
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # If utf-8 fails, try with latin-1 encoding
            try:
                with open(filepath, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to read file {filepath}: {e}")
                return f"[Error reading file: {filepath}]"
        except Exception as e:
            logger.error(f"Failed to read file {filepath}: {e}")
            return f"[Error reading file: {filepath}]"

    def split_large_text(self, text: str, chunk_size: int = 10000) -> List[str]:
        """
        Split text into smaller chunks to fit within API limits.
        
        Args:
            text: The text to split
            chunk_size: Maximum character count per chunk
            
        Returns:
            List[str]: List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunks.append(text[i:i + chunk_size])
            
        return chunks

    def analyze_code_chunk(self, code_chunk: str, context: str) -> str:
        """
        Analyze a chunk of code using Gemini API.
        
        Args:
            code_chunk: The code to analyze
            context: Additional context to help with analysis
            
        Returns:
            str: Analysis result
        """
        prompt = f"""
        You are a code analyst. Please analyze the following code from a GitHub repository. 
        This is part of {context}.
        
        CODE:
        ```
        {code_chunk}
        ```
        
        Analyze this code and extract insights that would help understand:
        1. What functionality does this implement?
        2. What patterns or architecture does it use?
        3. What libraries/dependencies/frameworks does it utilize?
        4. How does this fit into the overall project structure?
        
        Provide your analysis in a concise format focusing on the key insights.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Failed to analyze code chunk: {e}")
            return f"[Error analyzing code: {str(e)}]"

    def generate_project_summary(self, analyses: List[str], project_name: str, output_type: str = "analysis") -> str:
        """
        Generate a project summary based on code analyses with different output formats.
        
        Args:
            analyses: List of code analyses
            project_name: Name of the GitHub repository
            output_type: Type of output to generate (analysis, readme, guidance)
            
        Returns:
            str: Markdown report
        """
        combined_analyses = "\n\n".join(analyses)
        
        if output_type == "analysis":
            prompt = f"""
            You are a technical documentation expert. Based on the following code analyses from the GitHub repository "{project_name}", 
            generate a comprehensive markdown report with these sections:
            
            1. **Introduction** – What is the project about?
            2. **Idea** – What problem is it solving or what goal is it trying to achieve?
            3. **Features** – What are the key functionalities and capabilities offered by the project?
            4. **Implementation** – How does it work internally? Highlight logic and workflow.
            5. **Tech Stack Used** – Languages, frameworks, libraries used in the code.
            6. **Conclusion** – Wrap-up summarizing the project's core functionality and value.
            
            CODE ANALYSES:
            {combined_analyses}
            
            Format your response as a valid Markdown document. Be specific and technical, focusing only on what can be determined from the code itself. Do not make assumptions beyond what's evident from the code. Use appropriate Markdown formatting including headers, code blocks, bullet points, etc.
            """
        elif output_type == "readme":
            prompt = f"""
            You are a README.md generator and a technical documentation expert. Based on the following code analysis from the GitHub repository "{project_name}", create a professional and informative README file in Markdown format. The README should include the following sections:

            1. **# {project_name}** – Use this as the title.
            2. **## Introduction** – Briefly describe what the project is and its overall purpose.
            3. **## Problem Statement / Idea** – Explain the problem it solves or the goal it aims to achieve.
            4. **## Features** – List key features and functionalities implemented in the code.
            5. **## How It Works (Implementation Overview)** – Describe the internal logic, core components, and workflow.
            6. **## Tech Stack** – List programming languages, libraries, frameworks, and tools used.
            7. **## Getting Started (optional)** – If setup steps are found in the code (like setup.py, package.json, or Dockerfile), summarize them here.
            8. **## Conclusion** – Wrap up with a summary of the project's capabilities and use cases.

            CODE ANALYSIS:
            {combined_analyses}

            Guidelines:
            - Only include information that is evident from the code analysis. Do not speculate.
            - Use proper Markdown formatting (headings, bullet points, code blocks, etc.).
            - Maintain clarity, conciseness, and technical accuracy.
            """
        elif output_type == "guidance":
                prompt = f"""
                You are a senior software engineer and technical project architect. Based on the following code analysis from the GitHub repository "{project_name}", generate a **precise and prioritized Markdown guide** that outlines **only what is missing, incomplete, flawed, or needs improvement** in the current project.

                Your output should **strictly reflect the gaps and issues in the existing code** and serve as a clear technical to-do list to complete and enhance the project into a robust, full-stack application.

                ### Your guide must:
                1. Focus **only** on what is missing, partially implemented, buggy, or poorly structured — **do not add general guidance or best practices** unless the code clearly lacks it.
                2. Include:
                - Components or features that are not present but are implied to be needed
                - Incomplete logic, commented-out or placeholder sections
                - Bugs, unhandled cases, and performance concerns
                - Code quality or structural issues that require refactoring
                3. Highlight full-stack gaps:
                - If the frontend is missing, clearly list what should be added based on backend endpoints or expected user interactions.
                - If the backend is missing or incomplete, infer needed APIs or data handling from the frontend or related files.
                - Point out if there’s no database model despite persistent data needs, no authentication for protected routes, or missing deployment configuration.
                4. Group guide items under **technical categories** such as:
                - `Frontend`
                - `Backend`
                - `API`
                - `Database`
                - `Authentication & Authorization`
                - `Testing`
                - `Deployment`
                - `Code Quality & Refactoring`
                5. Use Markdown guide under the header:

                ## ✅ Next Steps to Complete and Improve the Project

                CODE ANALYSIS:
                {combined_analyses}

                ### Output Instructions:
                - Be brief but technically clear.
                - Do **not** describe what is already complete unless it needs fixing or revision.
                - Do **not** add assumptions not backed by the code.
                - Prioritize core issues before enhancements.
                """

        else:
            # Default to analysis if an unknown type is provided
            logger.warning(f"Unknown output type '{output_type}', defaulting to 'analysis'")
            return self.generate_project_summary(analyses, project_name, "analysis")

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Failed to generate project summary: {e}")
            return f"# Error Generating Project Summary\n\nAn error occurred: {str(e)}"

    def analyze_repository(self, repo_url: str, output_type: str = "analysis", output_dir: str = None) -> Tuple[str, str]:
        """
        Analyze a GitHub repository and generate a report.
        
        Args:
            repo_url: URL of the GitHub repository
            output_type: Type of output to generate (analysis, readme, guidance)
            output_dir: Directory to save the report
            
        Returns:
            Tuple[str, str]: (report_path, report_content)
        """
        # Create temporary directory for cloning
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract repository name from URL for reporting
            repo_name = repo_url.rstrip('/').split('/')[-1]
            if repo_name.endswith('.git'):
                repo_name = repo_name[:-4]
                
            logger.info(f"Starting analysis of repository: {repo_name}")
            
            # Clone the repository
            if not self.clone_repository(repo_url, temp_dir):
                return None, f"# Analysis Failed\n\nFailed to clone repository: {repo_url}"
            
            # Collect code files
            code_files = self.collect_code_files(temp_dir)
            if not code_files:
                return None, f"# Analysis Failed\n\nNo code files found in repository: {repo_url}"
            
            # Analyze code files
            analyses = []
            for extension, files in code_files.items():
                language = extension.lstrip('.') if extension else 'unknown'
                logger.info(f"Analyzing {len(files)} {language} files")
                
                # Limit the number of files per language to analyze
                max_files_per_lang = 10
                if len(files) > max_files_per_lang:
                    logger.info(f"Limiting analysis to {max_files_per_lang} {language} files")
                    files = files[:max_files_per_lang]
                
                for filepath in files:
                    rel_path = os.path.relpath(filepath, temp_dir)
                    logger.info(f"Analyzing file: {rel_path}")
                    
                    # Read file content
                    content = self.read_file_content(filepath)
                    if not content or content.startswith('[Error'):
                        continue
                    
                    # Split large files into chunks
                    chunks = self.split_large_text(content)
                    file_analysis = []
                    
                    for i, chunk in enumerate(chunks):
                        context = f"file {rel_path} (part {i+1}/{len(chunks)})"
                        analysis = self.analyze_code_chunk(chunk, context)
                        file_analysis.append(analysis)
                    
                    # Combine file analyses
                    combined_file_analysis = f"## Analysis of {rel_path}\n\n" + "\n\n".join(file_analysis)
                    analyses.append(combined_file_analysis)
            
            # Generate report based on specified output type
            report_content = self.generate_project_summary(analyses, repo_name, output_type)
            
            # Create appropriate filename based on output type
            filename_suffix = {
                "analysis": "analysis",
                "readme": "README",
                "guidance": "guidance"
            }.get(output_type, "analysis")
            
            # Save the report
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                report_path = os.path.join(output_dir, f"{repo_name}_{filename_suffix}.md")
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                logger.info(f"{output_type.capitalize()} report saved to: {report_path}")
            else:
                report_path = None
                
            return report_path, report_content
    
    def export_to_pdf(self, markdown_path: str) -> str:
        """
        Convert markdown report to PDF.
        
        Args:
            markdown_path: Path to the markdown file
            
        Returns:
            str: Path to the generated PDF file
        """
        try:
            pdf_path = os.path.splitext(markdown_path)[0] + '.pdf'
            
            # Read markdown content
            with open(markdown_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # Convert markdown to HTML
            html_content = markdown.markdown(markdown_content, extensions=['extra', 'codehilite'])
            
            # Add some basic styling
            styled_html = f"""
            <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Repository Analysis</title>
                    <style>
                        /* Base styles */
                        body {{
                            font-family: 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                            line-height: 1.6;
                            max-width: 900px;
                            margin: 0 auto;
                            padding: 30px;
                            color: #333;
                            background-color: #fff;
                        }}

                        /* Headers */
                        h1 {{
                            font-size: 28px;
                            color: #2c3e50;
                            border-bottom: 2px solid #3498db;
                            padding-bottom: 10px;
                            margin-top: 20px;
                            font-weight: 600;
                        }}

                        h2 {{
                            font-size: 24px;
                            color: #2980b9;
                            margin-top: 24px;
                            border-left: 4px solid #3498db;
                            padding-left: 10px;
                            font-weight: 500;
                        }}

                        h3 {{
                            font-size: 20px;
                            color: #16a085;
                            margin-top: 20px;
                            font-weight: 500;
                        }}

                        /* Paragraphs and text */
                        p {{
                            margin-bottom: 16px;
                            text-align: justify;
                        }}

                        strong {{
                            color: #2c3e50;
                            font-weight: 600;
                        }}

                        em {{
                            color: #7f8c8d;
                        }}

                        /* Code blocks */
                        code {{
                            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                            background-color: #f7f9fb;
                            color: #e74c3c;
                            padding: 2px 5px;
                            border-radius: 3px;
                            font-size: 90%;
                            border: 1px solid #eaecef;
                        }}

                        pre {{
                            background-color: #f8f8f8;
                            padding: 15px;
                            border-radius: 5px;
                            overflow-x: auto;
                            border: 1px solid #e1e4e8;
                            margin: 16px 0;
                        }}

                        pre code {{
                            background-color: transparent;
                            padding: 0;
                            border: none;
                            color: #333;
                            font-size: 14px;
                            line-height: 1.5;
                        }}

                        /* Lists */
                        ul, ol {{
                            padding-left: 20px;
                            margin-bottom: 16px;
                        }}

                        li {{
                            margin-bottom: 8px;
                        }}

                        /* Tables */
                        table {{
                            border-collapse: collapse;
                            width: 100%;
                            margin: 20px 0;
                            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                        }}

                        th, td {{
                            text-align: left;
                            padding: 12px;
                            border: 1px solid #e1e4e8;
                        }}

                        th {{
                            background-color: #f1f8ff;
                            color: #0366d6;
                            font-weight: 600;
                        }}

                        tr:nth-child(even) {{
                            background-color: #f6f8fa;
                        }}

                        tr:hover {{
                            background-color: #f0f4f8;
                        }}

                        /* Blockquotes */
                        blockquote {{
                            border-left: 4px solid #3498db;
                            padding: 10px 15px;
                            margin: 16px 0;
                            background-color: #f8f9fa;
                            color: #4a5568;
                            font-style: italic;
                        }}

                        /* Links */
                        a {{
                            color: #3498db;
                            text-decoration: none;
                        }}

                        a:hover {{
                            text-decoration: underline;
                            color: #2980b9;
                        }}

                        /* Page header */
                        .repo-header {{
                            background-color: #f1f8ff;
                            padding: 20px;
                            margin-bottom: 30px;
                            border-radius: 8px;
                            border-left: 5px solid #0366d6;
                        }}

                        .repo-header h1 {{
                            margin-top: 0;
                            border-bottom: none;
                        }}

                        /* Feature boxes */
                        .feature-section {{
                            margin: 25px 0;
                            padding: 20px;
                            background-color: #f8f9fa;
                            border-radius: 8px;
                            border: 1px solid #e1e4e8;
                        }}

                        /* Footer */
                        .footer {{
                            margin-top: 40px;
                            padding-top: 20px;
                            border-top: 1px solid #eaecef;
                            color: #6c757d;
                            font-size: 14px;
                            text-align: center;
                        }}
                    </style>
                </head>
                <body>
                    <div class="repo-header">
                        <h1>Repository Analysis Report</h1>
                        <p>Comprehensive analysis powered by Google's Gemini AI</p>
                    </div>

                    {html_content}

                    <div class="footer">
                        <p>Generated on {datetime.now().strftime("%Y-%m-%d at %H:%M:%S")} | GitHub Repository Analyzer</p>
                    </div>
                </body>
            </html>
            """
            
            # Specify path to wkhtmltopdf executable
            config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
            
            # Convert HTML to PDF with configuration
            pdfkit.from_string(styled_html, pdf_path, configuration=config)
            logger.info(f"PDF report saved to: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"Failed to export to PDF: {e}", exc_info=True)  # Added exc_info for more detailed error
            return None

def main():
    
    load_dotenv()

    parser = argparse.ArgumentParser(description='Analyze a GitHub repository using Gemini API')
    parser.add_argument('repo_url', help='URL of the GitHub repository to analyze')
    parser.add_argument('--output-type', '-t', choices=['analysis', 'readme', 'guidance'], 
                        default='analysis', help='Type of output to generate (analysis, readme, guidance)')
    parser.add_argument('--output-dir', '-o', help='Directory to save the analysis report')
    parser.add_argument('--api-key', '-k', help='Google Gemini API key')
    parser.add_argument('--pdf', action='store_true', help='Export report to PDF')
    args = parser.parse_args()
    
    # Get API key from arguments or environment variable
    api_key = args.api_key or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("Error: Gemini API key is required. Provide it with --api-key or set GEMINI_API_KEY environment variable.")
        sys.exit(1)
    
    # Set default output directory if not provided
    output_dir = args.output_dir or os.path.join(os.getcwd(), 'reports')
    
    # Create analyzer and process repository
    analyzer = GitHubRepoAnalyzer(api_key)
    
    # Get the output type from args
    output_type = args.output_type
    
    print(f"Processing repository to generate {output_type} report...")
    report_path, report_content = analyzer.analyze_repository(args.repo_url, output_type, output_dir)
    
    if not report_path:
        print(report_content)  # Print error message
        sys.exit(1)
        
    # Export to PDF if requested
    if args.pdf:
        pdf_path = analyzer.export_to_pdf(report_path)
        if pdf_path:
            print(f"PDF report saved to: {pdf_path}")
    
    report_type_name = {
        "analysis": "Analysis report",
        "readme": "README file",
        "guidance": "Development guidance"
    }.get(output_type, "Report")
    
    print(f"{report_type_name} complete. Saved to: {report_path}")
    
if __name__ == "__main__":
    main()