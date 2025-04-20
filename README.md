# RepoAnalyser 

A web application leveraging Google's generative AI to automatically analyze GitHub repositories and generate insightful reports in various formats, including project summaries and development guidance.

## Features

*   **GitHub Repository Analysis:** Analyzes code within a specified GitHub repository.
*   **Report Generation:**  Generates reports in various formats, including
      - 🔎 Code Analysis  
      - 📝 README Generator  
      - 🛠️ Development Guidance
*   **Web Interface:**  Provides a web interface for submitting repository URLs, displaying analysis status, and downloading reports.
*   **Asynchronous Processing:** Uses background tasks (threading) to handle repository analysis without blocking the main application.
*   **Report Formats:** Generates Markdown reports.
*   **PDF Generation (Optional):** Converts Markdown reports to PDF format.
*   **Job Tracking:**  Tracks the status and results of analysis jobs.
*   **Error Handling and Logging:** Includes error handling and logging for monitoring the analysis process.
*   **Automated Report Download:** Allows users to download generated reports in Markdown (.md) and PDF formats.

|Web UI|
|------|
![GitHub Repository Analyzer - Google Chrome 20-04-2025 16_45_06](https://github.com/user-attachments/assets/547a127f-ba7d-466e-a468-e182abed657f)
![GitHub Repository Analyzer - Google Chrome 20-04-2025 16_45_34](https://github.com/user-attachments/assets/5c292706-c139-492d-ad35-e82679de7780)


### Command Line Interface

```bash
python main.py https://github.com/username/repo-name --output-type analysis
```
|CLI UI|
|------|
![FaceRecognition_analysis md - RepoAnalyser - Visual Studio Code 15-04-2025 22_48_09](https://github.com/user-attachments/assets/98fecfe3-267a-4bde-aa1e-0c687e31441c)


## Prerequisites

- Python 3.8+
- Git installed and accessible in your PATH
- Google Gemini API key

## How It Works (Implementation Overview)

The application's workflow involves the following core steps:

1.  **User Input:** The web interface (templates\index.html) allows users to submit a GitHub repository URL, an output type (analysis, README, or guidance), and an API key.
2.  **Analysis Initiation:**  A backend process (likely in app.py or main.py) receives the user's input and initiates the analysis process.
3.  **Repository Cloning:** The application clones the specified GitHub repository locally (using `git clone`).
4.  **Code File Collection:** The application identifies and collects code files within the repository.
5.  **Code Analysis:** The `GitHubRepoAnalyzer` class (from main.py) analyzes the code, potentially using the Google Gemini API.
6.  **Report Generation:** Based on the selected output type, a report is generated.
7.  **Markdown Conversion and PDF Generation:** The report is generated as Markdown, with an option for converting the Markdown to PDF (using `pdfkit`).
8.  **Report Storage:** Generated reports are saved.
9.  **Status Display:** The web interface (templates\status.html) displays the status of the analysis job, including progress, errors, and links to download the reports.
10. **Report Downloading:** Users can download generated reports.

The `GitHubRepoAnalyzer` class, likely defined in `main.py`, is responsible for the core analysis functionality.  It uses methods to clone the repository, identify code files, read file content, split large text into chunks (to handle API limits), and analyze code using prompts for an LLM (e.g., Google Gemini).

## Tech Stack

*   **Programming Language:** Python
*   **Web Framework:** Flask
*   **AI Model Interaction:** Google Gemini API via `google-generativeai` library.
*   **Templating Engine:** Jinja (implied)
*   **Markdown Processing:** `markdown` library.
*   **PDF Generation:** `pdfkit` library (requires wkhtmltopdf).
*   **Asynchronous Task Execution:**  `threading` module.
*   **Command-line Argument Parsing:** `argparse` library.
*   **Version Control (Git):** `gitpython` library.
*   **CSS Framework:** Bootstrap (5.3.0-alpha1)

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

## Limitations

- The analysis is limited to the latest commit only
- Large repositories may take longer to analyze due to API rate limits
- The quality of the analysis depends on the Gemini model's capabilities
- Binary files and documentation are excluded from the analysis
