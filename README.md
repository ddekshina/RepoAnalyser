# RepoAnalyser 

This tool analyzes GitHub repositories using Google's Gemini API to generate detailed reports about the code. The tool clones a repository, extracts code from the latest commit, and uses Gemini to analyze the codebase.

## Features

- **Clone GitHub repositories** directly from their URL
- **Analyze only the latest commit** (excluding documentation files)
- **Generate structured reports** with the following sections:
  - Introduction - What the project is about
  - Idea - The problem it solves or its goal
  - Implementation - Internal workings and code flow
  - Tech Stack - Languages, frameworks, and libraries used
  - Conclusion - Summary of core functionality and value
- **Export reports** in Markdown format
- **Web interface** for easy repository submission and report viewing
- **Command-line interface** for automation and scripting

## Prerequisites

- Python 3.8+
- Git installed and accessible in your PATH
- Google Gemini API key

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/github-repo-analyzer.git
   cd github-repo-analyzer
   ```

2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up your Gemini API key:
   ```
   export GEMINI_API_KEY=your_api_key_here
   ```
   
   For Windows:
   ```
   set GEMINI_API_KEY=your_api_key_here
   ```

### Web Interface

Start the web server:

```bash
python app.py
```

Then navigate to `http://localhost:5000` in your web browser.
|Web UI|
|------|
![GitHub Repository Analyzer - Personal - Microsoft​ Edge 15-04-2025 22_19_17](https://github.com/user-attachments/assets/671739b3-63c4-4f68-b524-534383ed5f4a)
![Analysis Status - FaceRecognition - Personal - Microsoft​ Edge 15-04-2025 22_26_00](https://github.com/user-attachments/assets/4d0ec619-b655-4746-a959-3d43ed22c901)

### Command Line Interface

```bash
python main.py https://github.com/username/repository --api-key your_api_key_here
```
|CLI UI|
|------|
![FaceRecognition_analysis md - RepoAnalyser - Visual Studio Code 15-04-2025 22_48_09](https://github.com/user-attachments/assets/98fecfe3-267a-4bde-aa1e-0c687e31441c)


## How It Works

1. **Repository Cloning**: The tool clones the specified GitHub repository with a depth of 1 to get only the latest commit.
2. **Code Extraction**: It identifies all code files in the repository, skipping documentation files and binary files.
3. **Code Analysis**: The code is processed in chunks and analyzed using Gemini API to extract insights.
4. **Report Generation**: The analyses are combined to create a comprehensive report detailing the project's purpose, implementation, and technologies.
5. **Export**: The report is saved as a Markdown file.

## Limitations

- The analysis is limited to the latest commit only
- Large repositories may take longer to analyze due to API rate limits
- The quality of the analysis depends on the Gemini model's capabilities
- Binary files and documentation are excluded from the analysis
