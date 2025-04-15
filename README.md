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
- **Export reports** in Markdown and PDF formats
- **Web interface** for easy repository submission and report viewing
- **Command-line interface** for automation and scripting

## Prerequisites

- Python 3.8+
- Git installed and accessible in your PATH
- Google Gemini API key

### For PDF Generation

- wkhtmltopdf installed on your system:
  - On Ubuntu/Debian: `sudo apt-get install wkhtmltopdf`
  - On macOS: `brew install wkhtmltopdf`
  - On Windows: Download from [wkhtmltopdf website](https://wkhtmltopdf.org/downloads.html)

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

## Usage

### Command Line Interface

Analyze a repository from the command line:

```bash
python main.py https://github.com/username/repository --output-dir ./reports
```

Generate a PDF report as well:

```bash
python main.py https://github.com/username/repository --output-dir ./reports --pdf
```

Explicitly specify your API key:

```bash
python main.py https://github.com/username/repository --api-key your_api_key_here
```

### Web Interface

Start the web server:

```bash
python app.py
```

Then navigate to `http://localhost:5000` in your web browser.

## How It Works

1. **Repository Cloning**: The tool clones the specified GitHub repository with a depth of 1 to get only the latest commit.
2. **Code Extraction**: It identifies all code files in the repository, skipping documentation files and binary files.
3. **Code Analysis**: The code is processed in chunks and analyzed using Gemini API to extract insights.
4. **Report Generation**: The analyses are combined to create a comprehensive report detailing the project's purpose, implementation, and technologies.
5. **Export**: The report is saved as a Markdown file and optionally converted to PDF.

## Limitations

- The analysis is limited to the latest commit only
- Large repositories may take longer to analyze due to API rate limits
- The quality of the analysis depends on the Gemini model's capabilities
- Binary files and documentation are excluded from the analysis

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Acknowledgments

- Google Generative AI for the Gemini API
- All the open source libraries that made this project possible